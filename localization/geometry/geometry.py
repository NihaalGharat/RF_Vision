"""Room geometry helpers (RF Vision native, stdlib only).

Maps the normalized 1-D link coordinate ``p in [0, 1]`` (0 = node A,
1 = node B) to physical metres along the link line, using the room
dimensions from config (``room_width`` = A-B separation). 2-D/3-D
geometry (trilateration, multi-node fusion) is a scheduled native work
package -- this module only covers the validated 1-D link model.
"""

from __future__ import annotations

__all__ = ["clamp01", "position_to_metres", "metres_to_position",
           "link_length_m"]


def clamp01(value: float) -> float:
    """Clamp a normalized coordinate into [0, 1]."""
    return min(max(float(value), 0.0), 1.0)


def link_length_m(room_width_m: float) -> float:
    """A-B link length in metres (config ``room_width``)."""
    if room_width_m <= 0:
        raise ValueError("room_width must be > 0")
    return float(room_width_m)


def position_to_metres(position: float, room_width_m: float) -> float:
    """Normalized link coordinate -> distance from node A in metres."""
    return clamp01(position) * link_length_m(room_width_m)


def metres_to_position(metres_from_a: float, room_width_m: float) -> float:
    """Distance from node A in metres -> normalized link coordinate."""
    return clamp01(metres_from_a / link_length_m(room_width_m))
