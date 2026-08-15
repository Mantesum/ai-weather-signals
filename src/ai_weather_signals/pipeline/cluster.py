from dataclasses import dataclass
from datetime import datetime, timedelta

from .geocode import haversine_km


@dataclass(frozen=True)
class ClusterCandidate:
    phenomenon: str
    latitude: float
    longitude: float
    observed_at: datetime


def belongs_to_cluster(
    candidate: ClusterCandidate,
    phenomenon: str,
    latitude: float,
    longitude: float,
    last_seen_at: datetime,
    radius_km: float = 35,
    window_hours: float = 3,
) -> bool:
    return (
        candidate.phenomenon == phenomenon
        and abs(candidate.observed_at - last_seen_at) <= timedelta(hours=window_hours)
        and haversine_km(candidate.latitude, candidate.longitude, latitude, longitude) <= radius_km
    )
