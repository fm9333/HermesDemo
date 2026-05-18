from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from hermes_app.core.database import Database
from hermes_app.services.providers import ProviderRegistry


class MapService:
    provider_id = "map.nominatim"

    def __init__(self, db: Database, providers: ProviderRegistry):
        self.db = db
        self.providers = providers

    def search(self, query: str, limit: int = 5) -> dict:
        cleaned_query = query.strip()
        if not cleaned_query:
            raise ValueError("Map query is required.")

        normalized_limit = max(1, min(int(limit or 5), 10))
        cached = self._cached(cleaned_query, normalized_limit)
        if cached:
            return {"status": "cached", "places": cached, "count": len(cached)}

        provider = self.providers.get(self.provider_id)
        if not provider or provider["status"] != "connected":
            return {"status": "disabled", "places": [], "count": 0}

        max_limit = int(provider["config"].get("max_limit", 5) or 5)
        request_limit = max(1, min(normalized_limit, max_limit, 10))
        raw_places = json.loads(self._fetch(cleaned_query, request_limit, provider))
        saved = [self._save(cleaned_query, raw) for raw in raw_places[:request_limit]]
        return {"status": "ok", "places": saved, "count": len(saved)}

    def list(self, limit: int = 50) -> list[dict]:
        rows = self.db.query(
            "SELECT * FROM map_places ORDER BY created_at DESC LIMIT ?",
            (limit,),
        )
        return [self._deserialize(row) for row in rows]

    def get(self, place_id: str) -> dict | None:
        row = self.db.query_one("SELECT * FROM map_places WHERE id = ?", (place_id,))
        return self._deserialize(row) if row else None

    def _fetch(self, query: str, limit: int, provider: dict) -> bytes:
        params = urlencode(
            {
                "q": query,
                "format": "jsonv2",
                "addressdetails": 1,
                "limit": limit,
                "dedupe": 1,
            }
        )
        endpoint = provider["config"].get("endpoint", "https://nominatim.openstreetmap.org/search")
        request = Request(
            f"{endpoint}?{params}",
            headers={"User-Agent": "HermesDesktop/0.1 local map search"},
        )
        with urlopen(request, timeout=8) as response:
            return response.read()

    def _cached(self, query: str, limit: int) -> list[dict]:
        rows = self.db.query(
            "SELECT * FROM map_places WHERE query = ? ORDER BY importance DESC, created_at DESC LIMIT ?",
            (query, limit),
        )
        return [self._deserialize(row) for row in rows]

    def _save(self, query: str, raw: dict) -> dict:
        place_id = _place_id(query, raw)
        address = raw.get("address") if isinstance(raw.get("address"), dict) else {}
        bounding_box = raw.get("boundingbox") if isinstance(raw.get("boundingbox"), list) else []
        params = (
            self.provider_id,
            query,
            raw.get("display_name") or raw.get("name") or query,
            float(raw.get("lat") or 0),
            float(raw.get("lon") or 0),
            raw.get("category") or raw.get("class") or "",
            raw.get("type") or "",
            float(raw.get("importance") or 0),
            json.dumps(address, ensure_ascii=False),
            json.dumps(bounding_box, ensure_ascii=False),
            json.dumps(raw, ensure_ascii=False),
            _now(),
            place_id,
        )
        if self.get(place_id):
            self.db.execute(
                """
                UPDATE map_places
                SET provider_id = ?, query = ?, display_name = ?, lat = ?, lon = ?,
                    category = ?, place_type = ?, importance = ?, address_json = ?,
                    bounding_box_json = ?, raw_json = ?, created_at = ?
                WHERE id = ?
                """,
                params,
            )
        else:
            self.db.execute(
                """
                INSERT INTO map_places
                    (provider_id, query, display_name, lat, lon, category, place_type, importance,
                     address_json, bounding_box_json, raw_json, created_at, id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                params,
            )
        return self.get(place_id) or {}

    def _deserialize(self, row: dict) -> dict:
        row["address"] = json.loads(row.pop("address_json"))
        row["bounding_box"] = json.loads(row.pop("bounding_box_json"))
        row["raw"] = json.loads(row.pop("raw_json"))
        return row


def _place_id(query: str, raw: dict) -> str:
    osm_key = f"{raw.get('osm_type', '')}:{raw.get('osm_id', '')}:{raw.get('place_id', '')}"
    key = f"{query}:{osm_key}:{raw.get('display_name', '')}"
    return hashlib.sha256(key.encode("utf-8")).hexdigest()[:24]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()
