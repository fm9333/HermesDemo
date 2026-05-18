from __future__ import annotations

import hashlib
import html
import json
import re
from datetime import datetime, timezone
from urllib.request import Request, urlopen
from xml.etree import ElementTree

from hermes_app.core.database import Database
from hermes_app.services.providers import ProviderRegistry


class NewsService:
    provider_id = "news.rss"

    def __init__(self, db: Database, providers: ProviderRegistry):
        self.db = db
        self.providers = providers

    def refresh(self, limit: int = 20) -> dict:
        provider = self.providers.get(self.provider_id)
        if not provider or provider["status"] != "connected":
            return {"status": "disabled", "articles": [], "count": 0}

        articles = []
        for feed in provider["config"].get("feeds", []):
            source = feed.get("source") or "RSS"
            url = feed.get("url")
            if not url:
                continue
            articles.extend(self._parse_feed(self._fetch(url), source))

        saved = [self._save(article) for article in articles[:limit]]
        return {"status": "ok", "articles": saved, "count": len(saved)}

    def list(self, limit: int = 50) -> list[dict]:
        rows = self.db.query(
            "SELECT * FROM news_articles WHERE status = ? ORDER BY published_at DESC, fetched_at DESC LIMIT ?",
            ("active", limit),
        )
        return [self._deserialize(row) for row in rows]

    def get(self, article_id: str) -> dict | None:
        row = self.db.query_one("SELECT * FROM news_articles WHERE id = ?", (article_id,))
        return self._deserialize(row) if row else None

    def _fetch(self, url: str) -> bytes:
        request = Request(url, headers={"User-Agent": "HermesDesktop/0.1 RSS Reader"})
        with urlopen(request, timeout=8) as response:
            return response.read()

    def _parse_feed(self, content: bytes, source: str) -> list[dict]:
        root = ElementTree.fromstring(content)
        if _local_name(root.tag) == "rss":
            channel = next((child for child in root if _local_name(child.tag) == "channel"), root)
            return [self._parse_rss_item(item, source) for item in channel if _local_name(item.tag) == "item"]
        if _local_name(root.tag) == "feed":
            return [self._parse_atom_entry(entry, source) for entry in root if _local_name(entry.tag) == "entry"]
        return []

    def _parse_rss_item(self, item: ElementTree.Element, source: str) -> dict:
        title = _text(item, "title")
        url = _text(item, "link")
        summary = _clean_summary(_text(item, "description"))
        published_at = _text(item, "pubDate") or _now()
        tags = [_clean_summary(child.text or "") for child in item if _local_name(child.tag) == "category"]
        return {
            "provider_id": self.provider_id,
            "source": source,
            "title": title or url or "Untitled",
            "url": url,
            "summary": summary,
            "published_at": published_at,
            "tags": [tag for tag in tags if tag],
        }

    def _parse_atom_entry(self, entry: ElementTree.Element, source: str) -> dict:
        title = _text(entry, "title")
        url = ""
        for child in entry:
            if _local_name(child.tag) == "link":
                url = child.attrib.get("href", "")
                break
        summary = _clean_summary(_text(entry, "summary") or _text(entry, "content"))
        published_at = _text(entry, "published") or _text(entry, "updated") or _now()
        tags = [child.attrib.get("term", "") for child in entry if _local_name(child.tag) == "category"]
        return {
            "provider_id": self.provider_id,
            "source": source,
            "title": title or url or "Untitled",
            "url": url,
            "summary": summary,
            "published_at": published_at,
            "tags": [tag for tag in tags if tag],
        }

    def _save(self, article: dict) -> dict:
        article_id = _article_id(article)
        existing = self.get(article_id)
        params = (
            self.provider_id,
            article["source"],
            article["title"],
            article["url"],
            article["summary"],
            article["published_at"],
            json.dumps(article["tags"], ensure_ascii=False),
            "active",
            _now(),
            article_id,
        )
        if existing:
            self.db.execute(
                """
                UPDATE news_articles
                SET provider_id = ?, source = ?, title = ?, url = ?, summary = ?, published_at = ?,
                    tags_json = ?, status = ?, fetched_at = ?
                WHERE id = ?
                """,
                params,
            )
        else:
            self.db.execute(
                """
                INSERT INTO news_articles
                    (provider_id, source, title, url, summary, published_at, tags_json, status, fetched_at, id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                params,
            )
        return self.get(article_id) or {}

    def _deserialize(self, row: dict) -> dict:
        row["tags"] = json.loads(row.pop("tags_json"))
        return row


def _text(element: ElementTree.Element, name: str) -> str:
    for child in element:
        if _local_name(child.tag) == name:
            return (child.text or "").strip()
    return ""


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _clean_summary(value: str) -> str:
    text = html.unescape(value)
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _article_id(article: dict) -> str:
    key = article.get("url") or f"{article.get('source')}:{article.get('title')}"
    return hashlib.sha256(key.encode("utf-8")).hexdigest()[:24]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()
