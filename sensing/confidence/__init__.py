"""RF Evidence Confidence aggregator (P1 showcase foundation).

See :mod:`sensing.confidence.confidence` for the binding honesty rules.
Re-exported here so consumers write ``sensing.confidence.aggregate_evidence``.
"""

from sensing.confidence.confidence import (
    CALIBRATION_LABEL,
    DEGRADE_DERATE,
    aggregate_evidence,
)

__all__ = ["CALIBRATION_LABEL", "DEGRADE_DERATE", "aggregate_evidence"]
