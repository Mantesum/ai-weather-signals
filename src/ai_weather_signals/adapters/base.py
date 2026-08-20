import os
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from html.parser import HTMLParser
from pathlib import Path

import httpx
from dotenv import dotenv_values

from ..schemas import NormalizedMessage, SourceDefinition


@dataclass
class AdapterResult:
    messages: list[NormalizedMessage] = field(default_factory=list)
    cursor: str | None = None


class Adapter(ABC):
    def __init__(self, source: SourceDefinition, client: httpx.Client | None = None) -> None:
        self.source = source
        self.client = client or httpx.Client(timeout=20, follow_redirects=True)

    @abstractmethod
    def fetch(self, cursor: str | None = None) -> AdapterResult: ...


PUBLIC_FEED_HEADERS = {
    "Accept": "application/atom+xml, application/rss+xml, application/xml, text/xml, */*",
    "User-Agent": "AIWeatherSignals/0.4 (+https://github.com/Mantesum/ai-weather-signals)",
}


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


def source_token(name: str) -> str:
    """Resolve a source token from process environment, then the local ignored .env file."""
    value = os.getenv(name, "").strip()
    if value:
        return value
    dotenv_value = dotenv_values(Path.cwd() / ".env").get(name)
    return str(dotenv_value).strip() if dotenv_value else ""
