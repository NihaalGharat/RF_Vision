# Dependencies

Live pins are split so headless capture nodes stay lean. All installed and
tested on Ubuntu + Python 3.14 during foundation build (Sep 2026).

## requirements-base.txt (capture → features → sensing → classical ML)

- `pyserial>=3.5` — USB-serial capture + recorder (MIT-ish/ BSD)
- `numpy>=1.26` — I/Q math, features (BSD)
- `scipy>=1.11` — Butterworth filtering (BSD)
- `pandas>=2.1` — datasets (BSD)
- `scikit-learn>=1.3` — KNN/RF presence + position, metrics (BSD)
- `matplotlib>=3.8` — dataset/debug plots (PSF-based)
- `PyYAML>=6.0` — config (MIT)
- `joblib>=1.3` — model persistence (BSD)

## requirements-gui.txt (optional)

- `PyQt6>=6.6` — live dashboard (GPL/commercial dual — note: distributing
  the GUI may require a commercial Qt license; headless pipeline is
  unaffected) + `pyqtgraph`-class plotting via matplotlib Qt backend.

## requirements-ml.txt (optional)

- `torch>=2.2` (CPU wheel sufficient) — MLP presence/position (BSD).
  Without it, `train.py` runs baselines only and says so loudly.
  CUDA variant documented, never a hard gate.

## requirements-dev.txt

- `pytest>=8` — test runner (MIT). stdlib `unittest` also works.

## Firmware / system

- ESP-IDF v5.4.4 (commit `296b6ea…`) for `firmware/esp32/csi_recv_router`.
- Ubuntu Linux, `/dev/ttyUSB0` @ 921600 8N1. No GPU, no database.

## Excluded stacks

- csi-sensing CUDA-12.1 pin set (license-blocked; not inherited).
- ESP-IDF v4.3 / Arduino cores (reference firmware only, not built).
- esp-csi demo-parser extras (`statsmodels`, `pyqtgraph` for the old
  viewer) — pruned; `visualization/rf/csi_viewer_reference.html` needs only
  a Chromium/Edge browser.
