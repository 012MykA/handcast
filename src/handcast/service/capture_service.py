import time

import cv2

from handcast.capture.camera_capture import CameraCapture
from handcast.core.queues import RingQueue
from handcast.core.service import Service
from handcast.core.models import Frame


class CaptureService(Service):
    def __init__(
        self,
        camera: CameraCapture,
        out: RingQueue[Frame],
        mirror: bool = True,
    ):
        super().__init__("capture")
        self._camera = camera
        self._out = out
        self._mirror = mirror
        self._index = 0

    def run_once(self) -> None:
        image = self._camera.get_frame()
        if self._mirror:
            image = cv2.flip(image, 1)

        frame = Frame(
            image=image,
            index=self._index,
            timestamp=time.perf_counter(),
        )
        self._out.put(frame)
        self._index += 1
