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
    side: Side
    landmarks: tuple[Landmark, ...]
    world_landmarks: tuple[Landmark, ...]
    confidence: float
    timestamp: float


@dataclass(frozen=True, slots=True)
class TrackingResult:
    frame: Frame
    hands: tuple[HandPose, ...]


class GestureState(Enum):
    STARTED = "started"
    ENDED = "ended"


@dataclass(frozen=True, slots=True)
class GestureMatch:
    name: str
    side: Side
    score: float
    passed: bool  # score >= threshold на этом кадре
    active: bool = False  # после стабилизатора


@dataclass(frozen=True, slots=True)
class GestureEvent:
    name: str
    side: Side
    state: GestureState
    timestamp: float


class RecordPhase(Enum):
    IDLE = "idle"
    COUNTDOWN = "countdown"
    SAMPLING = "sampling"


@dataclass(frozen=True, slots=True)
class RecordStatus:
    phase: RecordPhase = RecordPhase.IDLE
    side: Side | None = None
    remaining_s: float = 0.0
    message: str = ""


@dataclass(frozen=True, slots=True)
class GestureResult:
    tracking: TrackingResult
    matches: tuple[GestureMatch, ...]
    events: tuple[GestureEvent, ...]
    record: RecordStatus
