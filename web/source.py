"""Data-source providers for the RF Vision web console (RFVISION-005/009).

RF Vision native. Providers feed envelope events into ``web/server.py``;
the UI never sees anything but contracts.

Modes:
- ``disconnected`` — no hardware. Emits nothing; status reports
  DISCONNECTED with null metrics.
- ``offline_fixture`` — replays ``web/fixtures/*.jsonl`` (validated
  recorded envelopes). Labeled OFFLINE_FIXTURE, never LIVE.
- ``simulated`` — deterministic seeded synthetic frames, labeled
  SIMULATED. For UI development only; never evidence.
- ``live`` — validated CURRENT receiver (RFVISION-003R-C2 PASS) on
  ``/dev/ttyUSB0`` @ 921600. Starts LIVE_UNVERIFIED; promotes to
  LIVE_VERIFIED only after the ~3 s session gate passes. Parses
  strictly through :class:`EspCsvAdapter` (never relaxed), fabricates
  nothing, counts every malformed line (never silently discarded).

Live/recording separation: the session ingests EVERY line (lossless
counting + optional lossless raw recording); ``frames()`` yields only
latest-frame envelopes decimated to ~10 Hz so visualization can never
back-pressure capture.
"""

from __future__ import annotations

import collections
import hashlib
import json
import math
import random
import time
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional

from csi.parser.csi_parser import PacketError, amplitude
from csi.parser.esp_csv_adapter import EspCsvAdapter
from web import contracts
from web.live_serial import (
    DEFAULT_BAUD,
    DEFAULT_PORT,
    FakeLineSource,
    LiveSerialError,
    SerialLineSource,
)

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
    """Live serial CSI path bound to the validated CURRENT receiver.

    Opens the port ONCE per session (``frames()`` run) at 921600 baud,
    reads binary-safe raw lines, and parses ``CSI_DATA`` through the
    EXISTING strict :class:`EspCsvAdapter` — parser rules are never
    relaxed, samples are never fabricated, malformed lines are counted
    (with reasons + recent examples) and never silently discarded.

    Provenance gate: sessions start ``LIVE_UNVERIFIED`` and promote to
    ``LIVE_VERIFIED`` only after ~``gate_window_s`` of streaming passes
    every check (records present, valid parse, plausible rate, single
    consistent channel, expected BSSID, physically possible throughput,
    no duplication-storm signature, fresh data). A failed gate stays
    ``LIVE_UNVERIFIED`` with reasons; transport death before any valid
    record reports ``DISCONNECTED`` with the diagnostic.
    """

    mode = "live"

    #: Session gate + anomaly thresholds (C2 phenomenology baked in).
    GATE_WINDOW_S = 3.0
    GATE_MIN_RATE_HZ = 5.0
    # Genuine rate varies with AP traffic (C1 101 Hz, C2 75 Hz, live
    # 44–156 Hz observed); duplication storms replay at thousands of
    # lines/s, far above this ceiling.
    GATE_MAX_RATE_HZ = 220.0
    FRAME_HZ = 10.0
    STALE_AFTER_S = 3.0
    #: Consecutive byte-identical lines that declare a duplication storm
    #: (genuine CSI carries timestamps + noise: exact repeats are
    #: effectively impossible; C2 storms replayed tens of thousands).
    STORM_REPEAT_LINES = 32
    RATE_WINDOW_N = 240
    RSSI_WINDOW_N = 120
    REC_MAX_SECONDS = 120.0  # bound covers a 15 s warm-up + 60 s clean
    # protocol window plus margins (RFVISION-011); still bounded by design

    def __init__(self, port: str = DEFAULT_PORT, baud: int = DEFAULT_BAUD,
                 expected_bssid: str = "8c:53:c3:5b:e1:59",
                 expected_channel: int = 1,
                 board_mac: str = "b0:3f:d3:70:20:3c",
                 line_source: Any = None,
                 gate_window_s: float = GATE_WINDOW_S,
                 settle_s: float = 2.0,
                 frame_hz: float = FRAME_HZ,
                 stale_after_s: float = STALE_AFTER_S) -> None:
        self.port = str(port)
        self.baud = int(baud)
        self.expected_bssid = str(expected_bssid).lower()
        self.expected_channel = int(expected_channel)
        self.board_mac = str(board_mac)
        self._factory_source = line_source
        self.gate_window_s = float(gate_window_s)
        self.settle_s = float(settle_s)
        self.frame_hz = float(frame_hz)
        self.stale_after_s = float(stale_after_s)
        self._reset_session(manual=True)
        self._latest: Optional[Dict[str, Any]] = None
        self._stop = False
        self._source: Any = None

    # -- session state -------------------------------------------------
    def _reset_session(self, manual: bool = False) -> None:
        self._adapter = EspCsvAdapter()
        self._valid = 0
        self._malformed = 0
        self._non_csi = 0
        self._malformed_recent: collections.deque = collections.deque(
            maxlen=5)
        self._last_seq: Optional[int] = None
        self._gaps = 0
        self._missing: List[int] = []
        self._duplicates = 0
        self._out_of_order = 0
        self._channels: Dict[int, int] = {}
        self._bssids: Dict[str, int] = {}
        self._rssi: collections.deque = collections.deque(
            maxlen=self.RSSI_WINDOW_N)
        self._arrivals: collections.deque = collections.deque(
            maxlen=self.RATE_WINDOW_N)
        self._last_sample: Any = None
        self._last_valid_ts: Optional[float] = None
        self._last_line = ""
        self._consec_identical = 0
        self._storm = False
        self._storm_epochs = 0
        self._settle_epochs = 0
        self._tp_ever = False
        self._byte_marks: collections.deque = collections.deque(maxlen=2048)
        self._bytes_start = 0
        self._session_start: Optional[float] = None
        self._gate_passed = False
        self._gate_reasons: List[str] = ["gate not yet evaluated"]
        self._gate_evaluated = False
        self._gate_t0: Optional[float] = None
        self._settle_ok = False
        self._settle_start: Optional[float] = None
        self._pre_gate_storm = False
        self._transport_error: Optional[str] = None
        self._last_yield_ts = 0.0
        self._rec_fp: Any = None
        self._rec_path: Optional[str] = None
        self._rec_bytes = 0
        self._rec_start: Optional[float] = None
        self._rec_max_s = self.REC_MAX_SECONDS
        self._rec_sha: Optional[str] = None
        self._rec_last_info: Optional[Dict[str, Any]] = None
        if manual:
            self._session_id = "NO_ACTIVE_SESSION"

    @property
    def source_state(self) -> str:
        """Current provenance token (gate + transport aware)."""
        if self._transport_error is not None and self._valid == 0:
            return "DISCONNECTED"
        if self._gate_passed:
            return "LIVE_VERIFIED"
        return "LIVE_UNVERIFIED"

    def close(self) -> None:
        """Request session stop + release the port (idempotent)."""
        self._stop = True
        self._stop_recording()
        source, self._source = self._source, None
        if source is not None:
            try:
                source.close()
            except Exception:
                pass

    # -- ingest ----------------------------------------------------------
    def _begin_session(self) -> Any:
        # An armed recording survives session start so "Record then Start
        # stream" captures from the first line (bounded as always).
        keep = (self._rec_fp, self._rec_path, self._rec_bytes,
                self._rec_start, self._rec_max_s, self._rec_sha,
                self._rec_last_info)
        self._reset_session()
        (self._rec_fp, self._rec_path, self._rec_bytes,
         self._rec_start, self._rec_max_s, self._rec_sha,
         self._rec_last_info) = keep
        self._stop = False
        self._session_start = time.time()
        self._session_id = (
            f"LIVE-{self.board_mac.replace(':', '')}-"
            f"{int(self._session_start)}")
        source = self._factory_source
        if source is None:
            source = SerialLineSource(port=self.port, baud=self.baud)
        self._source = source
        try:
            source.open()
        except LiveSerialError as exc:
            self._transport_error = str(exc)
            self._source = None
            raise
        self._bytes_start = getattr(source, "bytes_read", 0)
        return source

    def _ingest(self, line: str,
                rx_ns: Optional[int] = None) -> None:
        text = line.strip()
        if not text:
            return
        # Duplication-storm signature: byte-identical consecutive lines.
        # Rising-edge counted as epochs so pre-settle transients stay
        # distinguishable from storms inside the validation window.
        if text == self._last_line:
            self._consec_identical += 1
            if self._consec_identical == self.STORM_REPEAT_LINES:
                self._storm = True
                self._storm_epochs += 1
        else:
            self._consec_identical = 0
            self._last_line = text[:2048]
        if not text.startswith("CSI_DATA"):
            self._non_csi += 1
            self._record_raw(line)
            return
        try:
            sample = self._adapter.handle_line(text, time.time(),
                                               ts_host_ns=rx_ns)
        except PacketError as exc:
            self._malformed += 1
            self._malformed_recent.append(f"{str(exc)[:120]} :: "
                                          f"{text[:120]}")
            self._record_raw(line)
            return
        if sample is None:  # pragma: no cover (adapter guards this)
            return
        self._valid += 1
        now = time.monotonic()
        self._arrivals.append(now)
        self._last_valid_ts = time.time()
        self._last_sample = sample
        self._rssi.append(sample.rssi)
        self._channels[sample.channel] = self._channels.get(
            sample.channel, 0) + 1
        mac = str(sample.mac).lower()
        self._bssids[mac] = self._bssids.get(mac, 0) + 1
        if self._last_seq is None:
            self._last_seq = sample.seq
        elif sample.seq > self._last_seq + 1:
            self._gaps += 1
            if len(self._missing) < 32:
                self._missing.extend(
                    range(self._last_seq + 1, sample.seq))
            self._last_seq = sample.seq
        elif sample.seq == self._last_seq + 1:
            # Normal in-order arrival: just advance the anchor.
            self._last_seq = sample.seq
        elif sample.seq == self._last_seq:
            # Exact repeat of the previous sequence: duplicate delivery
            # (counted, never silently absorbed).
            self._duplicates += 1
        else:
            # Older than the previous sequence: out-of-order delivery.
            # _last_seq is NOT moved backwards so gap detection stays
            # anchored to the newest sequence seen.
            self._out_of_order += 1
        self._record_raw(line)
        self._note_bytes()
        self._maybe_settle()
        self._maybe_evaluate_gate()
        # Late-breaking integrity failures demote a passed gate: a NEW
        # storm epoch or impossible throughput while VERIFIED means the
        # session is not verified, whenever it appears.
        if self._gate_passed and (self._storm_epochs > self._settle_epochs
                                  or self._tp_now()):
            cause = ("duplication-storm inside verified session"
                     if self._storm_epochs > self._settle_epochs
                     else "impossible serial throughput in verified session")
            self._gate_passed = False
            self._gate_reasons = [f"{cause} — demoted to UNVERIFIED"]

    def _note_bytes(self) -> None:
        """Sample transport byte counts for windowed throughput checks."""
        if self._source is None:
            return
        self._byte_marks.append(
            (time.monotonic(), getattr(self._source, "bytes_read", 0)))

    def _tp_now(self) -> bool:
        """True when the trailing ~3 s byte rate exceeds the baud cap."""
        marks = self._byte_marks
        while len(marks) > 2 and marks[0][0] < marks[-1][0] - 3.0:
            marks.popleft()
        if len(marks) < 2:
            return False
        span = marks[-1][0] - marks[0][0]
        if span < 0.5:
            return False
        if (marks[-1][1] - marks[0][1]) / span > (self.baud / 10.0) * 1.05:
            self._tp_ever = True
            return True
        return False

    # -- session gate ------------------------------------------------------
    def _rate_hz(self) -> Optional[float]:
        if len(self._arrivals) < 2:
            return None
        span = self._arrivals[-1] - self._arrivals[0]
        if span <= 0:
            return None
        return len(self._arrivals) / span

    def _maybe_settle(self) -> None:
        """Automated open-transient SOP (RFVISION-003R-C2 phenomenology).

        Fresh opens intermittently replay duplicated tail bursts
        (host/bridge side, NOT firmware data). The validation window
        starts only after ``settle_s`` of CURRENTLY clean streaming
        (valid records flowing, no active repeat run, physically
        possible trailing throughput). Pre-settle storms stay recorded
        in stats — never hidden — but do not poison the window. A storm
        epoch that starts AFTER settle demotes the session.
        """
        if self._settle_ok:
            return
        if (self._consec_identical >= self.STORM_REPEAT_LINES
                or self._tp_now()):
            self._pre_gate_storm = True
            self._settle_start = None
            return
        if self._valid == 0:
            return
        now = time.time()
        if self._settle_start is None:
            self._settle_start = now
        if now - self._settle_start >= self.settle_s:
            self._settle_ok = True
            self._gate_t0 = now
            self._settle_epochs = self._storm_epochs
            self._arrivals.clear()  # rate is measured on clean air only

    def _maybe_evaluate_gate(self) -> None:
        if self._gate_evaluated or self._gate_t0 is None:
            return
        if time.time() - self._gate_t0 < self.gate_window_s:
            return
        if len(self._arrivals) < 2:
            return  # rate unmeasurable yet: defer, do not fail
        self._gate_evaluated = True
        reasons: List[str] = []
        rate = self._rate_hz()
        if self._valid == 0:
            reasons.append("no valid CSI_DATA in gate window")
        if rate is None:
            reasons.append("record rate unmeasurable in gate window")
        elif not (self.GATE_MIN_RATE_HZ <= rate <= self.GATE_MAX_RATE_HZ):
            reasons.append(f"implausible record rate {rate:.1f} Hz")
        if set(self._channels) != {self.expected_channel}:
            reasons.append(f"channel not consistent: "
                           f"{sorted(self._channels)}")
        if set(self._bssids) != {self.expected_bssid}:
            reasons.append(f"BSSID not as expected: "
                           f"{sorted(self._bssids)}")
        if self._tp_now():
            reasons.append("impossible serial throughput for baud rate")
        if self._storm_epochs > self._settle_epochs:
            reasons.append("duplication-storm inside validation window")
        if self._last_valid_ts is None or (
                time.time() - self._last_valid_ts) > self.stale_after_s:
            reasons.append("no fresh data at gate close")
        if reasons:
            self._gate_reasons = reasons
        else:
            self._gate_passed = True
            self._gate_reasons = ["all session-gate checks passed"]

    # -- recording (lossless, explicit only) ---------------------------------
    def start_recording(self, path: str | Path,
                        max_seconds: float = REC_MAX_SECONDS) -> str:
        """Arm lossless raw-line recording (every line, as received)."""
        if self._rec_fp is not None:
            raise LiveSerialError("recording already active")
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        self._rec_fp = open(target, "w", encoding="ascii",
                            errors="replace")
        self._rec_path = str(target)
        self._rec_bytes = 0
        self._rec_start = time.time()
        self._rec_max_s = min(float(max_seconds), self.REC_MAX_SECONDS)
        self._rec_sha = None
        return self._rec_path

    def _record_raw(self, line: str) -> None:
        if self._rec_fp is None:
            return
        if (self._rec_start is not None and
                time.time() - self._rec_start > self._rec_max_s):
            self._stop_recording()  # bounded by design, never unbounded
            return
        text = line if line.endswith("\n") else line + "\n"
        self._rec_fp.write(text)
        self._rec_bytes += len(text.encode("ascii", errors="replace"))

    def _stop_recording(self) -> Optional[Dict[str, Any]]:
        fp, self._rec_fp = self._rec_fp, None
        if fp is None:
            return None
        try:
            fp.close()
        except OSError:
            pass
        info = {"path": self._rec_path, "bytes": self._rec_bytes,
                "sha256": None}
        if self._rec_path:
            digest = hashlib.sha256()
            try:
                with open(self._rec_path, "rb") as fh:
                    for chunk in iter(lambda: fh.read(65536), b""):
                        digest.update(chunk)
                info["sha256"] = digest.hexdigest()
            except OSError:
                info["sha256"] = None
        self._rec_sha = info["sha256"]
        self._rec_start = None
        self._rec_last_info = info
        return info

    def stop_recording(self) -> Optional[Dict[str, Any]]:
        """Stop recording, checksum the file, report the manifest.

        Returns the last manifest even if the session already ended
        (bounded auto-stop), so the checksum is never lost.
        """
        return self._stop_recording() or self._rec_last_info

    # -- frames ------------------------------------------------------------
    def frames(self) -> Iterator[Dict[str, Any]]:
        """Live session: ingest every line, yield latest-frame envelopes.

        Envelopes are decimated to ~``frame_hz`` so visualization can
        never back-pressure capture; counting + recording stay lossless.
        Presence/activity/position stay UNKNOWN/unvalidated — this
        provider reports transport + signal, never sensing conclusions.
        """
        try:
            source = self._begin_session()
        except LiveSerialError:
            return
        try:
            for line in source.iter_lines():
                if self._stop:
                    break
                self._ingest(
                    line,
                    getattr(source, "last_line_rx_ns", None))
                event = self._maybe_frame()
                if event is not None:
                    yield event
        except LiveSerialError as exc:
            self._transport_error = str(exc)
        finally:
            self._stop_recording()
            try:
                source.close()
            except Exception:
                pass
            self._source = None

    def _maybe_frame(self) -> Optional[Dict[str, Any]]:
        sample = self._last_sample
        if sample is None:
            return None
        now = time.time()
        if now - self._last_yield_ts < 1.0 / self.frame_hz:
            return None
        self._last_yield_ts = now
        try:
            amps = [float(v) for v in amplitude(sample)]
        except (PacketError, ValueError):
            return None
        payload = contracts.sensing_snapshot_payload(
            presence="UNKNOWN", presence_prob=None,
            movement="UNKNOWN", movement_prob=None,
            position=None, position_m=None, confidence=None,
            rssi=float(sample.rssi), amplitudes=amps, phases=None,
            validated=False)
        payload["source_state"] = self.source_state
        event = contracts.wrap_event("sensing.snapshot", payload,
                                     source="rfvision-web(live)",
                                     seq=int(sample.seq))
        self._latest = event
        return event

    def latest_snapshot(self) -> Optional[Dict[str, Any]]:
        """Most recent live envelope (or None before first frame)."""
        return self._latest

    # -- telemetry -----------------------------------------------------------
    def live_stats(self) -> Dict[str, Any]:
        """Full live-session telemetry (§5); unknown stays None."""
        now = time.time()
        rate = self._rate_hz()
        total = self._valid + self._malformed
        valid_pct = (100.0 * self._valid / total) if total else None
        rssi_list = list(self._rssi)
        rssi_mean = (sum(rssi_list) / len(rssi_list)) if rssi_list else None
        trend: Optional[str] = None
        if len(rssi_list) >= 20:
            recent = sum(rssi_list[-10:]) / 10.0
            older = sum(rssi_list[-20:-10]) / 10.0
            trend = ("rising" if recent - older > 1.0
                     else "falling" if older - recent > 1.0 else "stable")
        amp_stats: Dict[str, Optional[float]] = {
            "min": None, "max": None, "mean": None, "std": None}
        tones: Optional[int] = None
        csi_len: Optional[int] = None
        iq_finite: Optional[bool] = None
        if self._last_sample is not None:
            try:
                vec = amplitude(self._last_sample)
                import math as _math
                vals = [float(v) for v in vec]
                tones = len(vals)
                csi_len = int(len(self._last_sample.csi))
                iq_finite = all(_math.isfinite(v) for v in vals)
                if vals:
                    mean = sum(vals) / len(vals)
                    amp_stats = {
                        "min": min(vals), "max": max(vals), "mean": mean,
                        "std": float((sum((v - mean) ** 2 for v in vals)
                                      / len(vals)) ** 0.5)}
            except (PacketError, ValueError):
                pass
        src = self._source
        elapsed = (now - self._session_start) if self._session_start else None
        byte_rate: Optional[float] = None
        if src is not None and elapsed and elapsed > 0:
            byte_rate = ((getattr(src, "bytes_read", 0) - self._bytes_start)
                         / elapsed)
        age = (now - self._last_valid_ts) if self._last_valid_ts else None
        # Gate reasons stay current: anomalies that trip after the
        # evaluation instant are appended so the report never hides them.
        gate_reasons = list(self._gate_reasons)
        if not self._gate_passed:
            if self._storm and not any("storm" in r for r in gate_reasons):
                gate_reasons.append("duplication-storm signature in session")
            if (self._tp_ever
                    and not any("throughput" in r for r in gate_reasons)):
                gate_reasons.append(
                    "impossible serial throughput in session")
        return {
            "available": True,
            "session_id": self._session_id,
            "board_mac": self.board_mac,
            "port": self.port,
            "baud": self.baud,
            "expected_bssid": self.expected_bssid,
            "expected_channel": self.expected_channel,
            "source_state": self.source_state,
            "gate": {"passed": self._gate_passed,
                     "reasons": gate_reasons,
                     "window_s": self.gate_window_s,
                     "settled": self._settle_ok,
                     "settle_s": self.settle_s,
                     "pre_gate_storm": self._pre_gate_storm},
            "transport": {
                "open": bool(src is not None and getattr(
                    src, "is_open", False)),
                "bytes_read": (getattr(src, "bytes_read", 0)
                               if src is not None else 0),
                "bytes_per_s": byte_rate,
                "overlong_dropped": (getattr(src, "overlong_dropped", 0)
                                     if src is not None else 0),
                "error": self._transport_error},
            "stream": {
                "valid": self._valid,
                "malformed": self._malformed,
                "non_csi_lines": self._non_csi,
                "valid_pct": valid_pct,
                "rate_hz": rate,
                "last_seq": self._last_seq,
                "gaps": self._gaps,
                "missing": list(self._missing[:32]),
                "duplicates": self._duplicates,
                "out_of_order": self._out_of_order,
                "last_update_age_s": age,
                "stale": (age is not None and age > self.stale_after_s),
                "session_s": elapsed},
            "signal": {
                "rssi_last": rssi_list[-1] if rssi_list else None,
                "rssi_mean": rssi_mean,
                "rssi_trend": trend,
                "channel": (max(self._channels, key=self._channels.get)
                            if self._channels else None),
                "channels_seen": sorted(self._channels),
                "bssid": (max(self._bssids, key=self._bssids.get)
                          if self._bssids else None),
                "bssids_seen": sorted(self._bssids),
                "csi_len": csi_len,
                "tones": tones,
                "amplitude": amp_stats,
                "iq_finite": iq_finite},
            "parser": {
                "lines_seen": self._adapter.stats.lines_seen,
                "parsed": self._adapter.stats.parsed,
                "rejected": dict(
                    self._adapter.stats.rejection_reasons),
                "recent_malformed": list(self._malformed_recent)},
            "duplication": {
                "consecutive_identical": self._consec_identical,
                "storm": self._storm,
                "storm_epochs": self._storm_epochs,
                "impossible_throughput": self._tp_ever},
            "recording": {
                "active": self._rec_fp is not None,
                "path": self._rec_path,
                "bytes": self._rec_bytes,
                "sha256": self._rec_sha},
        }


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
        return LiveProvider(
            port=str(kwargs.get("port", DEFAULT_PORT)),
            baud=int(kwargs.get("baud", DEFAULT_BAUD)),
            expected_bssid=str(kwargs.get(
                "expected_bssid", "8c:53:c3:5b:e1:59")),
            expected_channel=int(kwargs.get("expected_channel", 1)),
            line_source=kwargs.get("line_source", None))
    raise contracts.ContractError(f"unknown source mode: {mode!r}")
