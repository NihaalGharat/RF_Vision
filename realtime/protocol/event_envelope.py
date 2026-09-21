"""Versioned JSON event envelope for RF Vision real-time messages.

RF Vision native, stdlib only. Every message on the realtime bus (serial
bridge, future MQTT/WebSocket links, Unity bridge) is a JSON object with
``schema``, ``type``, ``ts`` (host Unix seconds), ``source``, ``seq`` and
``payload``. The envelope is transport-agnostic: ``dumps``/``parse``
round-trip through any text channel. Payload schemas for each ``type``
are specified in ``unity/integration/MESSAGE_FORMATS.md`` and
``docs/architecture/RFVISION_DATA_SCHEMA.md``.
"""

from __future__ import annotations

import json
import time
from typing import Any, Dict, Optional

__all__ = [
    "SCHEMA_VERSION",
    "EVENT_TYPES",
    "make_event",
    "parse_event",
    "EventError",
]

#: Envelope schema version. Bump on any envelope-field change.
SCHEMA_VERSION = 1

#: Known event types (payload schemas documented per type).
EVENT_TYPES = (
    "sensing.snapshot",     # presence/movement/position state
    "localization.update",  # filtered position incl. metric mapping
    "xai.explanation",      # feature-attribution payload
    "system.status",        # link health, rates, counters
    "system.log",           # human-readable log line
)


class EventError(ValueError):
    """Raised when an event envelope is invalid."""


def make_event(event_type: str, payload: Dict[str, Any], *,
               source: str = "rfvision",
               ts: Optional[float] = None,
               seq: int = 0) -> Dict[str, Any]:
    """Build a versioned event envelope (raises EventError on bad type)."""
    if event_type not in EVENT_TYPES:
        raise EventError(f"unknown event type: {event_type!r}")
    if not isinstance(payload, dict):
        raise EventError("payload must be an object")
    return {
        "schema": SCHEMA_VERSION,
        "type": event_type,
        "ts": float(ts if ts is not None else time.time()),
        "source": str(source),
        "seq": int(seq),
        "payload": payload,
    }


def dumps(event_type: str, payload: Dict[str, Any], **kwargs) -> str:
    """Build an event and serialize it to a JSON string."""
    return json.dumps(make_event(event_type, payload, **kwargs))


def parse_event(text: str) -> Dict[str, Any]:
    """Parse + validate an event envelope (raises EventError)."""
    try:
        obj = json.loads(text)
    except json.JSONDecodeError as exc:
        raise EventError(f"not JSON: {exc}") from exc
    if not isinstance(obj, dict):
        raise EventError("event must be an object")
    for key in ("schema", "type", "ts", "source", "seq", "payload"):
        if key not in obj:
            raise EventError(f"missing envelope field: {key}")
    if obj["schema"] != SCHEMA_VERSION:
        raise EventError(
            f"schema {obj['schema']} != {SCHEMA_VERSION} (upgrade required)")
    if obj["type"] not in EVENT_TYPES:
        raise EventError(f"unknown event type: {obj['type']!r}")
    if not isinstance(obj["payload"], dict):
        raise EventError("payload must be an object")
    return obj
