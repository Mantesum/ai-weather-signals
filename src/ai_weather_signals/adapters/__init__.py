from .base import Adapter, AdapterResult
from .cctv_jsonp import CCTVJsonpAdapter
from .eonet import EONETAdapter
from .gdelt import GDELTAdapter
from .google_news import GoogleNewsAdapter
from .jetstream import JetstreamAdapter
from .mastodon import MastodonAdapter
from .multi_rss import MultiRSSAdapter
from .reddit import RedditAdapter
from .rss import RSSAdapter
from .x_recent import XRecentSearchAdapter

__all__ = [
    "Adapter",
    "AdapterResult",
    "CCTVJsonpAdapter",
    "EONETAdapter",
    "GDELTAdapter",
    "GoogleNewsAdapter",
    "JetstreamAdapter",
    "MastodonAdapter",
    "MultiRSSAdapter",
    "RedditAdapter",
    "RSSAdapter",
    "XRecentSearchAdapter",
]
