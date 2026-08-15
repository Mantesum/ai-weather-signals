import os
from datetime import datetime
from html.parser import HTMLParser

from ..schemas import NormalizedMessage
from .base import Adapter, AdapterResult


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        self.parts.append(data)


def strip_html(value: str) -> str:
    parser = _TextExtractor()
    parser.feed(value)
    return " ".join("".join(parser.parts).split())


class MastodonAdapter(Adapter):
    def fetch(self, cursor: str | None = None) -> AdapterResult:
        hashtag = str(self.source.options.get("hashtag", "weather")).lstrip("#")
        url = f"{self.source.target.rstrip('/')}/api/v1/timelines/tag/{hashtag}"
        headers: dict[str, str] = {}
        token = os.getenv(self.source.env_token or "MASTODON_ACCESS_TOKEN", "")
        if token:
            headers["Authorization"] = f"Bearer {token}"
        params: dict[str, str | int] = {"limit": min(int(str(self.source.options.get("limit", 40))), 40)}
        if cursor:
            params["min_id"] = cursor
        response = self.client.get(url, headers=headers, params=params)
        response.raise_for_status()
        statuses = response.json()
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
