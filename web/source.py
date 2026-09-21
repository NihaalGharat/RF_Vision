"""Data-source providers for the RF Vision web console (RFVISION-005).

RF Vision native, stdlib only. Providers feed envelope events into
``web/server.py``; the UI never sees anything but contracts.

Modes:
- ``disconnected`` — no hardware (default until RFVISION-003R). Emits
  nothing; status reports DISCONNECTED with null metrics.
- ``offline_fixture`` — replays ``web/fixtures/*.jsonl`` (validated
  recorded envelopes). Labeled OFFLINE_FIXTURE, never LIVE.
- ``simulated`` — deterministic seeded synthetic frames, labeled
  SIMULATED. For UI development only; never evidence.
- ``live`` — REFUSED in this operation (003 golden test failed; gate in
  ``LiveProvider`` raises until 003R explicitly enables it).
"""

from __future__ import annotations

import json
import math
import random
import time
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional

from web import contracts

__all__ = [
    "FIXTURE_DIR",
    "LiveUnavailable",
    "DisconnectedProvider",
    "FixtureProvider",
    "SimulatedProvider",
    "LiveProvider",
    "make_provider",
]

FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures"


class LiveUnavailable(RuntimeError):
    """Raised when the live path is requested before RFVISION-003R."""


class DisconnectedProvider:
    """No-data provider: emits nothing, reports DISCONNECTED."""

    mode = "off"
    source_state = "DISCONNECTED"

    def frames(self) -> Iterator[Dict[str, Any]]:
        """Yield no frames (finite empty iterator)."""
        return iter(())

    def latest_snapshot(self) -> None:
        """No snapshot exists while disconnected."""
        return None


class FixtureProvider:
    """Replay validated recorded envelopes from a JSONL fixture file."""

    mode = "fixture"
    source_state = "OFFLINE_FIXTURE"

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        if not self.path.exists():
            raise FileNotFoundError(f"fixture not found: {self.path}")
        self._events: List[Dict[str, Any]] = []
        with open(self.path, "r", encoding="utf-8") as fh:
            for lineno, line in enumerate(fh, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError as exc:
                    raise ValueError(
                        f"{self.path}:{lineno}: bad JSON: {exc}") from exc
                self._events.append(obj)
        if not self._events:
            raise ValueError(f"fixture is empty: {self.path}")
        # Fixtures must already be valid envelopes with provenance;
        # fail fast here, not in the browser.
        for obj in self._events:
            contracts.validate_envelope(json.dumps(obj))
        self._cursor = 0
        self._latest: Optional[Dict[str, Any]] = None

    def __len__(self) -> int:
        return len(self._events)

    def frames(self, loop: bool = True) -> Iterator[Dict[str, Any]]:
        """Replay fixture events in order (optionally looping).

        Replays at ~10 Hz so subscribers (and the packet counter) see a
        realistic cadence instead of a busy loop.
        """
        idx = 0
        while True:
            if idx >= len(self._events):
                if not loop:
                    return
                idx = 0
            event = self._events[idx]
            idx += 1
            if event.get("type") == "sensing.snapshot":
                self._latest = event
            yield event
            time.sleep(0.1)

    def latest_snapshot(self) -> Optional[Dict[str, Any]]:
        """Most recent sensing.snapshot seen during replay (or None)."""
        return self._latest


class SimulatedProvider:
    """Deterministic seeded synthetic frames (UI development only)."""

    mode = "simulated"
    source_state = "SIMULATED"

    def __init__(self, seed: int = 7, n_subcarriers: int = 64) -> None:
        self._rng = random.Random(seed)
        self._n = int(n_subcarriers)
        self._seq = 0
        self._latest: Optional[Dict[str, Any]] = None

    def _frame(self) -> Dict[str, Any]:
        self._seq += 1
        t = self._seq / 10.0  # 10 Hz synthetic cadence
        drift = math.sin(t * 0.3) * 8.0
        amplitudes = [28.0 + drift + self._rng.gauss(0, 2.0)
                      for _ in range(self._n)]
        phases = [self._rng.gauss(0, 0.4) for _ in range(self._n)]
        presence = "PERSON" if math.sin(t * 0.11) > 0.2 else "EMPTY"
        movement = ("MOVING" if presence == "PERSON"
                    and math.sin(t * 0.53) > 0.4 else "STATIC")
        payload = contracts.sensing_snapshot_payload(
            presence=presence,
            presence_prob=0.5 + 0.4 * abs(math.sin(t * 0.11)),
            movement=movement,
            movement_prob=0.5 + 0.4 * abs(math.sin(t * 0.53)),
            position=0.5 + 0.3 * math.sin(t * 0.07),
            position_m=None,  # no calibration in sim: metric unknown
            confidence=None,  # unvalidated: no confidence claimed
            rssi=-50.0 + drift * 0.3,
            amplitudes=amplitudes,
            phases=phases,
            validated=False,
        )
        payload["source_state"] = self.source_state
        event = contracts.wrap_event("sensing.snapshot", payload,
                                     source="rfvision-web(simulated)",
                                     seq=self._seq)
        self._latest = event
        return event

    def frames(self) -> Iterator[Dict[str, Any]]:
        """Infinite synthetic stream at ~10 Hz."""
        while True:
            yield self._frame()
            time.sleep(0.1)

    def latest_snapshot(self) -> Optional[Dict[str, Any]]:
        """Most recent synthetic snapshot (or None before first frame)."""
        return self._latest


class LiveProvider:
    """Live serial path — GATED until RFVISION-003R.

    Instantiation always raises :class:`LiveUnavailable`: RFVISION-003's
    golden test failed, so no UI path may claim live data in this
    operation. 003R will replace this gate with the validated receiver
    binding.
    """

    mode = "live"
    source_state = "LIVE_UNVERIFIED"

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        raise LiveUnavailable(
            "live CSI is blocked by RFVISION-003R (003 golden test FAILED); "
            "use offline_fixture or simulated")


def make_provider(mode: str, **kwargs: Any) -> Any:
    """Build a provider by mode name (raises ContractError/LiveUnavailable)."""
    if mode == "off":
        return DisconnectedProvider()
    if mode == "fixture":
        return FixtureProvider(kwargs.get("path", FIXTURE_DIR /
                                         "offline_demo.jsonl"))
    if mode == "simulated":
        return SimulatedProvider(seed=int(kwargs.get("seed", 7)))
    if mode == "live":
        return LiveProvider()
    raise contracts.ContractError(f"unknown source mode: {mode!r}")
