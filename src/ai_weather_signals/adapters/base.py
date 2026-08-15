from abc import ABC, abstractmethod
from dataclasses import dataclass, field

import httpx

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
