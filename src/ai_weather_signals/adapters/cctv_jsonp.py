import json
from datetime import UTC, datetime, timedelta, timezone

import httpx

from ..schemas import NormalizedMessage
from .base import PUBLIC_FEED_HEADERS, Adapter, AdapterResult, strip_html

CHINA_TZ = timezone(timedelta(hours=8))


def _decode_jsonp(value: str) -> dict[str, object]:
    start = value.find("(")
    end = value.rfind(")")
    if start < 0 or end <= start:
        raise ValueError("CCTV response is not JSONP")
    payload = json.loads(value[start + 1 : end])
    if not isinstance(payload, dict):
        raise ValueError("CCTV JSONP payload must be an object")
    return payload


def _published_at(value: object) -> datetime:
    try:
        parsed = datetime.strptime(str(value), "%Y-%m-%d %H:%M:%S")
    except (TypeError, ValueError):
        return datetime.now(UTC)
    return parsed.replace(tzinfo=CHINA_TZ).astimezone(UTC)


class CCTVJsonpAdapter(Adapter):
    """Fetch bounded current-news lists directly from CCTV's public JSONP interface."""

    def fetch(self, cursor: str | None = None) -> AdapterResult:
        configured = self.source.options.get("endpoints", [self.source.target])
        endpoints = configured if isinstance(configured, list) else [str(configured)]
        endpoints = [str(endpoint).strip() for endpoint in endpoints if str(endpoint).strip()]
        if not endpoints:
            raise ValueError("CCTV JSONP source requires target or options.endpoints")

        total_limit = max(1, min(int(str(self.source.options.get("total_limit", 50))), 100))
        per_endpoint_limit = max(
            1, min(int(str(self.source.options.get("per_endpoint_limit", 40))), 80)
        )
        by_id: dict[str, NormalizedMessage] = {}
        successful_requests = 0
        last_error: Exception | None = None
        for endpoint in endpoints:
            try:
                response = self.client.get(endpoint, headers=PUBLIC_FEED_HEADERS)
                response.raise_for_status()
                payload = _decode_jsonp(response.text)
                data = payload.get("data")
                items = data.get("list", []) if isinstance(data, dict) else []
                if not isinstance(items, list):
                    raise ValueError("CCTV JSONP data.list must be an array")
                successful_requests += 1
            except (httpx.HTTPError, json.JSONDecodeError, ValueError) as error:
                last_error = error
                continue

            for item in items[:per_endpoint_limit]:
                if not isinstance(item, dict):
                    continue
                external_id = str(item.get("id") or item.get("url") or "").strip()
                if not external_id:
                    continue
                text = strip_html(
                    "\n".join(
                        filter(None, [str(item.get("title") or ""), str(item.get("brief") or "")])
                    )
                )
                if not text:
                    continue
                by_id[external_id] = NormalizedMessage(
                    source_name=self.source.name,
                    external_id=external_id,
                    permalink=str(item.get("url") or "") or None,
                    author_external_id="CCTV News",
                    text=text,
                    language=self.source.language,
                    published_at=_published_at(item.get("focus_date")),
                    raw={
                        "provider": "cctv_jsonp",
                        "endpoint": endpoint,
                        "keywords": item.get("keywords"),
                    },
                )

        if successful_requests == 0 and last_error is not None:
            raise last_error
        messages = sorted(by_id.values(), key=lambda item: item.published_at, reverse=True)[:total_limit]
        newest = messages[0].external_id if messages else cursor
        return AdapterResult(messages=messages, cursor=newest)
