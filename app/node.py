"""Distributed vote counter using a simple cache."""

import time
from typing import MutableMapping

from .cache import Cache


class Node:
    """Maintain counters for nodes A and B using a cache."""

    def __init__(self, cache: MutableMapping | None = None) -> None:
        """Create a Node with an optional shared cache."""
        self.cache = Cache(store=cache) if not isinstance(cache, Cache) else cache
        for key in ("A", "B"):
            if self.cache.get(key) is None:
                self.cache.set(key, 0)
        self.value = self._calculate_total()

    def _calculate_total(self) -> int:
        return self.cache.get("A", 0) + self.cache.get("B", 0)

    @property
    def counts(self) -> dict[str, int]:
        return {"A": self.cache.get("A", 0), "B": self.cache.get("B", 0)}

    def record_vote(self, node_id: str) -> None:
        """Increment the counter for the given node."""
        nid = node_id.upper()
        if nid in ("A", "B"):
            self.cache.increment(nid)
            self.value = self._calculate_total()

    def record_vote_with_latency(self, node_id: str, delay_seconds: float) -> None:
        """Increment the counter after an artificial delay."""
        time.sleep(max(delay_seconds, 0))
        self.record_vote(node_id)
