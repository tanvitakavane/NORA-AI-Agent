"""Lightweight in-process event bus; optional dashboard subscriber."""
from collections import deque
from copy import deepcopy
from datetime import datetime, timezone
from threading import RLock
from typing import Callable

class EventBus:
    def __init__(self, capacity: int = 200):
        self._events = deque(maxlen=capacity)
        self._subscribers: list[Callable[[dict], None]] = []
        self._lock = RLock()
        self._sequence = 0

    def subscribe(self, callback: Callable[[dict], None]) -> None:
        with self._lock:
            self._subscribers.append(callback)

    def publish(self, kind: str, payload: dict, case_id: str) -> dict:
        with self._lock:
            self._sequence += 1
            event = {'id': self._sequence, 'type': kind, 'case_id': case_id,
                     'timestamp': datetime.now(timezone.utc).isoformat(),
                     'payload': deepcopy(payload)}
            self._events.append(event)
            subscribers = list(self._subscribers)
        for subscriber in subscribers:
            try:
                subscriber(deepcopy(event))
            except Exception:
                # Observability must never break a live call.
                pass
        return deepcopy(event)

    def recent(self, case_id: str | None = None) -> list[dict]:
        with self._lock:
            return deepcopy([e for e in self._events if case_id is None or e['case_id'] == case_id])

DEFAULT_BUS = EventBus()
