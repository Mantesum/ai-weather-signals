from ..schemas import SourceDefinition
from .base import Adapter
from .cctv_jsonp import CCTVJsonpAdapter
from .eonet import EONETAdapter
from .gdelt import GDELTAdapter
from .google_news import GoogleNewsAdapter
from .jetstream import JetstreamAdapter
from .mastodon import MastodonAdapter
from .multi_rss import MultiRSSAdapter
from .reddit import RedditAdapter
from .rss import RSSAdapter
from .telegram import TelegramAdapter
from .x_recent import XRecentSearchAdapter

ADAPTERS: dict[str, type[Adapter]] = {
    "cctv_jsonp": CCTVJsonpAdapter,
    "eonet": EONETAdapter,
    "gdelt": GDELTAdapter,
    "google_news": GoogleNewsAdapter,
    "jetstream": JetstreamAdapter,
    "mastodon": MastodonAdapter,
    "multi_rss": MultiRSSAdapter,
    "rss": RSSAdapter,
    "telegram": TelegramAdapter,
    "x_recent": XRecentSearchAdapter,
    "reddit": RedditAdapter,
}


def build_adapter(source: SourceDefinition) -> Adapter:
    try:
        return ADAPTERS[source.adapter](source)
    except KeyError as error:
        raise ValueError(f"Unsupported adapter: {source.adapter}") from error
