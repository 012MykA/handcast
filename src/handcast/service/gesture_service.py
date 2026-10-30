from handcast.core.models import GestureResult, Side, TrackingResult
from handcast.core.queues import RingQueue
from handcast.core.service import Service
from handcast.core.settings import Settings
from handcast.gestures.matcher import GestureMatcher
from handcast.gestures.recorder import GestureRecorder
from handcast.gestures.stabilizer import GestureStabilizer
from handcast.gestures.templates import GestureLibrary


class GestureService(Service):
    def __init__(
        self,
        settings: Settings,
        library: GestureLibrary,
        in_queue: RingQueue[TrackingResult],
        out_queue: RingQueue[GestureResult],
    ):
        super().__init__("gesture")
        self._library = library
        self._in = in_queue
        self._out = out_queue
        self._matcher = GestureMatcher(settings.matching)
        self._stabilizer = GestureStabilizer(settings.stabilizer)
        self._recorder = GestureRecorder(settings.recording, library.next_name)

    def request_record(self, side: Side) -> None:
        self._recorder.request(side)

    def run_once(self) -> None:
        tracking = self._in.get(timeout=0.1)
        if tracking is None:
            return

        now = tracking.frame.timestamp

        status, new_template = self._recorder.update(tracking.hands, now)
        if new_template is not None:
            self._library.add(new_template)
            self._library.save()

        matches = self._matcher.match(tracking.hands, self._library.templates)
        matches, events = self._stabilizer.update(matches, now)

        self._out.put(GestureResult(tracking, tuple(matches), tuple(events), status))
