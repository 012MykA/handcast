import json
from dataclasses import asdict, dataclass, field, fields, is_dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_SETTINGS_PATH = PROJECT_ROOT / "config" / "settings.json"


@dataclass(frozen=True, slots=True)
class CameraSettings:
    index: int = 0
    mirror: bool = True


@dataclass(frozen=True, slots=True)
class TrackingSettings:
    max_hands: int = 2
    min_detection: float = 0.5
    min_presence: float = 0.5
    min_tracking: float = 0.5
    swap_sides: bool = True


@dataclass(frozen=True, slots=True)
class QueueSettings:
    frames: int = 2
    tracking: int = 2
    gestures: int = 2


@dataclass(frozen=True, slots=True)
class MatchingSettings:
    threshold: float = 0.8
    angle_tolerance_deg: float = 45.0
    spread_tolerance_deg: float = 30.0
    pinch_tolerance: float = 0.6
    use_orientation: bool = False
    orientation_tolerance_deg: float = 40.0
    exclusive_per_hand: bool = True


@dataclass(frozen=True, slots=True)
class StabilizerSettings:
    min_frames: int = 4
    release_frames: int = 3
    cooldown_ms: int = 300


@dataclass(frozen=True, slots=True)
class RecordingSettings:
    countdown_s: float = 3.0
    samples: int = 15
    min_samples: int = 8
    sampling_timeout_s: float = 3.0
    min_confidence: float = 0.8
    message_s: float = 4.0


@dataclass(frozen=True, slots=True)
class PathSettings:
    gestures: str = "config/gestures.json"


@dataclass(frozen=True, slots=True)
class Settings:
    camera: CameraSettings = field(default_factory=CameraSettings)
    tracking: TrackingSettings = field(default_factory=TrackingSettings)
    queues: QueueSettings = field(default_factory=QueueSettings)
    matching: MatchingSettings = field(default_factory=MatchingSettings)
    stabilizer: StabilizerSettings = field(default_factory=StabilizerSettings)
    recording: RecordingSettings = field(default_factory=RecordingSettings)
    paths: PathSettings = field(default_factory=PathSettings)

    def gestures_path(self) -> Path:
        p = Path(self.paths.gestures)
        return p if p.is_absolute() else PROJECT_ROOT / p


def _build(cls, data: dict):
    """Constructs dataclass from dict"""
    known = {f.name: f for f in fields(cls)}
    for key in data.keys() - known.keys():
        print(f"[settings] unknown key '{key}' in  {cls.__name__} ignored")

    kwargs = {}
    for name, f in known.items():
        if name not in data:
            continue
        value = data[name]
        if is_dataclass(f.type):
            value = _build(f.type, value)
        kwargs[name] = value
    return cls(**kwargs)


def load_settings(path: Path = DEFAULT_SETTINGS_PATH) -> Settings:
    if not path.is_file():
        settings = Settings()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(asdict(settings), indent=2), encoding="utf-8")
        print(f"[settings] created default settings at {path}")
        return settings

    data = json.loads(path.read_text(encoding="utf-8"))
    return _build(Settings, data)
