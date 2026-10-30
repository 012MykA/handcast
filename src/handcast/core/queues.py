from collections import deque
from multiprocessing import Condition


class RingQueue[T]:
    def __init__(self, max_size: int = 2):
        self._buf: deque[T] = deque(maxlen=max_size)
        self._cond = Condition()
        self._dropped = 0

    @property
    def dropped(self) -> int:
        return self._dropped

    def put(self, item: T) -> None:
        with self._cond:
            if len(self._buf) == self._buf.maxlen:
                self._dropped += 1
            self._buf.append(item)
            self._cond.notify()

    def get(self, timeout: float | None = None) -> T | None:
        with self._cond:
            if not self._buf:
                self._cond.wait(timeout)
            return self._buf.popleft() if self._buf else None
