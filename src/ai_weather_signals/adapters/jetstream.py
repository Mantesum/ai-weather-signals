import json
from datetime import datetime
from urllib.parse import urlencode, urlparse, urlunparse

from websockets.sync.client import connect

from ..schemas import NormalizedMessage
from .base import Adapter, AdapterResult


class JetstreamAdapter(Adapter):
    """Bounded Jetstream read; a worker reconnects using the microsecond cursor."""

    def fetch(self, cursor: str | None = None) -> AdapterResult:
        configured = self.source.options.get("collections", ["app.bsky.feed.post"])
        wanted = configured if isinstance(configured, list) else [str(configured)]
        query: list[tuple[str, str]] = [("wantedCollections", str(item)) for item in wanted]
        if cursor:
            query.append(("cursor", cursor))
        parsed = urlparse(self.source.target)
        url = urlunparse(parsed._replace(query=urlencode(query)))
        maximum = min(int(str(self.source.options.get("max_messages", 200))), 1000)
        timeout = min(float(str(self.source.options.get("read_timeout_seconds", 10))), 30)
        messages: list[NormalizedMessage] = []
        newest = cursor
        with connect(url, open_timeout=10, close_timeout=2) as websocket:
            while len(messages) < maximum:
                try:
                    event = json.loads(websocket.recv(timeout=timeout))
                except TimeoutError:
                    break
                newest = str(event.get("time_us") or newest or "")
                commit = event.get("commit") or {}
                record = commit.get("record") or {}
                if commit.get("operation") != "create" or record.get("$type") != "app.bsky.feed.post":
                    continue
                did = str(event.get("did", ""))
                rkey = str(commit.get("rkey", ""))
                messages.append(
                    NormalizedMessage(
                        source_name=self.source.name,
                        external_id=f"{did}:{rkey}",
                        permalink=f"https://bsky.app/profile/{did}/post/{rkey}",
                        author_external_id=did,
                        text=str(record.get("text", "")),
                        language=(record.get("langs") or [self.source.language])[0],
                        published_at=datetime.fromisoformat(str(record["createdAt"]).replace("Z", "+00:00")),
                        raw={"collection": "app.bsky.feed.post"},
                    )
                )
        return AdapterResult(messages=messages, cursor=newest)
