from dataclasses import dataclass, replace

from handcast.core.models import GestureEvent, GestureMatch, GestureState, Side
from handcast.core.settings import StabilizerSettings


@dataclass(slots=True)
class _State:
    active: bool = False
    hits: int = 0
    misses: int = 0
    ended_at: float = float("-inf")


class GestureStabilizer:
    def __init__(self, cfg: StabilizerSettings):
        self._cfg = cfg
        self._states: dict[tuple[str, Side], _State] = {}

    def update(
        self, matches: list[GestureMatch], now: float
    ) -> tuple[list[GestureMatch], list[GestureEvent]]:
        seen = {(m.name, m.side): m for m in matches}
        cooldown = self._cfg.cooldown_ms / 1000
        events: list[GestureEvent] = []

        for key in seen.keys() | self._states.keys():
            st = self._states.setdefault(key, _State())
            if key in seen and seen[key].passed:
                st.hits += 1
                st.misses = 0
            else:
                st.misses += 1
                st.hits = 0

            if (
                not st.active
                and st.hits >= self._cfg.min_frames
                and now - st.ended_at >= cooldown
            ):
                st.active = True
                events.append(GestureEvent(key[0], key[1], GestureState.STARTED, now))
            elif st.active and st.misses >= self._cfg.release_frames:
                st.active = False
                st.ended_at = now
                events.append(GestureEvent(key[0], key[1], GestureState.ENDED, now))

        result = [
            replace(m, active=self._states[(m.name, m.side)].active) for m in matches
        ]
        return result, events
