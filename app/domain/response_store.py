from __future__ import annotations

from typing import Any


class InMemoryResponseStore:
    def __init__(self) -> None:
        self._store: dict[str, dict[str, Any]] = {}

    def put(self, response_id: str, payload: dict[str, Any]) -> None:
        self._store[response_id] = payload

    def get(self, response_id: str) -> dict[str, Any] | None:
        return self._store.get(response_id)
