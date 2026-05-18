from hermes_app.core.database import Database
from hermes_app.services.news import NewsService
from hermes_app.services.providers import ProviderRegistry


RSS_SAMPLE = b"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Example RSS</title>
    <item>
      <title>RSS headline</title>
      <link>https://example.com/rss-headline</link>
      <description><![CDATA[<p>RSS summary</p>]]></description>
      <pubDate>Mon, 18 May 2026 10:00:00 GMT</pubDate>
      <category>Technology</category>
    </item>
  </channel>
</rss>
"""

ATOM_SAMPLE = b"""<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <title>Example Atom</title>
  <entry>
    <title>Atom headline</title>
    <link href="https://example.com/atom-headline" />
    <summary>Atom summary</summary>
    <updated>2026-05-18T11:00:00Z</updated>
    <category term="AI" />
  </entry>
</feed>
"""


def test_news_service_refreshes_rss_and_atom_feeds(tmp_path, monkeypatch):
    db = Database(tmp_path / "news.db")
    db.init()
    providers = ProviderRegistry(db)
    service = NewsService(db, providers)

    def fake_fetch(url: str) -> bytes:
        return RSS_SAMPLE if "bbc" in url else ATOM_SAMPLE

    monkeypatch.setattr(service, "_fetch", fake_fetch)

    refreshed = service.refresh()
    listed = service.list()

    assert refreshed["status"] == "ok"
    assert refreshed["count"] == 2
    assert {item["title"] for item in listed} == {"RSS headline", "Atom headline"}
    assert next(item for item in listed if item["title"] == "RSS headline")["summary"] == "RSS summary"
    assert next(item for item in listed if item["title"] == "Atom headline")["tags"] == ["AI"]

    refreshed_again = service.refresh()
    assert refreshed_again["count"] == 2
    assert len(service.list()) == 2


def test_news_service_respects_provider_status(tmp_path, monkeypatch):
    db = Database(tmp_path / "news_disabled.db")
    db.init()
    providers = ProviderRegistry(db)
    providers.disconnect("news.rss")
    service = NewsService(db, providers)
    monkeypatch.setattr(service, "_fetch", lambda url: RSS_SAMPLE)

    refreshed = service.refresh()

    assert refreshed == {"status": "disabled", "articles": [], "count": 0}
    assert service.list() == []
