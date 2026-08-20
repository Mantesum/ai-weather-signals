import hashlib
from datetime import UTC, datetime
from typing import Any

from ..schemas import NormalizedMessage
from .base import Adapter, AdapterResult


class GDELTAdapter(Adapter):
    """Bounded GDELT DOC 2.0 article search; configure at most one request per cycle."""

    def fetch(self, cursor: str | None = None) -> AdapterResult:
        maximum = max(1, min(int(str(self.source.options.get("max_records", 25))), 250))
        params: dict[str, str | int] = {
            "query": str(self.source.options.get("query", "extreme weather")),
            "mode": "ArtList",
            "format": "json",
            "maxrecords": maximum,
            "timespan": str(self.source.options.get("timespan", "1d")),
            "sort": "DateDesc",
        }
        response = self.client.get(
            self.source.target,
            params=params,
            headers={"User-Agent": "AIWeatherSignals/0.4 (+https://github.com/Mantesum/ai-weather-signals)"},
        )
        response.raise_for_status()
        payload: dict[str, Any] = response.json()
        messages = []
        for article in payload.get("articles", []):
            url = str(article.get("url", "")).strip()
            if not url:
                continue
            seen = str(article.get("seendate", ""))
            try:
                published_at = datetime.strptime(seen, "%Y%m%dT%H%M%SZ").replace(tzinfo=UTC)
            except ValueError:
                published_at = datetime.now(UTC)
            messages.append(
                NormalizedMessage(
                    source_name=self.source.name,
                    external_id=hashlib.sha256(url.encode()).hexdigest(),
                    permalink=url,
                    author_external_id=str(article.get("domain", "")),
                    text=str(article.get("title", "")),
                    language=str(article.get("language") or self.source.language),
                    published_at=published_at,
                    raw={
                        "provider": "gdelt_doc_2",
                        "source_country": article.get("sourcecountry"),
                    },
                )
            )
        newest = messages[0].external_id if messages else cursor
        return AdapterResult(messages=messages, cursor=newest)
