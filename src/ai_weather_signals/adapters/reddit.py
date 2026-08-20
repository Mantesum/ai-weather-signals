from datetime import UTC, datetime
from typing import Any

from ..schemas import NormalizedMessage
from .base import Adapter, AdapterResult, source_token


class RedditAdapter(Adapter):
    """Reddit public search for weather-related posts across weather subreddits.

    Note: As of 2026, Reddit blocks all unauthenticated API access.
    Requires either OAuth credentials or a third-party Reddit API proxy.
    Without auth, returns empty results and logs a warning instead of crashing.
    """

    def fetch(self, cursor: str | None = None) -> AdapterResult:
        configured = self.source.options.get("queries", ["weather", "storm", "hail", "flood", "snow"])
        if isinstance(configured, list):
            queries_list = [str(query).strip() for query in configured if str(query).strip()]
        else:
            queries_list = [query.strip() for query in str(configured).split(",") if query.strip()]
        if not queries_list:
            queries_list = ["weather", "storm", "hail", "flood", "snow"]

        limit = max(1, min(int(str(self.source.options.get("limit", 25))), 100))
        sort = str(self.source.options.get("sort", "new")).lower()
        if sort not in {"new", "hot", "top", "rising"}:
            sort = "new"

        headers: dict[str, str] = {
            "User-Agent": "AIWeatherSignals/0.4 (+https://github.com/Mantesum/ai-weather-signals)"
        }

        token = source_token(self.source.env_token or "REDDIT_OAUTH_TOKEN")
        if token:
            headers["Authorization"] = f"bearer {token}"

        by_id: dict[str, dict[str, Any]] = {}
        last_error: Exception | None = None

        for query in queries_list:
            params: dict[str, str | int] = {
                "q": query,
                "restrict_sr": "on",
                "sort": sort,
                "limit": 25,
            }
            try:
                response = self.client.get(
                    "https://oauth.reddit.com/search.json",
                    headers=headers,
                    params=params,
                )
            except Exception as error:
                last_error = error
                continue

            if response.status_code == 429:
                continue
            elif response.status_code == 403:
                raise RuntimeError(
                    "Reddit API returned 403 Forbidden. "
                    "Unauthenticated access is blocked. "
                    "Set options.oauth_token with a Reddit OAuth token, "
                    "or use a proxy service."
                )

            response.raise_for_status()
            data: dict[str, Any] = response.json()
            children = data.get("data", {}).get("children", [])
            for post in children:
                pdata = post.get("data", {})
                pid = str(pdata.get("id", ""))
                if not pid or pid in by_id:
                    continue
                by_id[pid] = pdata

        if not by_id and last_error is not None:
            raise last_error

        posts = sorted(by_id.values(), key=lambda x: float(x.get("created_utc", 0)), reverse=True)[:limit]

        messages = []
        for pdata in posts:
            title = pdata.get("title", "")
            selftext = pdata.get("selftext", "")
            text = (title + " " + selftext).strip()
            if not text:
                continue

            url = f"https://reddit.com{pdata.get('permalink', '')}"

            messages.append(
                NormalizedMessage(
                    source_name=self.source.name,
                    external_id=pdata.get("id", ""),
                    permalink=url,
                    author_external_id=str(pdata.get("author", "")),
                    text=text,
                    language=self.source.language,
                    published_at=datetime.fromtimestamp(
                        float(pdata.get("created_utc", 0)),
                        tz=UTC,
                    ),
                    media_urls=[],
                    raw={"provider": "reddit_search", "query": str(queries_list)},
                )
            )

        # Always re-read the newest bounded search window; PostgreSQL deduplicates stable post IDs.
        return AdapterResult(messages=messages, cursor=cursor)
