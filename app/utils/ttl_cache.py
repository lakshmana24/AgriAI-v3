from __future__ import annotations

import time
from dataclasses import dataclass
from threading import RLock
from typing import Dict, Generic, Optional, Tuple, TypeVar


K = TypeVar("K")
V = TypeVar("V")


@dataclass(frozen=True)
class CacheItem(Generic[V]):
    value: V
    expires_at: float


class TTLCache(Generic[K, V]):
    """A small in-memory TTL cache.

    This is intentionally simple and keeps all state in-process.
    """

    def __init__(self, ttl_seconds: float, max_items: int = 1000) -> None:
        self._ttl_seconds = ttl_seconds
        self._max_items = max_items
        self._data: Dict[K, CacheItem[V]] = {}
        self._lock = RLock()

    def set(self, key: K, value: V) -> None:
        now = time.monotonic()
        item = CacheItem(value=value, expires_at=now + self._ttl_seconds)
        with self._lock:
            self._data[key] = item
            self._prune_locked(now)

    def get(self, key: K) -> Optional[V]:
        now = time.monotonic()
        with self._lock:
            item = self._data.get(key)
            if item is None:
                return None
            if item.expires_at <= now:
                self._data.pop(key, None)
                return None
            return item.value

    def items(self) -> Dict[K, V]:
        now = time.monotonic()
        with self._lock:
            self._prune_locked(now)
            return {k: v.value for k, v in self._data.items()}

    def _prune_locked(self, now: float) -> None:
        expired_keys = [k for k, v in self._data.items() if v.expires_at <= now]
        for k in expired_keys:
            self._data.pop(k, None)

        if len(self._data) <= self._max_items:
            return

        sorted_items: list[Tuple[K, CacheItem[V]]] = sorted(
            self._data.items(), key=lambda kv: kv[1].expires_at
        )
        to_remove = len(self._data) - self._max_items
        for i in range(to_remove):
            self._data.pop(sorted_items[i][0], None)
