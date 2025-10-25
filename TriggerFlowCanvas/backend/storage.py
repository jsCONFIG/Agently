"""File based persistence helpers for TriggerFlow Canvas."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .schemas import FlowDefinition


class FlowStorage:
    """Handles loading and storing flow definitions on disk."""

    def __init__(self, storage_path: Path):
        self._storage_path = storage_path
        self._storage_path.parent.mkdir(parents=True, exist_ok=True)

    def load(self) -> FlowDefinition | None:
        """Return the stored flow definition if present."""
        if not self._storage_path.exists():
            return None
        data = json.loads(self._storage_path.read_text(encoding="utf-8"))
        return FlowDefinition.model_validate(data)

    def save(self, definition: FlowDefinition) -> None:
        """Persist the provided flow definition to disk."""
        data: Any = definition.model_dump(mode="json")
        self._storage_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
