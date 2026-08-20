from datetime import UTC, datetime
from typing import Any

from ..schemas import NormalizedMessage
from .base import Adapter, AdapterResult


class EONETAdapter(Adapter):
    """NASA EONET v3 open-event adapter."""

    def fetch(self, cursor: str | None = None) -> AdapterResult:
        params: dict[str, str | int] = {
            "category": str(self.source.options.get("categories", "severeStorms,floods")),
            "status": str(self.source.options.get("status", "open")),
            "limit": max(1, min(int(str(self.source.options.get("limit", 50))), 200)),
            "days": max(1, min(int(str(self.source.options.get("days", 14))), 90)),
        }
        response = self.client.get(self.source.target, params=params)
        response.raise_for_status()
        payload: dict[str, Any] = response.json()
        messages = []
        for event in payload.get("events", []):
            geometry = event.get("geometry") or []
            latest = geometry[-1] if geometry else {}
            try:
                published_at = datetime.fromisoformat(str(latest.get("date", "")).replace("Z", "+00:00"))
            except ValueError:
                published_at = datetime.now(UTC)
            sources = event.get("sources") or []
            permalink = sources[0].get("url") if sources else event.get("link")
            text = "\n".join(filter(None, [event.get("title", ""), event.get("description", "")]))
            messages.append(
                NormalizedMessage(
                    source_name=self.source.name,
                    external_id=str(event["id"]),
                    permalink=permalink,
                    author_external_id="NASA-EONET",
                    text=text,
                    language=self.source.language,
                    published_at=published_at,
                    raw={
                        "categories": event.get("categories", []),
                        "geometry": latest,
                    },
                )
            )
        newest = messages[0].external_id if messages else cursor
        return AdapterResult(messages=messages, cursor=newest)
