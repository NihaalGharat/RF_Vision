"""Focused regression for bounded-recording finalization ordering.

The trial watcher and the acquisition pump share a LiveProvider. A bounded
recording can auto-stop on the pump thread at the same time the trial finalizes
on the watcher thread. The finalized manifest must never be published as
bytes=0/sha256=null while a nonempty raw file is being closed/checksummed.
"""

from __future__ import annotations

import hashlib
import threading
import time
from unittest import mock

from web import source as sources
from web.live_serial import FakeLineSource


class SlowHash:
    def __init__(self, real, block: bool, entered, release) -> None:
        self.real = real
        self.block = block
        self.entered = entered
        self.release = release

    def update(self, data) -> None:
        self.real.update(data)

    def hexdigest(self) -> str:
        if self.block:
            self.entered.set()
            self.release.wait(timeout=2.0)
        return self.real.hexdigest()

    def digest(self) -> bytes:
        return self.real.digest()


def test_stop_during_auto_stop_returns_completed_manifest(tmp_path):
    provider = sources.LiveProvider(line_source=FakeLineSource([]))
    target = tmp_path / "race.bin"
    provider.start_recording(target, max_seconds=30)
    provider._record_raw("synthetic-line\n")
    provider._rec_start -= 31.0  # next pump write crosses the bound

    entered = threading.Event()
    release = threading.Event()
    real_sha = hashlib.sha256
    first = True

    def slow_sha(*args, **kwargs):
        nonlocal first
        block = first
        first = False
        return SlowHash(real_sha(*args, **kwargs), block, entered, release)

    result = {}
    stopper_started = threading.Event()

    def stop():
        stopper_started.set()
        result["info"] = provider.stop_recording()

    try:
        with mock.patch.object(sources.hashlib, "sha256", slow_sha):
            auto = threading.Thread(
                target=provider._record_raw, args=("late-line\n",))
            auto.start()
            assert entered.wait(1.0), "auto-stop did not reach checksum"

            stopper = threading.Thread(target=stop)
            stopper.start()
            assert stopper_started.wait(1.0)
            time.sleep(0.05)
            assert stopper.is_alive(), (
                "stop_recording returned before auto-stop published its manifest")

            release.set()
            auto.join(1.0)
            stopper.join(1.0)
    finally:
        release.set()

    assert not auto.is_alive()
    assert not stopper.is_alive()
    info = result["info"]
    assert info is not None
    raw = target.read_bytes()
    assert raw
    assert info["bytes"] == len(raw)
    assert info["sha256"] == hashlib.sha256(raw).hexdigest()
    assert provider.stop_recording()["sha256"] == info["sha256"]
