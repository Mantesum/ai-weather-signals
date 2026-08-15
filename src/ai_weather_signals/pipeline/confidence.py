from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass(frozen=True)
class ConfidenceInputs:
    llm: float
    geography: float
    time: float
    source_trust: float
    personal_weight: float
    independent_authors: int
    platforms: int
    media: bool
    official: bool
    copy_ratio: float = 0.0
    conflict_ratio: float = 0.0


def load_weights(path: Path) -> dict[str, float]:
    return {
        key: float(value)
        for key, value in yaml.safe_load(path.read_text(encoding="utf-8"))["weights"].items()
    }


def confidence_score(inputs: ConfidenceInputs, weights: dict[str, float]) -> float:
    base = (
        inputs.llm * weights["llm"]
        + inputs.geography * weights["geography"]
        + inputs.time * weights["time"]
        + inputs.source_trust * weights["source_trust"]
        + inputs.personal_weight * weights["assertion"]
    )
    bonus = min(inputs.independent_authors - 1, 3) * weights["independent_author"]
    bonus += min(inputs.platforms - 1, 2) * weights["platform"]
    bonus += weights["media"] if inputs.media else 0
    bonus += weights["official"] if inputs.official else 0
    penalty = (
        inputs.copy_ratio * weights["copy_penalty"] + inputs.conflict_ratio * weights["conflict_penalty"]
    )
    return round(max(0.0, min(1.0, base + bonus - penalty)), 4)


def event_status(score: float, authors: int, platforms: int, official: bool, conflict: float = 0) -> str:
    if conflict >= 0.5:
        return "conflicting"
    if score >= 0.75 and (authors >= 2 or official) and (platforms >= 2 or authors >= 3 or official):
        return "confirmed"
    if score >= 0.55 and (authors >= 2 or official):
        return "probable"
    return "unconfirmed"
