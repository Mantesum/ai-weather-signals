from pathlib import Path

import yaml

from .schemas import SourceDefinition


def load_sources(path: Path) -> list[SourceDefinition]:
    if not path.exists():
        return []
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return [SourceDefinition.model_validate(item) for item in payload.get("sources", [])]


def save_sources(path: Path, sources: list[SourceDefinition]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {"version": 1, "sources": [item.model_dump(mode="json", exclude_none=True) for item in sources]}
    path.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")


def upsert_source(path: Path, definition: SourceDefinition) -> None:
    sources = load_sources(path)
    sources = [item for item in sources if item.name != definition.name]
    sources.append(definition)
    save_sources(path, sorted(sources, key=lambda item: item.name))


def set_source_enabled(path: Path, name: str, enabled: bool) -> None:
    sources = load_sources(path)
    found = False
    for source in sources:
        if source.name == name:
            source.enabled = enabled
            found = True
    if not found:
        raise KeyError(f"Unknown source: {name}")
    save_sources(path, sources)
