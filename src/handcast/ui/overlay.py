import math

import cv2
import numpy as np

from handcast.core.models import GestureMatch, RecordPhase, RecordStatus

FONT = cv2.FONT_HERSHEY_SIMPLEX
# BGR
WHITE = (255, 255, 255)
GREEN = (120, 220, 120)
YELLOW = (80, 210, 240)
GREY = (170, 170, 170)
ORANGE = (80, 170, 255)


def draw_text(image, text, org, scale=0.6, color=WHITE, thickness=1) -> None:
    cv2.putText(image, text, org, FONT, scale, (0, 0, 0), thickness + 2, cv2.LINE_AA)
    cv2.putText(image, text, org, FONT, scale, color, thickness, cv2.LINE_AA)


def draw_center_text(image, text, y, scale, color=WHITE, thickness=2) -> None:
    (tw, _), _ = cv2.getTextSize(text, FONT, scale, thickness)
    draw_text(image, text, ((image.shape[1] - tw) // 2, y), scale, color, thickness)


def draw_matches(
    image: np.ndarray, matches: tuple[GestureMatch, ...], top: int = 96
) -> None:
    y = top
    for m in sorted(matches, key=lambda m: (m.side.value, -m.score)):
        color = GREEN if m.active else YELLOW if m.passed else GREY
        draw_text(
            image, f"{m.side.value:<5} {m.name}  {m.score:.2f}", (12, y), 0.55, color
        )
        y += 22


def draw_record_status(image: np.ndarray, status: RecordStatus) -> None:
    h = image.shape[0]
    if status.phase is RecordPhase.COUNTDOWN:
        draw_center_text(
            image, str(math.ceil(status.remaining_s)), h // 2, 4.0, ORANGE, 6
        )
        draw_center_text(
            image, f"Show {status.side.value} hand gesture", h // 2 + 60, 0.9, ORANGE
        )
    elif status.phase is RecordPhase.SAMPLING:
        draw_center_text(image, "Hold still...", h // 2, 1.2, ORANGE)
    elif status.message:
        draw_center_text(image, status.message, h - 48, 0.8, GREEN)


def draw_hints(image: np.ndarray) -> None:
    draw_text(
        image,
        "1 / 2: record left / right gesture    Esc: quit",
        (12, image.shape[0] - 14),
        0.5,
        GREY,
    )
