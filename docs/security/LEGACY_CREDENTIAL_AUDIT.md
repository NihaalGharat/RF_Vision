# LEGACY CREDENTIAL AUDIT (RFVISION-006)

> All credential VALUES are REDACTED in this file by policy. Detection locations
> are recorded so the exposure can be managed; values are never reproduced.

- Audit date (UTC): 2026-09-21
- Scope: full legacy source
  `~/Downloads/RF Vision Files-20260921T163602Z-1-001`
  (232 files) + migrated copies in this repo + external research-data copies.
- Method: case-insensitive scan for `password|passwd|api[_-]?key|secret|
  token|private[_-]?key|ssh[_-]?key|WPA|PSK|ssid`, followed by manual review of
  every hit class. Binary `.npz/.png` byte-matches for `WPA|PSK|ssid` are false
  positives (compressed bytes) and were excluded.

## 1. CONFIRMED findings (values SUPPRESSED)

| # | What | Where (legacy) | Migrated? |
|---|---|---|---|
| F1 | Wi-Fi password (WPA2-PSK) printed VERBATIM inside the `sdkconfig.defaults` string of `02_FIRMWARE/firmware_versions.json` (+ byte-identical mirrors in `04_EVENTS_METADATA/metadata/`, `CSI_SENSE_001/METADATA/`, `SOURCE_PROJECT/`, `99_ARCHIVE/`) | `firmware_versions.json` family | YES — value replaced with `REDACTED` (see `docs/hardware/legacy/CSI-SENSE-001_firmware_versions.REDACTED.json`; 1 occurrence redacted; original SHA recorded in `LEGACY-MIGRATION-PROVENANCE.md`) |
| F2 | Same password VERBATIM in 2 lines of `07_REPORTS/CSI-VERIFY-001_FINAL_REPORT.md` (sdkconfig quote + `nmcli --show-secrets` transcript line) + mirrors in `FINAL-FOLDER-AUDIT-001.md`, manifests | `07_REPORTS/` family | YES — both occurrences replaced with `REDACTED` in `docs/research/legacy/CSI-VERIFY-001_FINAL_REPORT.md`; 1 further occurrence redacted in `FINAL-FOLDER-AUDIT-001.md` |
| F3 | `nmcli --show-secrets` methodology mentions (bare command invocations, NO values) across reports/plan/`hardware_identity.json` (`security` field) | widespread (part of 74 `password`-pattern hits / 24 files, mostly provenance discussion) | Methodology kept; `hardware_identity.json` wording changed to `"WPA2-PSK (method on file, value not migrated)"`; bare command lines retained (they disclose nothing) |

Total password-value occurrences redacted during migration: **4**
(`firmware_versions.json` ×1, VERIFY final report ×2, folder-audit ×1).

## 2. Deliberately RETAINED (not secrets)

Router BSSID, ESP32 MAC, SSID `Nihaal`, gateway IP, channel/frequency — kept in
migrated files per the legacy README §Security policy (reproducibility IDs).
They identify the experimental link; they do not authenticate to anything.

## 3. NOT found

API keys, auth tokens (`token` hits are English usage + `api.macvendors.com`),
private keys, SSH keys, `.pem`/`.key` files — none in legacy or current tree.

## 4. Current-repo verification (post-migration)

- Grep of migrated tree for the legacy password value: **0 hits**.
- Grep for `EXAMPLE_WIFI_PASSWORD`: **0 hits** outside this audit's prose
  (this file names the CONFIG key only, never its value).
- Grep for `BEGIN .*PRIVATE KEY`: **0 hits**.
- `firmware/esp32/csi_recv_router/sdkconfig.defaults` contains NO SSID/password
  (unchanged, verified by read).
- `.gitignore` already blocks `*password*`, `*secret*`, `*token*`, `*.pem`,
  `.env` filenames.

## 5. Recommendations

1. **Rotate the Wi-Fi password** — it lived in a Live-USB archive staged for
   cloud upload and in multiple report mirrors.
2. Treat the legacy Downloads folder as credential-bearing until cleanup is
   verified (cleanup moves duplicates/obsolete to the quarantine dir; canonical
   sources remain until the user decides their end state).
3. Never commit raw captures or sdkmate-style config dumps; keep secrets in
   `.env` (git-ignored) per `.gitignore` policy.
