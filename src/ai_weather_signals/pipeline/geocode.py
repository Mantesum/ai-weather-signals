import math
import unicodedata
from dataclasses import dataclass
from pathlib import Path

import yaml


def _key(value: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", value).casefold().split())


@dataclass(frozen=True)
class City:
    id: str
    name: str
    country: str
    latitude: float
    longitude: float
    geonames_id: int | None = None
    aliases: tuple[str, ...] = ()


@dataclass(frozen=True)
class GeocodeMatch:
    city: City
    precision: float


class LocalGeocoder:
    def __init__(self, cities: list[City]) -> None:
        self.cities = cities
        self.index: dict[str, City] = {}
        for city in cities:
            for name in (city.name, *city.aliases):
                self.index[_key(name)] = city

    @classmethod
    def from_yaml(cls, path: Path) -> "LocalGeocoder":
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
        return cls([City(aliases=tuple(item.pop("aliases", [])), **item) for item in payload["cities"]])

    def names(self) -> set[str]:
        return set(self.index)

    def resolve(self, place: str | None, fallback_region: str | None = None) -> GeocodeMatch | None:
        for value, precision in ((place, 0.95), (fallback_region, 0.65)):
            if not value:
                continue
            key = _key(value)
            if key in self.index:
                return GeocodeMatch(self.index[key], precision)
            matches = [(name, city) for name, city in self.index.items() if len(name) >= 4 and name in key]
            if matches:
                return GeocodeMatch(max(matches, key=lambda item: len(item[0]))[1], precision - 0.1)
        return None


def haversine_km(a_lat: float, a_lon: float, b_lat: float, b_lon: float) -> float:
    radius = 6371.0088
    p1, p2 = math.radians(a_lat), math.radians(b_lat)
    dp, dl = math.radians(b_lat - a_lat), math.radians(b_lon - a_lon)
    h = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * radius * math.asin(math.sqrt(h))
