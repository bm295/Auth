import time
from typing import MutableMapping

class Cache:
    """Simple in-memory cache that can back a distributed counter."""

    def __init__(self, store: MutableMapping | None = None, ttl: float | None = None) -> None:
        self.store = store if store is not None else {}
        self.ttl = ttl
        self._expiry: dict[str, float] = {}

    def _is_expired(self, key: str) -> bool:
        if self.ttl is None:
            return False
        return self._expiry.get(key, float('inf')) < time.time()

    def get(self, key: str, default=None):
        if self._is_expired(key):
            self.delete(key)
            return default
        return self.store.get(key, default)

    def set(self, key: str, value) -> None:
        self.store[key] = value
        if self.ttl is not None:
            self._expiry[key] = time.time() + self.ttl

    def delete(self, key: str) -> None:
        self.store.pop(key, None)
        self._expiry.pop(key, None)

    def increment(self, key: str, amount: int = 1) -> int:
        value = self.get(key, 0) + amount
        self.set(key, value)
        return value
