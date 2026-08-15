from ..schemas import SourceDefinition
from .base import Adapter
from .jetstream import JetstreamAdapter
from .mastodon import MastodonAdapter
from .rss import RSSAdapter
from .telegram import TelegramAdapter

ADAPTERS: dict[str, type[Adapter]] = {
    "jetstream": JetstreamAdapter,
    "mastodon": MastodonAdapter,
    "rss": RSSAdapter,
    "telegram": TelegramAdapter,
}


def build_adapter(source: SourceDefinition) -> Adapter:
    try:
        return ADAPTERS[source.adapter](source)
    except KeyError as error:
        raise ValueError(f"Unsupported adapter: {source.adapter}") from error
