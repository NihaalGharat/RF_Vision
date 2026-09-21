# `dsp/` — why not `signal/`

This package implements the **`signal/` block of the RF Vision target
architecture** (preprocessing, amplitude, phase, filtering, features).

It is named `dsp/` (digital signal processing) because a top-level Python
package named `signal` irreversibly shadows the standard library's
`signal` module in every process that puts the project root on
`sys.path`. Consequences observed during foundation testing:

- `import signal.preprocessing` resolves to stdlib `signal.py` (a module,
  not a package) whenever stdlib `signal` was imported first — which
  pytest and joblib do at startup;
- joblib's loky backend (`import signal`) would receive our package and
  lose `SIGTERM`/`SIGKILL`, breaking sklearn parallel training.

Renaming is the standard fix and is recorded as a deliberate, documented
deviation from the architecture diagram (which keeps the name `signal/`
for the subsystem). Import paths: `dsp.preprocessing`, `dsp.amplitude`,
`dsp.phase`, `dsp.filtering`, `dsp.features`.
