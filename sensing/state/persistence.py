"""Showcase presence-state machine with short persistence/fade (P1).

Maps the EXISTING deterministic outputs (presence/movement labels from
``sensing/presence``, ``sensing/motion``, ``sensing/activity``) onto the
six P1 product states::

    ABSENT / DETECTED / MOVING / STATIONARY / LOW_CONFIDENCE / EXITING

plus short persistence: when strong evidence disappears the last-known
representation persists briefly (EXITING with a fading confidence) and
then transitions to ABSENT.

Binding constraints:

* Detection mathematics are NEVER re-decided here. The 0.5 presence /
  movement thresholds live in their owner modules; this machine only
  routes their labels to display states.
* ``LOW_CONFIDENCE_BAND`` is a PRESENTATION band on the explicitly
  uncalibrated product score — it selects which honesty label to show,
  never whether a human is present. Documented, not scientific.
* ``HOLD_S`` / ``FADE_S`` are presentation timings (how long the UI
  holds/fades the last-known figure), not detection parameters.

Stdlib only. Clock-injectable for deterministic tests.
"""

from __future__ import annotations

import time
from typing import Callable, Optional, Tuple

__all__ = [
    "PRESENCE_STATES",
    "LOW_CONFIDENCE_BAND",
    "HOLD_S",
    "FADE_S",
    "PresencePersistence",
]

#: The six P1 product states (plus UNKNOWN = no inference attached yet).
PRESENCE_STATES = (
    "ABSENT",
    "DETECTED",
    "MOVING",
    "STATIONARY",
    "LOW_CONFIDENCE",
    "EXITING",
    "UNKNOWN",
)

#: Uncalibrated-score presentation band: PERSON evidence scoring below
#: this renders LOW_CONFIDENCE instead of a named state. Presentation
#: only — see module docstring.
LOW_CONFIDENCE_BAND = 0.35

#: How long EXITING holds the last-known representation (seconds).
HOLD_S = 2.0

#: How long the shown confidence fades from its last strong value to 0.
FADE_S = 3.0


class PresencePersistence:
    """Stateful presence-state router with persistence/fade.

    Feed :meth:`update` with the current inference outputs on every
    pipeline step; read the display state via the return value or
    :meth:`current`. All times come from ``clock`` (default
    :func:`time.monotonic`) so tests can drive time deterministically.
    """

    def __init__(self, clock: Callable[[], float] | None = None) -> None:
        self._clock = clock or time.monotonic
        self._state = "UNKNOWN"
        self._shown_confidence: Optional[float] = None
        self._last_strong_confidence = 0.0
        self._exit_started: Optional[float] = None
        self._last_person_ts: Optional[float] = None

    def reset(self) -> None:
        """Forget everything (session switch / stream restart)."""
        self._state = "UNKNOWN"
        self._shown_confidence = None
        self._last_strong_confidence = 0.0
        self._exit_started = None
        self._last_person_ts = None

    def current(self) -> Tuple[str, Optional[float]]:
        """Last display state + shown confidence (no time advance)."""
        return self._state, self._shown_confidence

    def update(self, *, presence_label: str, movement_label: str,
               confidence: Optional[float],
               now: Optional[float] = None) -> Tuple[str, Optional[float]]:
        """Route one inference step to a display state.

        ``presence_label`` is PERSON/EMPTY/UNKNOWN (owner:
        ``sensing/presence``); ``movement_label`` is MOVING/STATIC/UNKNOWN
        (owner: ``sensing/activity``); ``confidence`` is the current
        (possibly derated) uncalibrated evidence score or ``None``.
        Advances time (sets/resets the EXITING hold timer).
        """
        ts = self._clock() if now is None else float(now)
        return self._route(presence_label, movement_label, confidence, ts,
                           commit=True)

    def preview(self, *, presence_label: str, movement_label: str,
                confidence: Optional[float],
                now: Optional[float] = None) -> Tuple[str, Optional[float]]:
        """Same routing as :meth:`update` but side-effect-free.

        Used when re-rendering the current step under a different session
        context (e.g. a degrade derate) without disturbing the hold/fade
        timers owned by the live pipeline.
        """
        ts = self._clock() if now is None else float(now)
        return self._route(presence_label, movement_label, confidence, ts,
                           commit=False)

    def _route(self, presence_label: str, movement_label: str,
               confidence: Optional[float], ts: float,
               commit: bool) -> Tuple[str, Optional[float]]:
        if presence_label == "PERSON":
            if commit:
                self._exit_started = None
                self._last_person_ts = ts
                if confidence is not None:
                    self._last_strong_confidence = float(confidence)
            if confidence is not None and confidence < LOW_CONFIDENCE_BAND:
                state: str = "LOW_CONFIDENCE"
            elif movement_label == "MOVING":
                state = "MOVING"
            elif movement_label == "STATIC":
                state = "STATIONARY"
            else:
                state = "DETECTED"
            if commit:
                self._state = state
                self._shown_confidence = confidence
            return state, confidence

        if presence_label == "EMPTY":
            # Strong evidence just disappeared: hold, fade, then ABSENT.
            if self._state in ("MOVING", "STATIONARY", "DETECTED",
                               "LOW_CONFIDENCE", "EXITING"):
                started = self._exit_started
                if started is None:
                    started = ts
                    if commit:
                        self._exit_started = ts
                age = ts - started
                if age < HOLD_S:
                    state, shown = ("EXITING", self._last_strong_confidence)
                elif age < HOLD_S + FADE_S:
                    frac = 1.0 - (age - HOLD_S) / FADE_S
                    state = "EXITING"
                    shown = (self._last_strong_confidence
                             * max(frac, 0.0))
                else:
                    state, shown = "ABSENT", None
                    if commit:
                        self._exit_started = None
                if commit:
                    self._state = state
                    self._shown_confidence = shown
                return state, shown
            if commit:
                self._state = "ABSENT"
                self._shown_confidence = None
            return "ABSENT", None

        # UNKNOWN inference: keep whatever we had (never invent).
        return self._state, self._shown_confidence
