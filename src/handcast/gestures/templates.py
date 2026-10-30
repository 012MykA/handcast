import json
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from handcast.core.models import Side
from handcast.gestures.features import FEATURE_NAMES


@dataclass(eq=False)
class GestureTemplate:
    name: str
    side: Side
    values: np.ndarray
    palm_normal: np.ndarray
    hand_dir: np.ndarray
    samples: int = 1
    threshold: float | None = None
    ignore: tuple[str, ...] = ()
    mask: np.ndarray = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self.mask = np.array(
            [not any(tok in self.ignore for tok in n.split("_")) for n in FEATURE_NAMES]
        )

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "side": self.side.value,
            "samples": self.samples,
            "threshold": self.threshold,
            "ignore": list(self.ignore),
            "features": {
                n: round(float(v), 2) for n, v in zip(FEATURE_NAMES, self.values)
            },
            "orientation": {
                "palm_normal": [round(float(x), 3) for x in self.palm_normal],
                "hand_dir": [round(float(x), 3) for x in self.hand_dir],
            },
        }

    @classmethod
    def from_dict(cls, d: dict) -> "GestureTemplate":
        feats = d["features"]
        missing = [n for n in FEATURE_NAMES if n not in feats]
        if missing:
            raise ValueError(f"'{d.get('name', '?')}' misses features: {missing}")
        orient = d.get("orientation", {})
        return cls(
            name=d["name"],
            side=Side(d["side"]),
            values=np.array([feats[n] for n in FEATURE_NAMES], dtype=np.float64),
            palm_normal=np.array(
                orient.get("palm_normal", (0, 0, 0)), dtype=np.float64
            ),
            hand_dir=np.array(orient.get("hand_dir", (0, 0, 0)), dtype=np.float64),
            samples=int(d.get("samples", 1)),
            threshold=d.get("threshold"),
            ignore=tuple(d.get("ignore", ())),
        )


class GestureLibrary:
    def __init__(self, path: Path):
        self._path = path
        self._templates: list[GestureTemplate] = []

    @property
    def templates(self) -> tuple[GestureTemplate, ...]:
        return tuple(self._templates)

    def load(self) -> None:
        self._templates = []
        if not self._path.is_file():
            print(f"[gestures] {self._path} not found, starting empty")
            return
        data = json.loads(self._path.read_text(encoding="utf-8"))
        for item in data.get("gestures", []):
            try:
                self._templates.append(GestureTemplate.from_dict(item))
            except (KeyError, ValueError, TypeError) as e:
                print(f"[gestures] skipped invalid gesture: {e!r}")
        print(f"[gestures] loaded {len(self._templates)} gesture(s)")

    def save(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"version": 1, "gestures": [t.to_dict() for t in self._templates]}
        tmp = self._path.with_suffix(".tmp")
        tmp.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        tmp.replace(self._path)

    def add(self, template: GestureTemplate) -> None:
        self._templates.append(template)

    def next_name(self) -> str:
        used = {t.name for t in self._templates}
        n = 1
        while f"gesture_{n}" in used:
            n += 1
        return f"gesture_{n}"
