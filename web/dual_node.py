"""Concurrent two-node CSI acquisition coordinator (sensing foundation).

Host-side temporal alignment, NOT hardware synchronization: the two ESP32
clocks are never disciplined to each other. Each node gets its own
:class:`LiveProvider` (single-node semantics preserved) plus a
:class:`ClockOffsetEstimator` mapping that node's firmware clock to the
common host monotonic clock. A session reports ``SYNCED`` only when BOTH
mappings satisfy the documented stability criterion — which means "both
device clocks are stably mapped to host time", never "the ESP32s are
synchronized".

SYNCED criterion (documented, tunable via constructor):
  * each node has >= ``sync_min_n`` offset observations, AND
  * each node's offset jitter (MAD) <= ``sync_max_jitter_ns``.
States: UNSYNCED (a node has too few observations) → SYNCING (collecting
but unstable) → SYNCED (criterion met). Insufficient quality stays visible.

Timing honesty (Phase 6): ESP→host physical latency is NOT measurable
without a common clock, so it is reported as ``None`` with the reason —
never ``host_time - ESP_time``. What IS measured per sample is the
host-side pipeline delay (ingress → parsed sample), reported as
``host_pipeline_us`` with mean/max statistics.
"""

from __future__ import annotations

import queue
import threading
import time
from typing import Any, Dict, Iterator, List, Optional, Tuple

from csi.transport.nodes import (
    NODES,
    NodeIdentity,
    all_nodes_resolved,
)
from localization.synchronization.sync import ClockOffsetEstimator
from web import source as sources
from web.live_serial import SerialLineSource

__all__ = [
    "SYNC_MIN_N",
    "SYNC_MAX_JITTER_NS",
    "NodeProvider",
    "DualNodeSession",
]

#: Default SYNCED criterion: >= 64 offset observations per node with offset
#: jitter (MAD) <= 2 ms. Initial defaults from host-scheduling reasoning
#: (serial ingress jitter is ~sub-ms to few ms); subject to revision once
#: measured on real dual captures. Tunable per session.
SYNC_MIN_N = 64
SYNC_MAX_JITTER_NS = 2_000_000

SYNC_STATES = ("UNSYNCED", "SYNCING", "SYNCED")


class NodeProvider(sources.LiveProvider):
    """One node's live path: ``LiveProvider`` + sync + pipeline accounting.

    Adds NOTHING to the parse/gate path (inherited untouched): after each
    ingested line it feeds new valid samples to the node's offset
    estimator and records the host pipeline delay. ``node_id`` tags every
    snapshot this provider yields.
    """

    mode = "live"

    def __init__(self, node: NodeIdentity, port: str, **kwargs: Any) -> None:
        super().__init__(port=port, board_mac=node.board_mac, **kwargs)
        self.node = node
        self.sync = ClockOffsetEstimator()
        self._fed_sample_id: Optional[int] = None
        self._pipeline_us: List[float] = []
        self._pipeline_max = 200
        self._acq_latency_note = (
            "esp_to_host latency is not measurable without a common clock; "
            "host_time - ESP_time is NOT reported as latency. "
            "host_pipeline_us (ingress to parsed sample) is measured.")

    # -- ingest hook -----------------------------------------------------
    def _ingest(self, line: str,
                rx_ns: Optional[int] = None) -> None:
        super()._ingest(line, rx_ns)
        sample = self._last_sample
        if sample is None or id(sample) == self._fed_sample_id:
            return
        self._fed_sample_id = id(sample)
        if rx_ns is not None:
            self._pipeline_us.append((time.monotonic_ns() - rx_ns) / 1000.0)
            if len(self._pipeline_us) > self._pipeline_max:
                del self._pipeline_us[:len(self._pipeline_us)
                                       - self._pipeline_max]
        if sample.ts_host_ns is not None:
            # Common unit: nanoseconds (firmware us -> ns).
            self.sync.observe(float(sample.ts_esp32_us) * 1000.0,
                              float(sample.ts_host_ns))

    # -- node telemetry ----------------------------------------------------
    def node_stats(self) -> Dict[str, Any]:
        """Single-node stats + sync + honest timing block."""
        base = self.live_stats()
        pipe = list(self._pipeline_us)
        base["node_id"] = self.node.node_id
        base["sync"] = {
            "offset_ns": self.sync.offset,
            "jitter_ns": self.sync.jitter,
            "drift_per_sample_ns": self.sync.drift_per_sample,
            "observations": self.sync.n,
            "ready": self.sync.stable(SYNC_MAX_JITTER_NS, SYNC_MIN_N),
        }
        base["timing"] = {
            # NOT physical latency — see module docstring + note.
            "esp_to_host_latency_us": None,
            "latency_note": self._acq_latency_note,
            "host_pipeline_us_mean": (
                sum(pipe) / len(pipe) if pipe else None),
            "host_pipeline_us_max": (max(pipe) if pipe else None),
            "host_pipeline_samples": len(pipe),
        }
        return base


class DualNodeSession:
    """Concurrent two-node capture with deterministic fan-in.

    Each node pumps in its own daemon thread into one shared FIFO queue;
    readers see ``(node_id, event)`` in arrival order. No shared mutable
    provider state — providers are independent, the queue is thread-safe —
    so behaviour never depends on thread scheduling beyond arrival order.
    Single-node operation is untouched (use ``LiveProvider`` directly).
    """

    def __init__(self, node_ids: Tuple[str, ...] = ("esp32-a", "esp32-b"),
                 expected_bssid: str = "8c:53:c3:5b:e1:59",
                 expected_channel: int = 1,
                 line_source_factory: Any = None,
                 sync_min_n: int = SYNC_MIN_N,
                 sync_max_jitter_ns: int = SYNC_MAX_JITTER_NS,
                 **provider_kwargs: Any) -> None:
        unknown = [n for n in node_ids if n not in NODES]
        if unknown:
            raise ValueError(f"unknown node ids: {unknown}")
        self.node_ids = tuple(node_ids)
        self.expected_bssid = expected_bssid
        self.expected_channel = expected_channel
        self._factory = line_source_factory
        self.sync_min_n = int(sync_min_n)
        self.sync_max_jitter_ns = int(sync_max_jitter_ns)
        self._provider_kwargs = provider_kwargs
        self.providers: Dict[str, NodeProvider] = {}
        self._queue: "queue.Queue[Tuple[str, Dict[str, Any]]]" = queue.Queue()
        self._threads: List[threading.Thread] = []
        self._stop = threading.Event()
        self._started_at: Optional[float] = None

    # -- lifecycle ---------------------------------------------------------
    def start(self) -> Dict[str, str]:
        """Resolve devices (fail fast if any board missing) + start pumps."""
        devices = all_nodes_resolved()
        for nid in self.node_ids:
            if nid not in devices:
                raise ValueError(f"node {nid} has no resolved device")
        self._stop.clear()
        self._started_at = time.time()
        for nid in self.node_ids:
            node = NODES[nid]
            source = (self._factory(nid) if self._factory is not None
                      else SerialLineSource(port=devices[nid], baud=921600))
            provider = NodeProvider(
                node, port=devices[nid],
                expected_bssid=self.expected_bssid,
                expected_channel=self.expected_channel,
                line_source=source, **self._provider_kwargs)
            self.providers[nid] = provider
            thread = threading.Thread(
                target=self._pump, args=(nid, provider),
                daemon=True, name=f"dual-pump-{nid}")
            self._threads.append(thread)
            thread.start()
        return {nid: devices[nid] for nid in self.node_ids}

    def _pump(self, node_id: str, provider: NodeProvider) -> None:
        try:
            for event in provider.frames():
                if self._stop.is_set():
                    break
                event = dict(event)
                event["node_id"] = node_id
                self._queue.put((node_id, event))
        finally:
            provider.close()

    def stop(self) -> None:
        """Stop all pumps + release ports (idempotent)."""
        self._stop.set()
        for provider in self.providers.values():
            try:
                provider.close()
            except Exception:
                pass
        for thread in self._threads:
            thread.join(timeout=5.0)
        self._threads = []

    def frames(self, timeout: float = 1.0) -> Iterator[Tuple[str, Dict]]:
        """Yield ``(node_id, event)`` in arrival order until stopped."""
        while not self._stop.is_set():
            try:
                yield self._queue.get(timeout=timeout)
            except queue.Empty:
                continue

    # -- session telemetry ---------------------------------------------------
    def sync_state(self) -> Dict[str, Any]:
        """Session sync state from per-node estimator readiness."""
        nodes: Dict[str, Any] = {}
        for nid, provider in self.providers.items():
            est = provider.sync
            ready = est.stable(self.sync_max_jitter_ns, self.sync_min_n)
            nodes[nid] = {
                "observations": est.n,
                "offset_ns": est.offset,
                "jitter_ns": est.jitter,
                "drift_per_sample_ns": est.drift_per_sample,
                "ready": ready,
            }
        if not nodes:
            state = "UNSYNCED"
        elif any(n["observations"] < self.sync_min_n for n in nodes.values()):
            state = "UNSYNCED"
        elif all(n["ready"] for n in nodes.values()):
            state = "SYNCED"
        else:
            state = "SYNCING"
        return {
            "state": state,
            "criterion": (f"SYNCED iff every node has >= {self.sync_min_n} "
                          f"observations AND jitter <= "
                          f"{self.sync_max_jitter_ns} ns; SYNCED means both "
                          f"device clocks are stably mapped to host time, "
                          f"NOT that the ESP32 clocks are synchronized."),
            "nodes": nodes,
        }

    def session_stats(self) -> Dict[str, Any]:
        """Full dual-session telemetry: per-node stats + sync state."""
        return {
            "nodes": self.node_ids,
            "started_at": self._started_at,
            "elapsed_s": ((time.time() - self._started_at)
                          if self._started_at else None),
            "per_node": {nid: p.node_stats()
                         for nid, p in self.providers.items()},
            "sync": self.sync_state(),
        }
