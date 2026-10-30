import threading
from typing import Callable

import numpy as np

from handcast.core.models import HandPose, RecordPhase, RecordStatus, Side
from handcast.core.settings import RecordingSettings
from handcast.gestures.features import (
    FEATURE_NAMES,
    HandFeatures,
    extract_features,
    unit,
)
from handcast.gestures.templates import GestureTemplate


class GestureRecorder:
    def __init__(self, cfg: RecordingSettings, next_name: Callable[[], str]):
        self._cfg = cfg
        self._next_name = next_name
        self._lock = threading.Lock()
        self._pending: Side | None = None

        self._phase = RecordPhase.IDLE
        self._side: Side | None = None
        self._deadline = 0.0
        self._samples: list[HandFeatures] = []
        self._message = ""
        self._message_until = 0.0

    def request(self, side: Side) -> None:
        with self._lock:
            self._pending = side

    def update(
        self, hands: tuple[HandPose, ...], now: float
    ) -> tuple[RecordStatus, GestureTemplate | None]:
        with self._lock:
            pending, self._pending = self._pending, None

        if pending is not None:
            self._phase = RecordPhase.COUNTDOWN
            self._side = pending
            self._deadline = now + self._cfg.countdown_s
            self._samples = []
            self._message = ""

        if self._phase is RecordPhase.COUNTDOWN and now >= self._deadline:
            self._phase = RecordPhase.SAMPLING
            self._deadline = now + self._cfg.sampling_timeout_s

        template = None
        if self._phase is RecordPhase.SAMPLING:
            hand = next(
                (
                    h
                    for h in hands
                    if h.side is self._side and h.confidence >= self._cfg.min_confidence
                ),
                None,
            )
            if hand is not None:
                self._samples.append(extract_features(hand))

            if len(self._samples) >= self._cfg.samples:
                template = self._finish(now)
            elif now >= self._deadline:
                if len(self._samples) >= self._cfg.min_samples:
                    template = self._finish(now)
                else:
                    self._to_idle(
                        now, f"{self._side.value} hand not visible, try again"
                    )

        return self._status(now), template

    def _finish(self, now: float) -> GestureTemplate:
        stack = np.array([s.values for s in self._samples])
        values = np.median(stack, axis=0)
        stds = stack.std(axis=0)
        template = GestureTemplate(
            name=self._next_name(),
            side=self._side,
            values=values,
            palm_normal=unit(np.mean([s.palm_normal for s in self._samples], axis=0)),
            hand_dir=unit(np.mean([s.hand_dir for s in self._samples], axis=0)),
            samples=len(self._samples),
        )

        print(
            f"\n[record] '{template.name}' ({template.side.value}), {template.samples} samples"
        )
        for n, v, sd in zip(FEATURE_NAMES, values, stds):
            print(f"  {n:<20}{v:8.2f} ± {sd:5.2f}")

        self._to_idle(now, f"saved '{template.name}' ({template.side.value})")
        return template

    def _to_idle(self, now: float, message: str) -> None:
        self._phase = RecordPhase.IDLE
        self._samples = []
        self._message = message
        self._message_until = now + self._cfg.message_s

    def _status(self, now: float) -> RecordStatus:
        if self._phase is RecordPhase.COUNTDOWN:
            return RecordStatus(self._phase, self._side, max(0.0, self._deadline - now))
        if self._phase is RecordPhase.SAMPLING:
            return RecordStatus(self._phase, self._side)
        return RecordStatus(message=self._message if now < self._message_until else "")
