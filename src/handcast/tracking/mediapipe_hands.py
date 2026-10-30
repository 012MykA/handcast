from pathlib import Path
import urllib.request

import cv2
import mediapipe as mp
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision
import urllib

from handcast.core.models import Frame, HandPose, Landmark, Side

MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/hand_landmarker/"
    "hand_landmarker/float16/1/hand_landmarker.task"
)

DEFAULT_MODEL_PATH = (
    Path(__file__).resolve().parents[3] / "models" / "hand_landmarker.task"
)


class MediaPipeHandsTracker:
    def __init__(
        self,
        model_path: Path = DEFAULT_MODEL_PATH,
        max_hands: int = 2,
        min_detection: float = 0.5,
        min_presence: float = 0.5,
        min_tracking: float = 0.5,
        swap_sides: bool = True,
    ):
        self._model_path = model_path
        self._max_hands = max_hands
        self._min_detection = min_detection
        self._min_presence = min_presence
        self._min_tracking = min_tracking
        self._swap_sides = swap_sides
        self._landmarker: vision.HandLandmarker | None = None
        self._last_ts_ms = -1

    def open(self) -> None:
        self._ensure_model()
        options = vision.HandLandmarkerOptions(
            base_options=mp_python.BaseOptions(model_asset_path=str(self._model_path)),
            running_mode=vision.RunningMode.VIDEO,
            num_hands=self._max_hands,
            min_hand_detection_confidence=self._min_detection,
            min_hand_presence_confidence=self._min_presence,
            min_tracking_confidence=self._min_tracking,
        )
        self._landmarker = vision.HandLandmarker.create_from_options(options)

    def close(self) -> None:
        if self._landmarker is not None:
            self._landmarker.close()
            self._landmarker = None

    def process(self, frame: Frame) -> tuple[HandPose, ...]:
        rgb_frame = cv2.cvtColor(frame.image, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)

        ts_ms = max(int(frame.timestamp * 1000), self._last_ts_ms + 1)
        self._last_ts_ms = ts_ms

        result = self._landmarker.detect_for_video(mp_image, ts_ms)

        hands = []
        for landmarks, handedness in zip(result.hand_landmarks, result.handedness):
            category = handedness[0]

            is_left = category.category_name == "Left"
            if self._swap_sides:
                is_left = not is_left

            side = Side.LEFT if is_left else Side.RIGHT

            pose = HandPose(
                side=side,
                landmarks=tuple(Landmark(p.x, p.y, p.z) for p in landmarks),
                confidence=category.score,
                timestamp=frame.timestamp,
            )
            hands.append(pose)

        return tuple(hands)

    def _ensure_model(self) -> None:
        if self._model_path.exists():
            return
        print(f"Downloading hand_landmarker model to {self._model_path}...")
        self._model_path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self._model_path.with_suffix(".tmp")
        urllib.request.urlretrieve(MODEL_URL, tmp)
        tmp.replace(self._model_path)
