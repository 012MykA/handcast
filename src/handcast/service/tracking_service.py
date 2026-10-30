from handcast.core.models import Frame, TrackingResult
from handcast.core.queues import RingQueue
from handcast.core.service import Service
from handcast.tracking.mediapipe_hands import MediaPipeHandsTracker


class TrackingService(Service):
    def __init__(
        self,
        tracker: MediaPipeHandsTracker,
        in_frame_queue: RingQueue[Frame],
        out_result_queue: RingQueue[TrackingResult],
    ):
        super().__init__("tracking")
        self._tracker = tracker
        self._frame_queue = in_frame_queue
        self._result_queue = out_result_queue

    def on_start(self) -> None:
        self._tracker.open()

    def on_stop(self) -> None:
        self._tracker.close()

    def run_once(self) -> None:
        frame = self._frame_queue.get(timeout=0.1)
        if frame is None:
            return

        hands = self._tracker.process(frame)
        self._result_queue.put(TrackingResult(frame, hands))
