import os
import time
from dataclasses import dataclass
from threading import Lock


@dataclass
class KeyState:
    index: int
    secret: str
    consecutive_failures: int = 0
    cooldown_until: float = 0
    last_failure: float | None = None
    last_success: float | None = None

    def public_state(self) -> dict:
        return {
            "keyIndex": self.index, "available": time.monotonic() >= self.cooldown_until,
            "consecutiveFailures": self.consecutive_failures,
            "cooldownUntil": self.cooldown_until or None, "lastFailure": self.last_failure,
            "lastSuccess": self.last_success,
        }


class GeminiKeyPool:
    def __init__(self, cooldown_seconds: int = 120, environ: dict[str, str] | None = None):
        source = environ if environ is not None else os.environ
        configured = sorted(
            ((int(name.rsplit("_", 1)[1]), value) for name, value in source.items()
             if name.startswith("GEMINI_API_KEY_") and name.rsplit("_", 1)[1].isdigit() and value.strip()),
            key=lambda item: item[0],
        )
        fallback = source.get("GEMINI_API_KEY", "").strip()
        if fallback and not configured:
            configured = [(1, fallback)]
        self._states = [KeyState(index, secret) for index, secret in configured]
        self._cooldown = cooldown_seconds
        self._cursor = 0
        self._lock = Lock()

    def acquire(self, excluded: set[int] | None = None) -> KeyState | None:
        excluded = excluded or set()
        with self._lock:
            now = time.monotonic()
            for offset in range(len(self._states)):
                position = (self._cursor + offset) % len(self._states)
                state = self._states[position]
                if state.index not in excluded and state.cooldown_until <= now:
                    self._cursor = (position + 1) % len(self._states)
                    return state
        return None

    def report_success(self, index: int):
        with self._lock:
            state = self._find(index)
            state.consecutive_failures = 0
            state.cooldown_until = 0
            state.last_success = time.monotonic()

    def report_failure(self, index: int, credential: bool = False):
        with self._lock:
            state = self._find(index)
            state.consecutive_failures += 1
            state.last_failure = time.monotonic()
            if credential or state.consecutive_failures >= 2:
                state.cooldown_until = time.monotonic() + self._cooldown

    def _find(self, index: int) -> KeyState:
        return next(state for state in self._states if state.index == index)

    def __len__(self):
        return len(self._states)

