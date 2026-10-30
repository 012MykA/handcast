from dataclasses import dataclass
from enum import Enum

import numpy as np


@dataclass(frozen=True, slots=True)
class Frame:
    image: np.ndarray
    index: int
    timestamp: float  # time.perf_counter()


class Side(Enum):
    LEFT = "left"
    RIGHT = "right"


@dataclass(frozen=True, slots=True)
class Landmark:
    x: float
    y: float
    z: float


@dataclass(frozen=True, slots=True)
class HandPose:
    size: Side
    landmarks: tuple[Landmark, ...]
    confidence: float
    timestamp: float


@dataclass(frozen=True, slots=True)
class TrackingResult:
    frame: Frame
    hands: tuple[HandPose, ...]
