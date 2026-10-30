import time

from handcast.capture.camera_capture import CameraCapture
from handcast.core.queues import RingQueue
from handcast.core.service import Service
from handcast.core.models import Frame


class CaptureService(Service):
    def __init__(self, camera: CameraCapture, out: RingQueue[Frame]):
        super().__init__("capture")
        self._camera = camera
        self._out = out
        self._index = 0

    def run_once(self) -> None:
        image = self._camera.get_frame()

        frame = Frame(
            image=image,
            index=self._index,
            timestamp=time.perf_counter(),
        )
        self._out.put(frame)
        self._index += 1
