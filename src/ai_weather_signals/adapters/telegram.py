import os
from datetime import UTC, datetime

from ..schemas import NormalizedMessage
from .base import Adapter, AdapterResult


class TelegramAdapter(Adapter):
    def fetch(self, cursor: str | None = None) -> AdapterResult:
        try:
            from telethon.sync import TelegramClient
        except ImportError as error:
            raise RuntimeError("Install the 'telegram' extra to enable this adapter") from error
        api_id = int(os.environ["TELEGRAM_API_ID"])
        api_hash = os.environ["TELEGRAM_API_HASH"]
        session_path = os.getenv("TELEGRAM_SESSION_PATH", "data/private/telegram")
        messages: list[NormalizedMessage] = []
        with TelegramClient(session_path, api_id, api_hash) as client:
            for item in client.iter_messages(
                self.source.target, min_id=int(cursor or 0), limit=100, reverse=True
            ):
                published = item.date or datetime.now(UTC)
                messages.append(
                    NormalizedMessage(
                        source_name=self.source.name,
                        external_id=str(item.id),
                        permalink=f"https://t.me/{self.source.target.lstrip('@')}/{item.id}",
                        author_external_id=str(item.sender_id or ""),
                        text=item.message or "",
                        language=self.source.language,
                        published_at=published,
                        media_urls=["telegram:media"] if item.media else [],
                    )
                )
        newest = max((int(item.external_id) for item in messages), default=int(cursor or 0))
        return AdapterResult(messages=messages, cursor=str(newest))
