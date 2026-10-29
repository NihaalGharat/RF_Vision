# RF Vision — Operator Demo Runbook

Purpose: a short, honest demonstration of real dual-receiver CSI acquisition and
live visualization. This is not a new research trial or a validated sensing
demonstration.

## Preconditions

- Use the intended 2.4 GHz network. If using the verified `VCET Lab` baseline,
  verify channel 6 and the expected BSSID/SSID from operator-local notes. Exact
  network identifiers are intentionally omitted from the public repository.
- Both ESP32 receivers are attached and available as `/dev/ttyUSB0` and
  `/dev/ttyUSB1`.
- No other process owns the serial ports or the chosen web port.
- Read `docs/research/SCIENTIFIC_VALIDATION_STATUS.md` for the evidence
  boundary.

## Demo sequence

1. Enable the intended 2.4 GHz Wi-Fi network.
2. Verify the laptop SSID/BSSID/channel and both receiver BSSID/channel match
   the expected operator-local values. Do not continue on a mismatch.
3. Start the web console once on an isolated local port, for example:
   `python3 -m web.server --port 8130`.
4. Start dual acquisition once from Hardware.
5. Confirm both nodes show `LIVE_VERIFIED`, session `SYNCED`, and backend
   `RF_READY`.
6. Open Live Sensing. Verify fresh A/B CSI frames, `ws connected`, and `2/2`
   live nodes. Do not rely on the legacy single-source status card.
7. Open Visualization. Verify independent A/B activity histories and the 3D
   scene. Reference View is illustrative: one AP and two physical CSI
   receivers; waves are not measured time-of-flight.
8. Explain that the two ESP32s are receivers and the AP is an illustrative
   transmitter, not a second sensing receiver.
9. If acquisition remains stable, demonstrate controlled stillness/movement.
   Describe it as observed relative RF change, not detected presence or pose.
10. Show previously recorded research evidence with its historical/offline
    label. Do not present it as a new live run.
11. Before stopping, capture the evidence you intend to keep: screenshots,
    `/api/v1/nodes`, `/api/v1/rf_readiness`, `/api/v1/vision`, and the visible
    route state.
12. Stop acquisition cleanly. Verify the server is stopped and both serial
    ports are released.

No new 110- or 120-second trial is required for this demonstration.

## What to say

- Verified: real dual ESP32 CSI acquisition and live measured A/B display.
- Observed: reference-relative RF activity changes in some sessions.
- Exploratory: association between those changes and a human in the path.
- Not available: validated presence/activity classifier, human coordinates,
  trajectory, pose, obstacle detection, obstacle localization, or geometry.
- Illustrative: Reference View room and wave animation.
- Never quote residual-energy ratios as accuracy or confidence.

## Fallback if live CSI is unavailable

Do not fabricate data and do not silently switch to synthetic/simulated input.

1. Say clearly that live CSI is unavailable and why, if known.
2. Show previously verified evidence from the operator-local bundles with an
   explicit `HISTORICAL` or `OFFLINE` label. Detailed evidence, screenshots,
   and logs are retained outside the public repository; do not publish raw CSI
   or environment-identifying logs.
3. Explain that synthetic browser fixtures validate UI plumbing only; they are
   not live sensing evidence.
4. Do not claim the fallback is a current live result.

## Stop and cleanup

- Stop the dual session before closing the server.
- Confirm the server process is gone and the web port is no longer listening.
- Confirm `/dev/ttyUSB0` and `/dev/ttyUSB1` are free.
- Leave research data and correction manifests untouched.

## Recovery / evidence references

- Operator-local recovery snapshots and final checkpoint reports are retained
  outside the public repository.
- Detailed evidence bundles are local-only; raw CSI remains in the Git-ignored
  `research-data/` tree.
- Do not publish credentials, raw CSI, environment-identifying logs, or live
  screenshots containing private network details.
