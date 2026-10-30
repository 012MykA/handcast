import threading
import traceback

class Service:
    def __init__(self, name: str):
        self.name = name
        self.error = BaseException | None = None
        self._stop_event = threading.Event()
        self._thread = threading.Thread(target=self._loop, name=name, daemon=True)

    def start(self) -> None:
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread.is_alive():
            self._thread.join()

    @property
    def alive(self) -> bool:
        return self._thread.is_alive()

    def on_start(self) -> None: ...
    def on_stop(self) -> None: ...

    def run_once(self) -> None:
        raise NotImplementedError

    def _loop(self) -> None:
        try:
            self.on_start()
            while not self._stop_event.is_set():
                self.run_once()
        except BaseException as e:
            traceback.print_exc()
        finally:
            self.on_stop()
