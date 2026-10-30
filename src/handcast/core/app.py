import time

import cv2

from handcast.capture.camera_capture import CameraCapture
from handcast.core.models import Frame, GestureResult, Side, TrackingResult
from handcast.core.queues import RingQueue
from handcast.core.service import Service
from handcast.core.settings import load_settings
from handcast.gestures.templates import GestureLibrary
from handcast.service.capture_service import CaptureService
from handcast.service.gesture_service import GestureService
from handcast.service.tracking_service import TrackingService
from handcast.tracking.mediapipe_hands import MediaPipeHandsTracker
from handcast.ui.overlay import draw_hints, draw_matches, draw_record_status, draw_text
from handcast.ui.skeleton import draw_hands


class Application:
    def __init__(self):
        self.settings = s = load_settings()

        self.library = GestureLibrary(s.gestures_path())
        self.library.load()

        self.camera = CameraCapture(s.camera.index)
        self.frame_queue: RingQueue[Frame] = RingQueue(maxsize=s.queues.frames)
        self.track_queue: RingQueue[TrackingResult] = RingQueue(
            maxsize=s.queues.tracking
        )
        self.gesture_queue: RingQueue[GestureResult] = RingQueue(
            maxsize=s.queues.gestures
        )

        self.gesture_service = GestureService(
            s, self.library, self.track_queue, self.gesture_queue
        )
        self.services: list[Service] = [
            CaptureService(self.camera, self.frame_queue, mirror=s.camera.mirror),
            TrackingService(
                MediaPipeHandsTracker(
                    max_hands=s.tracking.max_hands,
                    min_detection=s.tracking.min_detection,
                    min_presence=s.tracking.min_presence,
                    min_tracking=s.tracking.min_tracking,
                    swap_sides=s.tracking.swap_sides,
                ),
                self.frame_queue,
                self.track_queue,
            ),
            self.gesture_service,
        ]

    def run(self):
        for s in reversed(self.services):
            s.start()

        try:
            while True:
                result = self.gesture_queue.get(timeout=0.1)
                if result is not None:
                    self._handle_events(result)
                    self._render(result)

                key = cv2.waitKey(1) & 0xFF
                if key == 27:  # Escape
                    break
                elif key == ord("1"):
                    self.gesture_service.request_record(Side.LEFT)
                elif key == ord("2"):
                    self.gesture_service.request_record(Side.RIGHT)

                for s in self.services:
                    if s.error is not None:
                        raise RuntimeError(f"Service '{s.name}' failed") from s.error
        finally:
            self.shutdown()

    def _handle_events(self, result: GestureResult) -> None:
        for e in result.events:
            print(f"[gesture] {e.state.value:<7} {e.side.value:<5} {e.name}")

    def _render(self, result: GestureResult) -> None:
        tracking = result.tracking
        image = draw_hands(tracking.frame.image, tracking.hands)

        latency_ms = (time.perf_counter() - tracking.frame.timestamp) * 1000
        draw_text(
            image,
            f"latency {latency_ms:.0f} ms   hands {len(tracking.hands)}",
            (12, 28),
            0.7,
            (255, 255, 255),
            2,
        )
        draw_text(image, "gestures:", (12, 74), 0.6, (170, 170, 170))

        draw_matches(image, result.matches)
        draw_record_status(image, result.record)
        draw_hints(image)
        cv2.imshow("Tracking", image)

    def shutdown(self):
        for s in self.services:
            s.stop()
        self.camera.release()
        cv2.destroyAllWindows()
