"""1-D link positioning (seed localizer).

RF Vision native thin layer over :mod:`localization.tracking`: feeds raw
model predictions through :class:`PositionFilter` and maps the filtered
``[0, 1]`` coordinate to metres via :mod:`localization.geometry`. This is
the full extent of the validated positioning story -- 2-D/3-D positioning,
fingerprinting, and AoA/ToA methods are scheduled native work (see
``docs/research/SCIENTIFIC_VALIDATION_STATUS.md``).
"""

from __future__ import annotations

from typing import Optional

from localization.tracking.position_filter import (
    PositionFilter, PositionFilterConfig)
from localization.geometry.geometry import position_to_metres

__all__ = ["Position1D"]


class Position1D:
    """Stateful 1-D position tracker with metric output."""

    def __init__(self, cfg: dict) -> None:
        self.filter = PositionFilter(PositionFilterConfig.from_config(cfg))
        self.room_width_m = float(cfg.get("room_width", 5.0))

    def reset(self) -> None:
        """Forget filter state (person lost / stream restarted)."""
        self.filter.reset()

    def update(self, raw_position: Optional[float],
               timestamp: float) -> Optional[dict]:
        """Filter one raw prediction; return normalized + metric position."""
        if raw_position is None:
            return None
        filtered = self.filter.filter(raw_position, timestamp)
        if filtered is None:
            return None
        return {
            "position": filtered,
            "position_m": position_to_metres(filtered, self.room_width_m),
            "raw": raw_position,
        }
