from tkinter import Frame

import cv2

from handcast.capture.camera_capture import CameraCapture
from handcast.core.queues import RingQueue
from handcast.core.service import Service
from handcast.service.capture_service import CaptureService


class Application:
    def __init__(self):
        self.camera = CameraCapture()
        self.frame_queue: RingQueue[Frame] = RingQueue(maxsize=2)

        self.services: list[Service] = [
            CaptureService(self.camera, self.frame_queue),
        ]

    def run(self):
        for s in reversed(self.services):
            s.start()

        try:
            while True:
                frame = self.frame_queue.get(timeout=0.1)
                if frame is not None:
                    cv2.imshow("Camera", frame.image)

                if cv2.waitKey(1) & 0xFF == 27:  # Escape
                    break

                for s in self.services:
                    if s.error is not None:
                        raise RuntimeError(f"Service '{s.name}' failed") from s.error
        finally:
            self.shutdown()

    def shutdown(self):
        print(f"Lost frames: {self.frame_queue.dropped}")

        for s in self.services:
            s.stop()
        self.camera.release()
        cv2.destroyAllWindows()
