from datetime import datetime
from typing import Any

from ..schemas import NormalizedMessage
from .base import Adapter, AdapterResult, source_token, strip_html


class MastodonAdapter(Adapter):
    def fetch(self, cursor: str | None = None) -> AdapterResult:
        configured = self.source.options.get("hashtags")
        if isinstance(configured, list):
            hashtags = list(dict.fromkeys(str(item).lstrip("#") for item in configured if str(item)))
        else:
            hashtags = [str(self.source.options.get("hashtag", "weather")).lstrip("#")]
        headers: dict[str, str] = {}
        token = source_token(self.source.env_token or "MASTODON_ACCESS_TOKEN")
        if token:
            headers["Authorization"] = f"Bearer {token}"
        total_limit = min(int(str(self.source.options.get("limit", 40))), 40)
        per_tag_limit = max(1, min(40, (total_limit + len(hashtags) - 1) // len(hashtags)))
        by_id: dict[str, dict[str, Any]] = {}
        for hashtag in hashtags:
            url = f"{self.source.target.rstrip('/')}/api/v1/timelines/tag/{hashtag}"
            params: dict[str, str | int] = {"limit": per_tag_limit}
            if cursor:
                params["min_id"] = cursor
            response = self.client.get(url, headers=headers, params=params)
            response.raise_for_status()
            for status in response.json():
                by_id[str(status["id"])] = status
        statuses = sorted(by_id.values(), key=lambda item: int(str(item["id"])), reverse=True)[:total_limit]
        messages = []
        for status in statuses:
            media = [item.get("url") for item in status.get("media_attachments", []) if item.get("url")]
            account = status.get("account", {})
            messages.append(
                NormalizedMessage(
                    source_name=self.source.name,
                    external_id=str(status["id"]),
                    permalink=status.get("url"),
                    author_external_id=str(account.get("id", "")),
                    text=strip_html(status.get("content", "")),
                    language=status.get("language") or self.source.language,
                    published_at=datetime.fromisoformat(status["created_at"].replace("Z", "+00:00")),
                    media_urls=media,
                )
            )
        newest = max((message.external_id for message in messages), key=int, default=cursor)
        return AdapterResult(messages=messages, cursor=newest)
