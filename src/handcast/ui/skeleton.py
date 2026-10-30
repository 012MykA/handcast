import cv2
import numpy as np

from handcast.core.models import HandPose, Side

# fmt: off
HAND_CONNECTIONS = [
    (0, 1), (1, 2), (2, 3), (3, 4),            # большой
    (0, 5), (5, 6), (6, 7), (7, 8),            # указательный
    (5, 9), (9, 10), (10, 11), (11, 12),       # средний
    (9, 13), (13, 14), (14, 15), (15, 16),     # безымянный
    (13, 17), (17, 18), (18, 19), (19, 20),    # мизинец
    (0, 17),                                   # ладонь
]
# fmt: on

# BGR
COLORS = {
    Side.LEFT: (80, 170, 255),
    Side.RIGHT: (238, 200, 80),
}


def draw_hands(image: np.ndarray, hands: tuple[HandPose, ...]) -> np.ndarray:
    out = image.copy()
    h, w = out.shape[:2]
    for hand in hands:
        color = COLORS[hand.side]
        pts = [(int(p.x * w), int(p.y * h)) for p in hand.landmarks]
        for a, b in HAND_CONNECTIONS:
            cv2.line(out, pts[a], pts[b], color, 2, cv2.LINE_AA)
        for pt in pts:
            cv2.circle(out, pt, 4, (255, 255, 255), -1, cv2.LINE_AA)
            cv2.circle(out, pt, 4, color, 1, cv2.LINE_AA)
        cv2.putText(
            out,
            f"{hand.side.value} {hand.confidence:.2f}",
            (pts[0][0] - 30, pts[0][1] + 28),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            color,
            2,
            cv2.LINE_AA,
        )
    return out
