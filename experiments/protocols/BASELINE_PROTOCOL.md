# Baseline Experiment Protocol (template — NOT executed)

Methodology reference for future studies. No human experiment is part of
foundation work; executing this requires explicit approval + ethics
considerations for the deployment context.

## CSI-SENSE-001 pattern (adapted from the integrated calibration flow)

1. Fix hardware per `docs/hardware/BASELINE.md`; record firmware/software/
   config versions + environment + geometry (see metadata schema).
2. Run `localization/calibration/calibrate.py`: empty room + positions
   0.00/0.25/0.50/0.75/1.00, ≥15 s per step. Keep `calibration.json`.
3. Collect ≥6 sessions per class with `ai/datasets/collector.py`
   (short repeated sessions beat one long session; vary time-of-day).
4. Train (`ai/training/train.py`) → session-split val selection → honest
   test report (`training_report.json`) → independent `ai/evaluation/`.
5. Report cross-session metrics; never quote synthetic or same-session
   numbers as results.

## Ground truth

Known scripted positions on the measured link line (tape + photo log);
subject count = 1 until multi-person is a scheduled package.
