from dataclasses import replace

import numpy as np

from handcast.core.models import GestureMatch, HandPose
from handcast.core.settings import MatchingSettings
from handcast.gestures.features import (
    FEATURE_KINDS,
    HandFeatures,
    angle_deg,
    extract_features,
)
from handcast.gestures.templates import GestureTemplate


class GestureMatcher:
    def __init__(self, cfg: MatchingSettings):
        self._cfg = cfg
        tol = {
            "angle": cfg.angle_tolerance_deg,
            "spread": cfg.spread_tolerance_deg,
            "pinch": cfg.pinch_tolerance,
        }
        self._tol = np.array([tol[k] for k in FEATURE_KINDS], dtype=np.float64)

    def match(
        self, hands: tuple[HandPose, ...], templates: tuple[GestureTemplate, ...]
    ) -> list[GestureMatch]:
        matches: list[GestureMatch] = []
        for hand in hands:
            features = extract_features(hand)
            scored = []
            for t in templates:
                if t.side is not hand.side:
                    continue
                score = self.score(features, t)
                threshold = (
                    t.threshold if t.threshold is not None else self._cfg.threshold
                )
                scored.append(
                    GestureMatch(t.name, hand.side, score, score >= threshold)
                )
            if self._cfg.exclusive_per_hand:
                scored = self._keep_best_passed(scored)
            matches.extend(scored)
        return matches

    def score(self, f: HandFeatures, t: GestureTemplate) -> float:
        dev = (np.abs(f.values - t.values) / self._tol)[t.mask]
        if self._cfg.use_orientation:
            tol = self._cfg.orientation_tolerance_deg
            dev = np.append(
                dev,
                [
                    angle_deg(f.palm_normal, t.palm_normal) / tol,
                    angle_deg(f.hand_dir, t.hand_dir) / tol,
                ],
            )
        if dev.size == 0:
            return 0.0
        return max(0.0, 1.0 - float(np.sqrt(np.mean(dev**2))))

    @staticmethod
    def _keep_best_passed(matches: list[GestureMatch]) -> list[GestureMatch]:
        passed = [m for m in matches if m.passed]
        if len(passed) <= 1:
            return matches
        best = max(passed, key=lambda m: m.score)
        return [
            m if (not m.passed or m is best) else replace(m, passed=False)
            for m in matches
        ]
