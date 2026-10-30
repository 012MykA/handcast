from dataclasses import dataclass

import numpy as np

from handcast.core.models import HandPose, Side

FINGERS = ("thumb", "index", "middle", "ring", "pinky")

# цепочки точек MediaPipe: запястье → основание → ... → кончик
CHAINS = {
    "thumb": (0, 1, 2, 3, 4),
    "index": (0, 5, 6, 7, 8),
    "middle": (0, 9, 10, 11, 12),
    "ring": (0, 13, 14, 15, 16),
    "pinky": (0, 17, 18, 19, 20),
}

PROXIMAL = {
    "thumb": (2, 3),
    "index": (5, 6),
    "middle": (9, 10),
    "ring": (13, 14),
    "pinky": (17, 18),
}
TIPS = {"index": 8, "middle": 12, "ring": 16, "pinky": 20}

ANGLE_NAMES = tuple(f"{f}_{j}" for f in FINGERS for j in ("base", "mid", "tip"))
SPREAD_NAMES = tuple(f"spread_{a}_{b}" for a, b in zip(FINGERS, FINGERS[1:]))
PINCH_NAMES = tuple(f"pinch_{f}" for f in FINGERS[1:])

FEATURE_NAMES = ANGLE_NAMES + SPREAD_NAMES + PINCH_NAMES
FEATURE_KINDS = (
    ("angle",) * len(ANGLE_NAMES)
    + ("spread",) * len(SPREAD_NAMES)
    + ("pinch",) * len(PINCH_NAMES)
)


def unit(v: np.ndarray) -> np.ndarray:
    n = np.linalg.norm(v)
    return v / n if n > 1e-9 else v


def angle_deg(u: np.ndarray, v: np.ndarray) -> float:
    denom = np.linalg.norm(u) * np.linalg.norm(v)
    if denom < 1e-9:
        return 0.0
    return float(np.degrees(np.arccos(np.clip(np.dot(u, v) / denom, -1.0, 1.0))))


@dataclass(frozen=True, slots=True, eq=False)
class HandFeatures:
    values: np.ndarray
    palm_normal: np.ndarray
    hand_dir: np.ndarray


def extract_features(hand: HandPose) -> HandFeatures:
    p = np.array([(l.x, l.y, l.z) for l in hand.world_landmarks], dtype=np.float64)

    angles = []
    for finger in FINGERS:
        c = CHAINS[finger]
        bones = [p[c[i + 1]] - p[c[i]] for i in range(4)]
        for k in (1, 2, 3):
            angles.append(angle_deg(bones[k - 1], bones[k]))

    prox = {f: p[b] - p[a] for f, (a, b) in PROXIMAL.items()}
    spread = [angle_deg(prox[a], prox[b]) for a, b in zip(FINGERS, FINGERS[1:])]

    palm_size = np.linalg.norm(p[9] - p[0])
    if palm_size > 1e-9:
        pinch = [np.linalg.norm(p[4] - p[TIPS[f]]) / palm_size for f in FINGERS[1:]]
    else:
        pinch = [0.0] * len(PINCH_NAMES)

    normal = unit(np.cross(p[5] - p[0], p[17] - p[0]))
    if hand.side is Side.LEFT:
        normal = -normal

    return HandFeatures(
        values=np.array(angles + spread + pinch, dtype=np.float64),
        palm_normal=normal,
        hand_dir=unit(p[9] - p[0]),
    )
