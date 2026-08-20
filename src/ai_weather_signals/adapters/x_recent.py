from datetime import datetime
from typing import Any

from ..schemas import NormalizedMessage
from .base import Adapter, AdapterResult, source_token


class XRecentSearchAdapter(Adapter):
    """Bounded X API v2 recent search using a resumable since_id cursor."""

    def fetch(self, cursor: str | None = None) -> AdapterResult:
        token_name = self.source.env_token or "X_BEARER_TOKEN"
        token = source_token(token_name)
        if not token:
            raise RuntimeError(f"Missing {token_name} for X recent search")

        query = str(self.source.options.get("query", "weather -is:retweet")).strip()
        if not query:
            raise ValueError("X recent search query must not be empty")
        maximum = max(10, min(int(str(self.source.options.get("max_results", 10))), 100))
        params: dict[str, str | int] = {
            "query": query,
            "max_results": maximum,
            "tweet.fields": "author_id,created_at,lang",
        }
        if cursor:
            params["since_id"] = cursor

        response = self.client.get(
            self.source.target,
            headers={"Authorization": f"Bearer {token}"},
            params=params,
        )
        response.raise_for_status()
        payload: dict[str, Any] = response.json()
        messages = [
            NormalizedMessage(
                source_name=self.source.name,
                external_id=str(post["id"]),
                permalink=f"https://x.com/i/web/status/{post['id']}",
                author_external_id=str(post.get("author_id", "")),
                text=str(post.get("text", "")),
                language=str(post.get("lang") or self.source.language),
                published_at=datetime.fromisoformat(str(post["created_at"]).replace("Z", "+00:00")),
                raw={"provider": "x_api_v2"},
            )
            for post in payload.get("data", [])
            if post.get("id") and post.get("created_at")
        ]
        newest = max((message.external_id for message in messages), key=int, default=cursor)
        return AdapterResult(messages=messages, cursor=newest)
