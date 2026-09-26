# RFVISION-ARCHITECTURE-NETWORK-AGNOSTIC-CHECKPOINT

**Status: RESEARCH / ARCHITECTURE REVIEW ONLY — READ → ANALYZE → PROPOSE.
No code, firmware, config, protocol, threshold, AP, wiring, commit, or
experiment was touched. No E1/E2/P1. No esptool, no out-of-stack serial use.**

## 1. Executive summary

**Is RF Vision fundamentally router/network-dependent, and where?**
Yes at the acquisition fringe, no in the core — the dependency is shallow but
load-bearing. Tracing the real code paths shows:

- **Firmware (`csi_recv_router`) is the single hard network lock-in (Class C/E):**
  build-time Kconfig SSID/password (`sdkconfig:418-419`), `example_connect()`
  only, no reachable runtime provisioning (STDIN path compiled out,
  `sdkconfig:416`; the `PROVIDE_WIFI_CONSOLE_CMD` command is compiled in,
  `sdkconfig:417`, but unreachable — no console REPL is ever started in
  `app_main.c`, and UART0 is a one-way CSI stream). CSI records are generated
  **only** from ping responses of the joined AP (100 Hz nominal ICMP to the
  gateway; BSSID-filtered in the RX callback). No IP/DHCP → no CSI at all.
- **Acquisition layer (`web/`) is network-aware but already parameterized:**
  `expected_bssid`/`expected_channel`/`board_mac` are constructor arguments
  with HOME values as *defaults* (`web/source.py:229-231`), and the gate
  enforces single-channel/single-BSSID unanimity. The coupling is explicit
  validation, not hidden logic — repointing it is a config change, not a
  redesign. No SSID/frequency concept exists anywhere in `csi/` or `web/`.
- **Sync (`ClockOffsetEstimator`) is rate-agnostic by construction** — it maps
  device↔host clocks from `(device_ts, host_ts)` pairs with median/MAD, no Hz
  or cadence assumption. The 2 ms tightness (`dual_node.py:52-53`) is a
  *policy* in the consumer, and HOME evidence says that policy, not the AP,
  is what fails under dual-node transport distress.
- **Downstream (preprocess → features → inference/XAI/viz) is already
  network-blind:** it consumes amplitudes + RSSI + `ts_local`; BSSID, channel,
  MAC, seq, MCS never flow past the acquisition envelope. Sanitizing RSSI
  handling and recording network context are the remaining gaps, not
  decoupling.
- **Achievable level: Level 2 (network-condition-aware) now, Level 3
  (RF-source abstraction) with modest engineering.** Level 1
  (router-specific) is where we accidentally live today, via the firmware
  provisioning path and HOME-defaulted acquisition constructors — not via
  physics. This checkpoint was produced read-only; §19/§21 list the changes
  without making them.

## 2. Current architecture (actual data flow, verified paths)

```text
AP (HOME Nihaal/8c:53:c3:5b:e1:59/ch1 today)
 │ ICMP echo replies to ESP32 ping (100 Hz nominal, gateway target)
 ▼
ESP32 Wi-Fi RX → wifi_csi_rx_cb (BSSID-filtered, app_main.c:61-63,179)
 │ CSI_DATA ASCII line via ets_printf @921600 8N1 (25 cols, classic ESP32 layout)
 ▼
UART/USB → SerialLineSource (per-LF host rx_ns=monotonic_ns, live_serial.py:157,209)
 │ EspCsvAdapter.handle_line: strict 25-col parse, int8 payload check (esp_csv_adapter.py:73-128)
 ▼
CsiSample (csi_parser.py:66-95): ts_esp32_us (=rx_ctrl.timestamp, µs, 32-bit wrap),
 ts_local (time.time), ts_host_ns (monotonic_ns), seq/mac/rssi/channel/.../csi int8[]
 │ LiveProvider._ingest: storm/throughput/settle/gate (source.py:350-519)
 │  gate: 5-220 Hz, channels=={expected}, bssids=={expected}, fresh, clean
 ▼
NodeProvider → DualNodeSession (dual_node.py): per-node ClockOffsetEstimator.observe
 │  SYNCED iff n≥64 and MAD≤2 ms per node (dual_node.py:52-53,230-242)
 ▼
Frames: sensing.snapshot {amplitudes (62/64 full), rssi, phases=None, UNKNOWN labels}
 │  + node_status Proof-of-Provenance {channel/bssid/tones/rate/sync telemetry}
 ▼
Preprocessor (54 valid-subcarrier amps) → FeatureExtractor (180-D vector + rssi)
 → inference (presence/movement/position) → XAI / dashboard
RawSessionWriter preserves full META_FIELDS incl. all three timestamps (serial_receiver.py:66-71)
```

## 3. Dependency inventory

| # | Dependency | Location | Why it exists | Gen | Trans | Sync | Feat | Essential | Abstractable |
|---|---|---|---|---|---|---|---|---|---|
| 1 | SSID+password (build-time) | `sdkconfig:418-419` via `example_connect()` | station join | indirect (no join→no traffic) | no | no | no | join is; build-time baking is not | **yes — runtime/NVS provisioning** |
| 2 | BSSID filter | `app_main.c:61-63,179` | router-compat (LLTF comment :130-132) | **yes — only AP frames emit** | no | no | no | AP association is; single-BSSID hard filter is a choice | partially (multi-AP/promiscuous modes exist in ESP-IDF) |
| 3 | Ping-to-gateway traffic | `app_main.c:183-204` (100 Hz, `data_size=1`) | deterministic stimulus | **yes — sets nominal rate** | yes (UART load ~480 B/rec) | indirect via rate | indirect via rate | stimulus is; gateway-ICMP specifically is not | **yes — traffic-gen mode enum** |
| 4 | IP/DHCP + gateway | `app_main.c:193-196`, `example_connect()` | ping target + join | **yes — no IP→no CSI** | no | no | no | for *this* firmware | no (within this backend) |
| 5 | `expected_bssid`/`expected_channel`/`board_mac` defaults (HOME) | `web/source.py:229-231,780-782`, `dual_node.py:135-136`, `nodes.py:60-74` (identity only, RF explicitly not there :15) | validation safeguard | no | no | no | no | validation yes; HOME values no | **yes — per-session config** |
| 6 | Gate rate window 5–220 Hz | `web/source.py:212-216` | reject dead/flooded links | no | yes | indirect | no | bounds yes; exact numbers policy | yes — per-source profile |
| 7 | `sample_rate=60 Hz` assumption | `config/settings.py:34`, `default.yaml:12`, `preprocessing.py:205` (filter design only) | filter + window sizing | no | no | no | mild (window ≈1 s) | no | yes — measured-rate design |
| 8 | Tone geometry (128 B→62/64; valid mask 54) | `csi_parser.py:36,51-55`, `preprocessing.py:62,276-284` | 20 MHz LLTF physics | no (shapes representation) | no | no | **yes — fixed dims** | physics yes; single-geometry code yes-today | yes — geometry-aware layers |
| 9 | `rx_ctrl.timestamp` 32-bit µs wrap | wire `cols[18]`, `csi_parser.py:29` | ESP-IDF API | no | no | **yes — unwrapped use** | no | API-shaped | yes — wrap compensation |
| 10 | Conflated `ts_esp32_us==ts_wifi_us` in CSV path | `esp_csv_adapter.py:131,152` | single clock on wire | no | no | mild | no | wire-shaped | yes — document/contract |
| 11 | Channel/BSSID/RSSI/MCS metadata | wire cols; `CsiSample`; dropped downstream (§7) | measurement context | context | no | no | RSSI only (features +3) | context yes; model-input no | keep as context, out of model |
| 12 | Dual-UART/USB host transport | `live_serial.py:31-32`, `serial_config.py` | physical link | no | **yes — dual-only corruption observed** | indirect | no | link yes; shared-bus fragility is platform fact | mitigate (topology/buffering), not abstract |
| 13 | Sync policy n≥64, MAD≤2 ms | `dual_node.py:52-53` | stability criterion | no | no | **yes — fails under transport jitter** | no | criterion yes; 2 ms value policy | yes — adaptive/contextual thresholds |
| 14 | Drift estimator (index-based LS slope) | `sync.py:71-88` | drift readout | no | no | mild (cadence-irregular bias) | no | diagnostic | yes — time-based regression |
| 15 | Laptop Wi-Fi network | — | operator convenience only | no | no | no | no | **no** | already irrelevant (proven by VCET attempt 2) |
| 16 | `drift_per_sample`, `esp_to_host_latency_us=None` honesty | `sync.py`, `dual_node.py:18-23,112-120` | telemetry | no | no | no | no | — | keep |

(Gen=CSI generation, Trans=transport, Sync=synchronization, Feat=downstream features.)

## 4. Dependency classification (A–E)

- **A — Fundamental (keep, record, never remove):** channel, bandwidth/cwb,
  RSSI, noise floor, MCS/rate/sig_mode, multipath-embodying tone amplitudes,
  packet timing as a measured quantity, antenna index.
- **B — Acquisition-source (isolate behind `CsiSource`):** ping-to-gateway
  stimulus (#3), IP/DHCP requirement (#4), BSSID RX filter (#2), 921600
  `ets_printf` transport, `rx_ctrl.timestamp` wrap (#9), single-clock CSV
  conflation (#10), 20 MHz LLTF-only CSI config (`app_main.c:166-174`).
- **C — Implementation (fixable in our code):** build-time credential baking
  (#1), HOME-defaulted constructors (#5), fixed 60 Hz design rate (#7),
  single-geometry feature dims (#8), index-based drift slope (#14),
  unwrapped-timestamp sync use (#9), hardcoded 2 ms/64 policy as constants
  rather than session profile (#13).
- **D — Experimental-context (record always, model never implicitly):**
  SSID/BSSID/channel/frequency/width/AP model/firmware SHA/traffic mode/rate
  stats/RSSI distribution/node geometry/environment label/session ID.
- **E — Accidental coupling (redesign candidates):**
  1. **Firmware SSID baking** — the system cannot change rooms without a
     rebuild+reflash; this is what blocked VCET, not physics.
  2. **Stimulus = gateway ping** — couples CSI existence to router ICMP
     behavior and DHCP; any AP that answers differently changes the science
     silently.
  3. **HOME values as code defaults** — `source.py:229-231` makes one network
     the path of least resistance; every future session must consciously
     override.
  4. **Fixed E1-style count/rate gates assuming a "Goldilocks" AP** — HOME
     evidence (E1: starved-but-synced vs bursty-but-unsynced) shows policy
     gates tuned to one AP's personality.
  5. **Laptop-Wi-Fi-as-environment fallacy (process, now documented)** —
     attempt 2 proved laptop association changes nothing about the ESP32 RF
     path; guard against relapsing in future field work.

## 5. CSI acquisition analysis (firmware, `app_main.c` 221 lines)

- **A. What generates a record:** an 802.11 frame from the associated AP
  arriving at the ESP32 and passing the `memcmp(mac, ap-bssid)` filter
  (`:61-63`), with the CSI engine enabled (`:176-180`). In practice the
  overwhelmingly dominant such frames are **ICMP echo replies to the
  firmware's own 100 Hz gateway ping** (`CONFIG_SEND_FREQUENCY=100`, `:38`;
  `interval 10 ms`, infinite count, 1-byte payload, `:188-191`).
- **B. Only router responses? Yes by code** — no promiscuous, no multi-AP, no
  self-stimulus path. The sender can only ever be whichever AP
  `example_connect()` joined (corroborated: unanimous-BSSID captures; non-CSI
  lines are UART fragments/binary, never other-AP CSI).
- **C. Does the ESP32 actively generate traffic? Yes** — the ping session
  (`esp_ping`, 3 KiB task). The AP is passive except for answering; CSI is
  measured on the *reply* path (AP→ESP), so AP reply timing/jitter directly
  shapes inter-arrival.
- **D. Arbitrary associated traffic? No, as built** — the BSSID filter would
  pass any frame from the joined AP, but with no other stimulus configured,
  beacons/management alone would give a sparse, beacon-interval-quantized
  stream. Enabling data-traffic CSI is an IDF-config matter, not a hardware
  impossibility.
- **E. Without IP connectivity? No** — `example_connect()` must succeed
  (`ESP_ERROR_CHECK`, `:217`) and the ping target is the DHCP-provided
  gateway (`:193-196`). Static-IP builds could relax DHCP but not the
  join+gateway shape.
- **F. Specific router behavior depended on:** ICMP responsiveness and reply
  timing of the gateway; DHCP server; all-channel-scan join by SSID/signal
  (`sdkconfig:422,439`). Nothing in the record path depends on router brand —
  but everything depends on the router *answering pings at a stable rate*.
- **G. Hardware limitations (ESP32):** single 20 MHz LLTF-only CSI config
  (router-compat comment `:130-132`); `rx_ctrl.timestamp` 32-bit µs (~71.6 min
  wrap); UART deprives us of hardware flow control at ~480 B/record ASCII
  verbosity (~74% of 921600 in singles, worse bursty in dual); one station
  association at a time.
- **H. Implementation choices (could differ in other firmware):** ASCII
  `ets_printf` wire format; ping-to-gateway stimulus; BSSID hard filter;
  100 Hz nominal; gain-compensation application in firmware (`:70-84`);
  no console/REPL; credentials via Kconfig.
- **I. Replaceable without touching downstream? Almost today:** downstream of
  `DualNodeSession` consumes only `(amplitudes, rssi, ts_local)` plus
  telemetry — any backend emitting valid `CsiSample`s flows through
  preprocessing→features→inference untouched. The friction is upstream of
  that boundary: 25-col wire-format parsing, 128 B geometry, and HOME-default
  constructors. A `CsiSource` interface + session-profile config removes all
  three.

## 6. CSI data-contract analysis

Per record (classic-ESP32 25-col wire → `CsiSample`, `csi_parser.py:66-95`):

- **RAW RF MEASUREMENT:** 62 complex subcarrier/tone measurements
  (128 B payload → `(128−4)/2` after `first_word_invalid` trim; 64 when
  untrimmed; preprocessed to **54 valid subcarriers** `0-26,32-58` as
  amplitudes) **forming raw RF sensing inputs from which downstream features
  are extracted** — never "62 features." Plus RSSI, noise floor, AGC/FFT gain
  (C-variant cols), channel/secondary/cwb, MCS/sig_mode/rate/stbc/sgi/
  smoothing/aggregation/ampdu_cnt, antenna, sig_len.
- **DERIVED FEATURE (host-side, not on wire):** amplitude/phase vectors,
  180-D `FeatureVector`, presence/movement/position outputs.
- **TRANSPORT METADATA:** `seq` (gap/dup/ooo accounting in `source.py:391-410`),
  `payload_len`/`first_word_invalid` integrity, byte throughput, storm flags.
- **NETWORK CONTEXT:** `mac` (AP BSSID by construction), channel, rate/MCS —
  recorded, validated, then **dropped before the model** (only RSSI survives
  into features, +3 dims).
- **SYNCHRONIZATION METADATA:** `ts_esp32_us` (device), `ts_local`/`ts_host_ns`
  (host), `host_pipeline_us`, offset/jitter/drift/ready telemetry.

## 7. Acquisition-layer analysis (`web/`)

Already abstracted: no SSID/frequency concept in code; node identity
(`csi/transport/nodes.py`) deliberately excludes RF config (`:15-18`); gate
inputs are constructor parameters; tone count is *reported*, never enforced
(the emergent-62 finding). Assumptions entering here: HOME-defaulted
`expected_bssid`/`expected_channel`/`board_mac` (#5); unanimity gate (correct
as validation — keep, but source from session profile); 5–220 Hz window (#6,
empirically motivated: genuine 44–156 Hz + C1 101/C2 75 Hz noted at
`source.py:213-214`); per-line `rx_ns` stamping (correct design — preserves
the UART-arrival leg for pipeline telemetry). **Do not remove validation;
relocate its values** from code defaults into per-session profiles.

## 8. Synchronization analysis (`localization/synchronization/sync.py`, 106 lines)

`ClockOffsetEstimator` is a clean device↔host mapper: `observe()` takes unit-
agnostic `(device_ts, host_ts)` pairs, offset = median, jitter = MAD, drift =
index-based LS slope; window 64, `stable()` = n≥min ∧ jitter≤max. It assumes
**nothing** about rate, cadence, gaps, order, or units ("identical units:
caller responsibility", `:23-25`) — and that sparseness is both virtue and
gap: no wrap handling, no monotonicity/finite checks, no seq awareness
(all gap/dup/ooo logic lives in `source.py:391-410`, correctly separated).
Timing trichotomy is a *caller convention*, honestly maintained:
ESP-local (`ts_esp32_us`) vs UART-arrival (`rx_ns` → `host_pipeline_us`) vs
host (`ts_host_ns`), with `esp_to_host_latency_us=None` explicitly refusing
to claim the unmeasurable leg (`dual_node.py:18-23`). Coupling verdict:
**the estimator is network-agnostic; the 2 ms/64 SYNCED policy is not** —
HOME dual shows per-node jitter 9.06/2.61 ms under transport distress while
pipelines stay ~5 ms, i.e. the criterion measures transport health as much as
clock mappability. Fix = contextual thresholds + wrap/time-based drift, not a
new estimator.

## 9. Home diagnostic interpretation (evidence)

Singles prove the chain *can* be clean: A 141.5/141.5 Hz ESP/host with
dt-med 6.29 ms, zero gaps/storms, LIVE_VERIFIED; B 128.4/128.5 Hz active
after a 7 s association delay (transport honesty: wall-rate 98.5 vs active
128.5 — the stack reports both). Dual proves fragility is in the **shared
transport + strict policy**, not the AP: 18/82 gaps, 3/11 storms (incl. a
~4 s identical-tail stuck buffer on A), host-rate divergence (76.8/95.6 vs
115.6/125.5 ESP), 0% SYNCED under the 2 ms rule. E1's inversion (starved but
79.2% SYNCED vs bursty 0%-sync) shows fixed gates demand a Goldilocks AP
personality the HOME router only sometimes provides. Architectural reading:
per-node generation is healthy; simultaneous dual-UART load + bursty AP
replies + tight sync policy interact. Separate the three in all future
analysis — never "the AP did it" without the transport and estimator legs.

## 10. VCET architectural interpretation (evidence)

Attempt 2 is a controlled demonstration of coupling #E5: laptop on
`VCET Lab/12:c5:f3:7d:04:3d/ch6` while Node A records 2701 valid frames
unanimously `HOME/ch1` — environment labels attached to the *laptop* are
scientifically void; only BSSID-in-record counts. The association check
closed the mechanism question: `CASE_C` — SSID baked at `sdkconfig:418`,
STDIN provisioning compiled out (`:416`), no console REPL started despite
`PROVIDE_WIFI_CONSOLE_CMD=y` (`:417`, dormant registration only), no VCET
string anywhere. So today, **changing rooms costs a rebuild + reflash** —
the textbook E1/E5 accidental coupling, and the reason no VCET-labeled data
exists. It is a provisioning-shape problem, not evidence that sensing can't
generalize.

## 11. Network-agnostic target architecture

```text
                    RF SOURCE (any: AP / hotspot / future radiator)
                       │
             ┌─────────┴─────────┐
             │                   │
     provisioned join      provisioned join   (credentials: runtime profile, §14)
             │                   │
   CsiSource[esp32-router]  CsiSource[esp32-router]   (identical backend ×2 today;
             │                   │                     other backends later, §13)
             └─────────┬─────────┘
                       │  CsiSample stream (contract §6, source-agnostic)
              Acquisition Layer (gate from session profile, not code defaults)
                       │  + NetworkContext attached, never injected (§14)
              Normalization Layer (per-session / baseline-relative, §15 C+D)
                       │
             Synchronization Layer (contextual thresholds, wrapped-time-aware)
                       │
                Feature Layer (geometry-aware dims; RSSI quarantined, §16)
                       │
             RF Vision Core Model (amplitudes + quarantined context only)
                       │
        ┌──────────────┼──────────────┐
        │              │              │
     Presence    Spatial/XAI    Visualization
   (all consumers read NetworkContext for display/provenance, never as features)
```

Principle: the router is a **measurement condition with a serial number**,
carried alongside the data, validated against, and available for
stratification — never a default, never a feature, never a sync prerequisite.

## 12. CSI source abstraction (proposal, not implemented)

```python
class CsiSource(Protocol):
    def start(self) -> NodeIdentity: ...
    def stop(self) -> None: ...
    def records(self) -> Iterator[CsiSample]: ...  # lossless, timestamped (§6)
    def health(self) -> SourceHealth: ...          # rate/gaps/storms/transport
    def metadata(self) -> SourceMetadata: ...      # backend id, fw SHA, geometry
```

`LiveProvider` becomes `Esp32RouterSource(CsiSource)`; `FakeLineSource`
already prefigures the offline backend (`OfflineFileSource` replays
`RawSessionWriter` META_FIELDS losslessly). Future backends (alternate ESP
firmware, other CSI hardware) implement the same five methods; downstream of
`DualNodeSession` is untouched by construction. Keep validation *inside* the
abstraction (unanimity gate) but feed it from the session profile.

## 13. Network context model (proposal)

```python
@dataclass(frozen=True)
class NetworkContext:
    session_id: str            # REQUIRED — joins data↔context everywhere
    environment_label: str     # REQUIRED — e.g. "HOME", "VCET-lab" (human claim)
    ssid: str                  # REQUIRED — claimed network
    bssid: str                 # REQUIRED — measured, from records (beats claim)
    channel: int               # REQUIRED — measured
    frequency_mhz: int         # REQUIRED — measured/known
    channel_width_mhz: int     # REQUIRED — measured/known
    source_firmware_sha: str   # REQUIRED — provenance
    source_hardware: str       # REQUIRED — e.g. "esp32"
    traffic_mode: str          # REQUIRED — e.g. "gateway-ping-100Hz"
    csi_rate_stats: dict       # REQUIRED — esp/host Hz, p50/p99/max dt, gaps
    rssi_stats: dict           # REQUIRED — distribution summary
    ap_model: str | None       # OPTIONAL — when known
    operator_notes: str        # DIAGNOSTIC ONLY
```

Model-input policy: amplitudes (+ quarantined RSSI, §16) are features;
**everything else is excluded from model input**, available for
stratification, calibration, display, and leakage audits. `bssid` measured
from records always overrides `environment_label` claims (the VCET lesson).

## 14. Normalization strategies

- **A. Raw CSI only.** Pros: zero information loss, maximal interpretability,
  strongest publication story for phenomenon existence. Cons: AP gain/rate/
  geometry differences become domain shift; cross-network generalization
  unlikely without conditioning. Verdict: keep raw as the *archived* layer
  always (RawSessionWriter already does), never as the sole model input.
- **B. Per-session normalized CSI.** Pros: removes per-AP gain/offset drift;
  cheap. Cons: can erase stable environmental signatures that aid
  calibration; session-length dependence. Verdict: reasonable default input
  *alongside* raw archives.
- **C. Baseline-relative ΔCSI (present − empty).** Pros: directly expresses
  the sensing phenomenon; cancels static multipath + AP personality;
  matches the pilot's empty-vs-present design. Cons: needs trustworthy empty
  captures per session; doubles acquisition cost. Verdict: strongest
  scientific object; make per-session empties a protocol requirement (§17).
- **D. Amplitude/phase normalized.** Pros: phase carries fine motion info the
  pilot currently discards (`phase_features=False`); scale-invariance.
  Cons: phase is wrap/noise-sensitive; needs the currently-unused `phases`
  path built and validated. Verdict: research track, not baseline input.
- **E. Network-conditioned (representation + context).** Pros: lets one model
  span APs by conditioning instead of pretending uniformity; leakage-auditable
  if context routing is explicit. Cons: complexity; conditioning features can
  *become* the shortcut if miswired. Verdict: the end-state for multi-network
  work — adopt only with §16 safeguards and leave-one-network-out proof.

## 15. Data leakage risks

Threat: SSID/BSSID/channel/RSSI/AP-identity shortcutting presence labels —
especially lethal if presence conditions correlate with sessions or rooms.
Current exposure is narrow but real: **RSSI flows into features (+3 dims,
`feature_extraction.py:162`)** while BSSID/channel/MAC/seq correctly stop at
the envelope. Safeguards: (1) keep all of §13 out of model input except via
explicit, reviewed conditioning (E); (2) quarantine RSSI — ablate it in every
evaluation and require the phenomenon to persist without it; (3) mandate
session- and network-stratified splits (never shuffle pooled frames);
(4) require per-session empties so ΔCSI (§15C) is computable and AP
personality subtracts out; (5) add a leakage probe to the eval harness — a
context-only classifier (BSSID/channel/RSSI → label) whose above-chance
performance fails the experiment, not the model; (6) record `session_id` on
every dataset row (`collector.py` already stores it — extend columns, §19).

## 16. Future experimental implications (RFVISION-011 untouched)

Recommend, without modifying any frozen protocol: per-session `NetworkContext`
capture as a field-work checklist item; per-session empty calibration
captures; repeated sessions per AP before adding APs; cross-AP train/test and
**leave-one-network-out** as the graduation criterion for any presence claim;
multi-AP environments added one variable at a time (same AP model new room →
new AP model same room → hotspot); context-only leakage probes as acceptance
gates. None of this alters v1.3/v1.4/Pilot verdicts — it defines what the
*next* protocol revision must contain to claim generalization.

## 17. Router-dependency gradient

| Component | Current dependency | Fundamental? | Should abstract? | Proposed mechanism |
|---|---|---|---|---|
| Wi-Fi association | build-time SSID (`sdkconfig:418`) | join: yes; baking: no | **yes** | runtime provisioning profile (§19) |
| CSI generation | gateway-ping replies only | stimulus: yes; gateway-ICMP: no | **yes** | `traffic_mode` enum + context |
| Router traffic | AP reply timing shapes rate | timing-as-measurement: yes | record, don't remove | rate stats in `NetworkContext` |
| CSI parser | strict 25-col classic-ESP32 | wire-shape: yes-today | version it | format tag + `CsiSource` backends |
| Timestamps | 32-bit wrap; CSV conflation | API-shaped | **yes** | wrap compensation; contract docs |
| Synchronization | 2 ms/64 policy fails in transport distress | criterion: yes; values: no | **yes** | contextual thresholds (§19) |
| Features | fixed 54-dim geometry; RSSI in-input | geometry: conditional | **yes** | geometry-aware dims; RSSI quarantine |
| ML | (no trained model in scope) — dataset lacks BSSID/channel cols | n/a | preempt | context cols + stratified splits |
| XAI | scores features only, no context | — | extend | context-aware caveats |
| Visualization | provenance display only | — | keep | show `NetworkContext`, never leak it |

## 18. Three architecture options (trade-offs, no winner)

**A — Minimal evolution.** Keep `csi_recv_router`; move SSID/password to a
runtime profile (future firmware rev with reachable provisioning or documented
reflash SOP), move HOME defaults into session profiles, record
`NetworkContext`, require per-session empties. *Validity:* full — removes E1
without touching physics. *Complexity:* low (host-only changes + provisioning
procedure). *HW:* none. *Effect on validated work:* additive only; all
verdicts stand. *Publication:* suffices for single-AP phenomenon claims with
context recorded. *Reproducibility:* high. *Risks:* still one backend; AP
change still needs care. *Migration:* first step of any path.

**B — Source abstraction.** A plus `CsiSource` interface, `OfflineFileSource`,
format-tagged parsers, geometry-aware features. *Validity:* full; enables
backend swaps as controlled variables. *Complexity:* medium (interface +
replay harness + fixtures). *HW:* none required. *Effect:* downstream
untouched by construction; acquisition tests rewritten around fakes.
*Publication:* enables backend-comparison studies. *Reproducibility:* highest
(record→replay determinism). *Risks:* abstraction without a second backend is
speculative — build the interface, defer extra backends. *Migration:* A → B
naturally.

**C — Network-robust sensing.** B plus normalization layer (B/C/D options),
network conditioning (E), leave-one-network-out evaluation, leakage probes.
*Validity:* strongest generalization claims. *Complexity:* high (eval
redesign, calibration discipline, multi-AP field work). *HW:* benefits from —
but does not require — a second AP/backend for contrast. *Effect:* changes
what "passing" means (cross-network, not per-AP). *Publication:* the
generalization story reviewers demand. *Reproducibility:* good if contexts
are complete. *Risks:* conditioning pathways can leak; needs the §15/§16
discipline. *Migration:* A → B → C; do not skip.

## 19. Hardware implications

The **ESP32 + current firmware is sufficient as the initial backend** for a
network-agnostic *downstream* architecture — downstream is already nearly
network-blind (§7 downstream table), and the blockers are provisioning shape
and session discipline, not silicon. Distinguish sharply: network-agnostic
downstream (achieved with software) vs network-independent acquisition
hardware (impossible in principle — every CSI source has *some* RF
personality; the goal is characterized, recorded personality). No purchase
recommended. If contrast hardware is ever wanted, the reason would be
*experimental* (a second backend to test abstraction B), never architectural
rescue. The dormant `PROVIDE_WIFI_CONSOLE_CMD` registration (`sdkconfig:417`)
is a hint for the provisioning redesign: a future firmware rev could expose a
reachable console/serial provisioning path instead of Kconfig baking.

## 20. Minimum architectural change set

- **Required now (host-only, no firmware/protocol/touch):** session-profile
  config replacing HOME code defaults (#5); `NetworkContext` capture +
  per-session checklist (BSSID-from-records overrides claims); RSSI ablation
  discipline; timestamp-wrap compensation in sync consumers; time-based
  (not index-based) drift diagnostics.
- **Required before multi-network research:** reachable ESP provisioning
  (firmware rev or authorized reflash SOP) so rooms can change without
  engineering; per-session empty captures; context columns in datasets;
  contextual sync thresholds.
- **Required before ML:** stratified splitting utilities; context-only
  leakage probe as eval gate; geometry-aware feature dims; documented
  normalization choice (B+C recommended, E gated on proof).
- **Required before publication-quality evaluation:** leave-one-network-out
  results; multi-AP replication; full `NetworkContext` appendix per session;
  raw archives retained (already policy).
- **Optional future:** `CsiSource` second backend; phase-feature path;
  `OfflineFileSource` replay CI; AP-model-stratified calibration.

## 21. Risks and unresolved questions

1. Dual-node transport corruption root (shared USB host? hub? driver
   buffering?) is still **unresolved** — the largest threat to any
   architecture, independent of network.
2. Spontaneous ESP "hangs" (HOME finding #6) need a cause before unattended
   multi-AP field work.
3. Whether 100 Hz gateway-ping generalizes to hotspots (phone ICMP
   throttling? DHCP lease behavior?) is untested — first VCET session must
   measure rate personality before any comparison.
4. RSSI's legitimate role (useful signal vs shortcut) needs the ablation
   study, not an assumption.
5. 62-vs-64 tone geometry across APs/firmware is characterized for one
   backend only.
6. `ts_wifi_us` vs `ts_esp32_us` conflation in the CSV path needs contract
   documentation before a second backend exists.
7. No trained model exists yet — all leakage analysis is preventive.

## 22. Recommended next checkpoint

**Decision checkpoint: provisioning-path selection.** The single blocking
architectural decision is how ESP32s change networks: (i) firmware rev with
reachable runtime provisioning (console/NVS/multi-profile), (ii) authorized
build-time reflash SOP per environment, or (iii) alternate backend. Until
that is decided, multi-network research cannot begin regardless of downstream
readiness. Recommended inputs to that decision: dual-transport root-cause
resolution (risk #1, it dominates all timelines), a provisioning prototype
assessment against the §4-E criteria, and adoption of the §20 "required now"
host-only items — all without touching frozen artifacts. **Nothing in this
section is authorized work; it describes the decision to be made.**

## 23. Verification (no-code-change requirement)

```text
$ git status --short   # (read-only inspection)
 M tests/unit/test_live_provider.py   # pre-authorized Option B work, pre-existing
 M web/source.py                      # pre-authorized Option B work, pre-existing
$ git log --oneline -1
d1f12a5 feat: add validated two-node CSI acquisition foundation
```

No source/firmware/config modifications, no rebuilds, no flashes, no resets,
no esptool, no out-of-stack serial use, no commits, no pushes, no
experiments, no threshold/protocol/AP changes. Analysis produced zero
repository files (three subagent traces were ephemeral); this report is the
only artifact, as required by §24. Firmware SHA untouched and previously
verified (`0a490737…dd`). All frozen documents and historical captures
unmodified; all prior verdicts stand.
