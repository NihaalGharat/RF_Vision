"""Pure per-node reference-relative CSI amplitude diagnostics.

This module measures how far a node's current valid-tone amplitude vector is
from an explicitly captured reference from that same node. It never infers
presence, movement, activity, or location, and it is not connected to the
existing inference, fusion, state, API, or frontend paths.

Reference calculation
---------------------
For each tone, finite positive reference amplitudes give a robust linear
``center`` (median) and a robust log-domain ``scale``::

    scale = 1.4826 * MAD(log(amplitude / center))

The optional scale floor only prevents division by zero for a perfectly
constant tone. Tones with fewer than ``min_samples`` usable reference samples
are not usable in later diagnostics.

Gain calculation
----------------
For a current vector, the scalar multiplicative gain offset is::

    gain = exp(median(log(current / center)))

computed over tones that are usable in the reference and finite positive in
the current vector. The structural residual is::

    residual = log(current / center) - log(gain)

so a common amplitude/gain shift changes ``gain`` without inflating structural
disturbance. The absolute gain is retained and is not normalized across nodes.

Diagnostic time is supplied by the caller as an actual timestamp or monotonic
clock value. No seconds are derived from the nominal sample rate.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Optional, Sequence

import numpy as np

__all__ = [
    "ReferenceState",
    "ReferenceConfig",
    "ReferenceProfile",
    "ReferenceDiagnostics",
    "ReferenceTracker",
]

_MAD_TO_SIGMA = 1.4826


class ReferenceState:
    """Reference diagnostic states (plain strings, matching project labels)."""

    ABSENT = "ABSENT"
    IMMATURE = "IMMATURE"
    VALID = "VALID"
    STALE = "STALE"
    INVALID = "INVALID"


@dataclass(frozen=True)
class ReferenceConfig:
    """Quality/age settings for a per-node explicit reference."""

    min_samples: int = 16
    min_valid_fraction: float = 0.5
    stale_after_s: float = 300.0
    disturbance_z: float = 3.0
    scale_floor: float = 1e-6

    def __post_init__(self) -> None:
        if self.min_samples < 1:
            raise ValueError("min_samples must be >= 1")
        if not 0.0 < self.min_valid_fraction <= 1.0:
            raise ValueError("min_valid_fraction must be in (0, 1]")
        if self.stale_after_s < 0.0:
            raise ValueError("stale_after_s must be >= 0")
        if self.disturbance_z <= 0.0:
            raise ValueError("disturbance_z must be > 0")
        if self.scale_floor <= 0.0:
            raise ValueError("scale_floor must be > 0")


@dataclass(frozen=True)
class ReferenceProfile:
    """Immutable robust per-tone reference statistics for one node."""

    center: np.ndarray
    scale: np.ndarray
    tone_counts: np.ndarray
    usable_tones: np.ndarray
    sample_count: int
    captured_at: float

    @property
    def n_tones(self) -> int:
        return int(len(self.center))

    @property
    def usable_tone_count(self) -> int:
        return int(np.count_nonzero(self.usable_tones))


@dataclass(frozen=True)
class ReferenceDiagnostics:
    """Reference-relative measurements, never a sensing classification."""

    state: str
    relative_amplitude: Optional[np.ndarray]
    disturbance_energy: Optional[float]
    disturbed_tone_fraction: Optional[float]
    gain_offset: Optional[float]
    reference_sample_count: int
    reference_age_s: Optional[float]
    compared_tones: int
    coverage: Optional[float]
    reason: Optional[str] = None


def _finite_time(value: object) -> Optional[float]:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result if math.isfinite(result) else None


def _neutral(state: str, profile: Optional[ReferenceProfile],
             age: Optional[float], reason: str, *,
             compared_tones: int = 0,
             coverage: Optional[float] = None) -> ReferenceDiagnostics:
    return ReferenceDiagnostics(
        state=state,
        relative_amplitude=None,
        disturbance_energy=None,
        disturbed_tone_fraction=None,
        gain_offset=None,
        reference_sample_count=(profile.sample_count if profile else 0),
        reference_age_s=age,
        compared_tones=int(compared_tones),
        coverage=coverage,
        reason=reason,
    )


class ReferenceTracker:
    """Explicit capture plus separate evaluation for one node's amplitudes."""

    def __init__(self, config: Optional[ReferenceConfig] = None) -> None:
        self.config = config or ReferenceConfig()
        self._profile: Optional[ReferenceProfile] = None

    @property
    def profile(self) -> Optional[ReferenceProfile]:
        return self._profile

    def reset(self) -> None:
        """Remove the stored reference; the next state is ``ABSENT``."""
        self._profile = None

    def capture(self, samples: Sequence[object], *,
                now: float) -> Optional[ReferenceProfile]:
        """Explicitly build a reference from supplied amplitude vectors.

        Incompatible, non-finite, and non-positive values are excluded per
        tone. The stored profile is replaced only when at least one usable
        vector is supplied. Calling :meth:`evaluate` never captures samples.
        """
        captured_at = _finite_time(now)
        if captured_at is None:
            return None

        vectors = []
        shape = None
        for sample in samples:
            try:
                vector = np.asarray(sample, dtype=np.float64)
            except (TypeError, ValueError):
                continue
            if vector.ndim != 1 or vector.size == 0:
                continue
            if shape is None:
                shape = vector.shape
            if vector.shape != shape:
                continue
            vectors.append(vector)

        if not vectors:
            return None

        matrix = np.vstack(vectors)
        finite_positive = np.isfinite(matrix) & (matrix > 0.0)
        sample_count = int(np.count_nonzero(
            np.any(finite_positive, axis=1)))
        if sample_count == 0:
            return None

        n_tones = int(matrix.shape[1])
        center = np.full(n_tones, np.nan, dtype=np.float64)
        scale = np.full(n_tones, np.nan, dtype=np.float64)
        tone_counts = np.count_nonzero(finite_positive, axis=0).astype(int)
        usable = np.zeros(n_tones, dtype=bool)

        for index in range(n_tones):
            values = matrix[finite_positive[:, index], index]
            if values.size == 0:
                continue
            median = float(np.median(values))
            center[index] = median
            log_ratio = np.log(values / median)
            mad = float(np.median(np.abs(
                log_ratio - np.median(log_ratio))))
            scale[index] = max(_MAD_TO_SIGMA * mad,
                               self.config.scale_floor)
            usable[index] = tone_counts[index] >= self.config.min_samples

        center.setflags(write=False)
        scale.setflags(write=False)
        tone_counts.setflags(write=False)
        usable.setflags(write=False)
        profile = ReferenceProfile(
            center=center,
            scale=scale,
            tone_counts=tone_counts,
            usable_tones=usable,
            sample_count=sample_count,
            captured_at=captured_at,
        )
        self._profile = profile
        return profile

    def _state_at(self, now: Optional[float]):
        profile = self._profile
        if profile is None:
            return ReferenceState.ABSENT, None, "no explicit reference"

        if now is None:
            return ReferenceState.INVALID, None, "timestamp is not finite"

        age = now - profile.captured_at
        if age < 0.0:
            return (ReferenceState.INVALID, age,
                    "timestamp precedes reference capture")

        if profile.sample_count < self.config.min_samples:
            return (ReferenceState.IMMATURE, age,
                    f"reference has {profile.sample_count}/"
                    f"{self.config.min_samples} required samples")

        if profile.usable_tone_count == 0 or (
                profile.usable_tone_count / profile.n_tones
                < self.config.min_valid_fraction):
            return (ReferenceState.INVALID, age,
                    f"reference has {profile.usable_tone_count}/"
                    f"{profile.n_tones} usable tones")

        if age > self.config.stale_after_s:
            return (ReferenceState.STALE, age,
                    f"reference age {age:.3f}s exceeds "
                    f"{self.config.stale_after_s:.3f}s")

        return ReferenceState.VALID, age, None

    def state(self, *, now: float) -> str:
        """Current reference state without evaluating a live vector."""
        state, _age, _reason = self._state_at(_finite_time(now))
        return state

    def evaluate(self, amplitudes: object, *,
                 now: float) -> ReferenceDiagnostics:
        """Measure one vector against the stored reference.

        Missing tones are represented by NaN/Inf/zero entries or by exclusion
        from the compared set. Insufficient coverage or an incompatible shape
        returns an explicit neutral ``INVALID`` result. A stale but otherwise
        usable reference still yields diagnostics while reporting ``STALE``.
        """
        profile = self._profile
        now_value = _finite_time(now)
        state, age, reason = self._state_at(now_value)

        if profile is None:
            return _neutral(state, profile, age, reason or "no reference")

        if state in (ReferenceState.IMMATURE, ReferenceState.INVALID):
            return _neutral(state, profile, age, reason or "reference invalid")

        try:
            current = np.asarray(amplitudes, dtype=np.float64)
        except (TypeError, ValueError):
            return _neutral(ReferenceState.INVALID, profile, age,
                            "current amplitude vector is not numeric")

        if current.ndim != 1 or current.size != profile.n_tones:
            return _neutral(
                ReferenceState.INVALID, profile, age,
                f"current vector has {current.size} tones; reference has "
                f"{profile.n_tones}")

        valid = np.isfinite(current) & (current > 0.0)
        compared_mask = profile.usable_tones & valid
        compared_tones = int(np.count_nonzero(compared_mask))
        usable_count = profile.usable_tone_count
        coverage = (compared_tones / usable_count) if usable_count else 0.0

        if usable_count == 0 or coverage < self.config.min_valid_fraction:
            return _neutral(
                ReferenceState.INVALID, profile, age,
                f"only {compared_tones}/{usable_count} usable reference "
                "tones are comparable",
                compared_tones=compared_tones, coverage=coverage)

        center = profile.center[compared_mask]
        scale = profile.scale[compared_mask]
        values = current[compared_mask]

        log_ratio = np.log(values / center)
        log_gain = float(np.median(log_ratio))
        gain = float(math.exp(log_gain))
        residual = log_ratio - log_gain
        normalized = residual / scale

        energy = float(np.mean(normalized ** 2))
        disturbed_fraction = float(np.mean(
            np.abs(normalized) > self.config.disturbance_z))

        relative = np.full(profile.n_tones, np.nan, dtype=np.float64)
        relative[compared_mask] = values / center

        if not np.isfinite(
                [gain, energy, disturbed_fraction]).all():
            return _neutral(
                ReferenceState.INVALID, profile, age,
                "reference diagnostic produced a non-finite value",
                compared_tones=compared_tones, coverage=coverage)

        return ReferenceDiagnostics(
            state=state,
            relative_amplitude=relative,
            disturbance_energy=energy,
            disturbed_tone_fraction=disturbed_fraction,
            gain_offset=gain,
            reference_sample_count=profile.sample_count,
            reference_age_s=age,
            compared_tones=compared_tones,
            coverage=coverage,
            reason=reason,
        )
