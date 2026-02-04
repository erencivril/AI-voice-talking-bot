from __future__ import annotations

from collections import deque
from dataclasses import dataclass
import time


@dataclass
class RateLimiter:
    max_calls: int
    window_seconds: float

    def __post_init__(self) -> None:
        self._calls: dict[str, deque[float]] = {}

    def allow(self, key: str) -> bool:
        if self.max_calls <= 0:
            return True

        now = time.monotonic()
        q = self._calls.get(key)
        if q is None:
            q = deque()
            self._calls[key] = q

        cutoff = now - self.window_seconds
        while q and q[0] < cutoff:
            q.popleft()

        if len(q) >= self.max_calls:
            return False

        q.append(now)
        return True
