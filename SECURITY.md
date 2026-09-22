# Security Policy — RF Vision

## Scope

RF Vision is a privacy-preserving Wi-Fi CSI research platform. All RF
processing is local: capture, parsing, signal processing, inference, and
visualization run on the operator's own machine. The repository contains
no cloud services, no telemetry, and no remote data transmission.

## No secrets in commits

- Never commit `.env` files, API tokens, passwords, Wi-Fi credentials,
  SSH keys, certificates, or authentication headers. Root `.gitignore`
  excludes `.env*`, `credentials*`, `*password*`, `*secret*`, `*token*`,
  `*.pem`, and `*.key`.
- Firmware Wi-Fi credentials live only in the local, git-ignored
  `sdkconfig` (generated via `idf.py menuconfig`); only the
  credential-free `sdkconfig.defaults` is tracked.
- Research provenance records use `REDACTED` placeholders where a live
  credential would otherwise appear.

## Research-data handling

- Raw CSI captures, derived datasets, and UI evidence binaries stay
  outside Git history (`research-data/` is ignored except manifests).
  Git tracks only identifiers, sizes, SHA-256 checksums, and provenance
  metadata. Verify artifacts with the recorded SHA-256 sidecars.

## Reproducibility

- Pinned baselines: ESP-IDF v5.4.4, esp-csi `8633d671`, requirements
  files, and `firmware/.../dependencies.lock`. CI runs the offline test
  suite only — no hardware, no radio, no credentials required.

## Reporting a vulnerability

Open a GitHub issue describing the concern without including secrets,
credentials, or private data. Do not submit proof-of-concept exploits
against live networks. Reports are reviewed on a best-effort basis by
the maintainers.
