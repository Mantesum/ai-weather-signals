from datetime import UTC, datetime, timedelta
from pathlib import Path

from ai_weather_signals.pipeline.cluster import ClusterCandidate, belongs_to_cluster
from ai_weather_signals.pipeline.confidence import (
    ConfidenceInputs,
    confidence_score,
    event_status,
    load_weights,
)


def test_confidence_requires_corroboration_for_confirmation() -> None:
    weights = load_weights(Path("config/confidence.yaml"))
    one = ConfidenceInputs(0.9, 0.95, 0.9, 0.8, 1, 1, 1, True, False)
    multiple = ConfidenceInputs(0.9, 0.95, 0.9, 0.8, 1, 3, 2, True, False)
    score_one = confidence_score(one, weights)
    score_multiple = confidence_score(multiple, weights)
    assert score_multiple > score_one
    assert event_status(score_one, 1, 1, False) == "unconfirmed"
    assert event_status(score_multiple, 3, 2, False) == "confirmed"


def test_cluster_uses_phenomenon_space_and_time() -> None:
    now = datetime.now(UTC)
    nearby = ClusterCandidate("rain", 55.76, 37.62, now)
    assert belongs_to_cluster(nearby, "rain", 55.75, 37.61, now - timedelta(hours=1))
    assert not belongs_to_cluster(nearby, "snow", 55.75, 37.61, now)
    assert not belongs_to_cluster(nearby, "rain", 59.93, 30.31, now)
