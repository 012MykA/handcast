from dataclasses import dataclass

import numpy as np


@dataclass
class Frame:
    image: np.ndarray
    index: int
    timestamp: float  # time.perf_counter()
