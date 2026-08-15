from collections import Counter
from threading import Lock


class Metrics:
    def __init__(self) -> None:
        self._values: Counter[str] = Counter()
        self._lock = Lock()

    def inc(self, name: str, amount: int = 1) -> None:
        with self._lock:
            self._values[name] += amount

    def snapshot(self) -> dict[str, int]:
        with self._lock:
            return dict(self._values)


metrics = Metrics()
