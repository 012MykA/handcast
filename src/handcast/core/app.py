import time

import cv2

from handcast.capture.camera_capture import CameraCapture
from handcast.core.models import Frame, TrackingResult
from handcast.core.queues import RingQueue
from handcast.core.service import Service
from handcast.service.capture_service import CaptureService
from handcast.service.tracking_service import TrackingService
from handcast.tracking.mediapipe_hands import MediaPipeHandsTracker
from handcast.ui.skeleton import draw_hands


class Application:
    def __init__(self):
        self.camera = CameraCapture()
        self.frame_queue: RingQueue[Frame] = RingQueue(maxsize=2)
        self.track_queue: RingQueue[TrackingResult] = RingQueue(maxsize=2)

        self.services: list[Service] = [
            CaptureService(self.camera, self.frame_queue),
            TrackingService(
                MediaPipeHandsTracker(), self.frame_queue, self.track_queue
            ),
        ]

    def run(self):
        for s in reversed(self.services):
            s.start()

        try:
            while True:
                frame = self.frame_queue.get(timeout=0.1)
                if frame is not None:
                    cv2.imshow("Capture", frame.image)

                result = self.track_queue.get(timeout=0.1)
                if result is not None:
                    self._render(result)

                if cv2.waitKey(1) & 0xFF == 27:  # Escape
                    break

                for s in self.services:
                    if s.error is not None:
                        raise RuntimeError(f"Service '{s.name}' failed") from s.error
        finally:
            self.shutdown()

    def _render(self, result: TrackingResult) -> None:
        image = draw_hands(result.frame.image, result.hands)
        latency_ms = (time.perf_counter() - result.frame.timestamp) * 1000
        # fmt: off
        cv2.putText(
            image, f"fps {(1000/latency_ms):.0f}\nlatency {latency_ms:.0f} ms\nhands {len(result.hands)}", (12, 28),
            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2, cv2.LINE_AA,
        )
        # fmt: on
        cv2.imshow("Tracking", image)

    def shutdown(self):
        for s in self.services:
            s.stop()
        self.camera.release()
        cv2.destroyAllWindows()
