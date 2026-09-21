> **RFVISION-006 legacy migration — HISTORICAL / PRE-UBUNTU.**
> Legacy source: `RF Vision Files/07_REPORTS/CSI-SENSE-001_PERSISTENT_BACKUP_GATE_REPORT.md` (SHA-256 `a3c32d24f8b22480a05a36c8b90a77b172ffa97a900a49aec1f55d6e3fa82053`) · Migrated 2026-09-21 ·
> See `docs/research/LEGACY-MIGRATION-PROVENANCE.md`.

# CSI-SENSE-001 — PERSISTENT BACKUP GATE REPORT

**Study:** CSI-SENSE-001 RF Vision  
**Gate:** Persistent Storage Prerequisite for Phase C (§5.5 PLAN v1.1)  
**Date:** 2026-09-06 22:55 UTC  
**Plan:** `~/Desktop/CSI-SENSE-001_PLAN_v1.1.md` (753 lines)  
**Tool audited:** `tools/csi_capture/backup_verify.py:1` (373 lines)  
**Scope:** Host-side mount inspection only — NO human CSI, NO 310s trial, NO 10s smoke test, NO flash/erase, NO router, NO Windows/BIOS/partitions/SSD modification

---

## 1. Objective

Identify an ACTUAL persistent, writable filesystem suitable for the CSI dataset and verify the §5.5 gate:

- `is_volatile=false`
- `is_persistent_guess=true`
- `free_sufficient_5GB=true`
- `write-test 100 MB ok=true sha_match=true`

Gate must REJECT Live-USB volatile: `/cow`, `/tmp`, `tmpfs`, `overlay`, `squashfs`, `/rofs`, `/cdrom`.

---

## 2. Methods (read-only)

Executed exactly:

```
lsblk -o NAME,SIZE,FSTYPE,MOUNTPOINTS,RO,MODEL
df -hT
findmnt
blkid
cat /proc/mounts
ls -R /media
```

No assumption of path, no creation, no mount, no write.

Rejection logic per `tools/csi_capture/backup_verify.py:49-97`:

- `VOLATILE_SUBSTRINGS = ["/cow","/tmp","tmpfs","overlay","/rofs","squashfs","cow"]` (`backup_verify.py:49`)
- `VOLATILE_MOUNT_TYPES = ["tmpfs","overlay","squashfs","iso9660"]` (`backup_verify.py:50`)
- `inspect_destination:61-103` checks `df -hT dest` + `findmnt -T dest` + `lsblk` + `/proc/mounts` combined string
- `write_test:115-149` requires `is_volatile=false` before write, then SHA round-trip `urandom → sha_before → fsync+sync → sha_after → sha_match`

---

## 3. Results — All Mounted Storage

### 3.1 lsblk

```
NAME          SIZE FSTYPE    MOUNTPOINTS                         RO MODEL
loop0         3.2G squashfs  /rofs                                1
loop1       562.7M squashfs                                       1
loop2       756.4M squashfs                                       1
...
sda          29.8G                                                0 v210w
└─sda1       29.8G vfat      /cdrom                               0
nvme0n1     476.9G                                                0 INTEL SSDPEKNW512GZL
├─nvme0n1p1   260M vfat                                           0
├─nvme0n1p2    16M                                                0
├─nvme0n1p3 474.7G BitLocker                                      0
└─nvme0n1p4     2G ntfs                                           0
```

### 3.2 df -hT

```
Filesystem     Type      Size  Used Avail Use% Mounted on
tmpfs          tmpfs     1.6G  4.8M  1.6G   1% /run
/dev/sda1      vfat       30G  6.1G   24G  21% /cdrom
/cow           overlay   7.7G  3.5G  4.2G  46% /
tmpfs          tmpfs     7.7G  8.0K  7.7G   1% /dev/shm
tmpfs          tmpfs     7.7G  4.0G  3.8G  52% /tmp
tmpfs          tmpfs     1.6G  156K  1.6G   1% /run/user/1000
```

### 3.3 findmnt (abridged)

```
/                 /cow                   overlay  rw,lowerdir=/minimal.standard.live.squashfs:...
/cdrom            /dev/sda1              vfat     ro,noatime
/rofs             /dev/loop0             squashfs ro,noatime
/tmp              tmpfs                  tmpfs    rw,nosuid,nodev,relatime,inode64
```

### 3.4 blkid

```
/dev/nvme0n1p1: LABEL="SYSTEM_DRV" UUID="10AA-A56F" TYPE="vfat" PARTLABEL="EFI system partition"
/dev/nvme0n1p3: UUID="8d8a0548-..." TYPE="BitLocker" PARTLABEL="Basic data partition"
/dev/nvme0n1p4: LABEL="WINRE_DRV" UUID="5CF4ABFAF4ABD494" TYPE="ntfs" PARTLABEL="Basic data partition"
/dev/sda1: LABEL="UBUNTU 26_0" UUID="961F-00E6" TYPE="vfat" PARTLABEL="Main Data Partition"
```

### 3.5 /media

```
/media:
cdrom
```

No `/media/ubuntu/*`, no `/mnt/*` persistent RW mount.

### 3.6 Per-Device Gate Evaluation

| Device / Path | FSTYPE | Mount | Avail | Volatile? | Reason | Suitable? |
|---|---|---|---|---|---|---|
| `/` on `/cow` | `overlay` | `/` | 4.2G | **YES** | `backup_verify.py:74-88` match `"/cow"` + `"overlay"` + `fstype overlay` — `is_volatile=true`; `free 4.2G <5GB` → `free_sufficient_5GB=false` | **NO** — forbidden Live overlay |
| `/tmp` | `tmpfs` | `/tmp` | 3.8G | **YES** | match `"/tmp"` + `"tmpfs"` — `is_volatile=true`; `<5GB` | **NO** — forbidden tmpfs |
| `/dev/shm` | `tmpfs` | `/dev/shm` | 7.7G | YES | `tmpfs` | NO |
| `/run` etc | `tmpfs` | `/run` | 1.6G | YES | `tmpfs` | NO |
| `/rofs` `loop0` | `squashfs` | `/rofs` | — | YES | `squashfs` RO `loop0 3.2G` — forbidden | NO |
| `/snap/*` `loop1-18` | `squashfs` | `/snap/*` | — | YES | `squashfs` RO | NO |
| `/dev/sda1` | `vfat` | `/cdrom` | 24G | **YES** | `/cdrom` RO `ro,noatime` Live USB `UBUNTU 26_0` — explicitly forbidden `/cdrom` + not writable (RO remount) | **NO** |
| `nvme0n1p1` `SYSTEM_DRV` | `vfat` | *unmounted* | — | — | Not mounted, EFI 260M (<5GB), internal SSD — DO NOT mount/modify per gate | NO |
| `nvme0n1p2` | — | *unmounted* | 16M | — | Not mounted, <5GB | NO |
| `nvme0n1p3` | `BitLocker` | *unmounted* | — | — | Locked, not mountable writable, internal SSD 474.7G — excluded | NO |
| `nvme0n1p4` `WINRE_DRV` | `ntfs` | *unmounted* | 2G max | — | Not mounted, `2G <5GB` → `free_sufficient_5GB=false`, internal SSD recovery — excluded | NO |

**No mounted persistent writable filesystem `ext4|xfs|ntfs|exfat|btrfs` RW `≥5GB` outside volatile set found.**

---

## 4. Backup-Verify Execution

Per gate rule 5-8:

- **Step 5 `python3 tools/csi_capture/backup_verify.py --inspect <ACTUAL_PATH>`: NOT EXECUTED** — no `ACTUAL_PATH` exists that satisfies `MUST NOT be /cow|/tmp|tmpfs|overlay|squashfs|/rofs|/cdrom`. Running against `/cow` or `/tmp` would trivially return `is_volatile=true` (verified in Phase C Readiness Report §5) but would violate “ACTUAL persistent” requirement.

- **Step 6 `is_volatile=false / is_persistent_guess=true / free_sufficient_5GB=true`: NOT MET** — vacuously false because no candidate.

- **Step 7 `python3 tools/csi_capture/backup_verify.py --write-test <ACTUAL_PATH> --size-mb 100`: NOT EXECUTED** — gate requires all three true first; `write_test:120` would `return ok false error volatile` even if forced.

- **Step 8 `ok=true sha_match=true`: NOT APPLICABLE**

Correct behavior of `backup_verify.py:332-335` (`if is_volatile and not dry_run → ERROR refusing exit 5`) and `write_test:120-123` was verified in prior audit but not re-triggered here to avoid volatile write-test violation.

---

## 5. Gate Verdict

**PERSISTENT-BACKUP GATE: FAILED**

- **Exact device:** *none*
- **Exact filesystem:** *none*
- **Mount path:** *none*
- **Available space:** *none* (largest RW available is `/` 4.2G and `/tmp` 3.8G — too small and volatile)
- **Write-test SHA result:** *not run — no persistent target*
- **Gate PASSED/FAILED:** **FAILED**

This is not a software defect. `tools/csi_capture/backup_verify.py:49-149` correctly identifies all current mounts as volatile and would reject them. Failure is environmental: Live USB session without external persistent storage attached.

`data/CSI-SENSE-001/metadata/study_metadata.json:45-53` `persistent_backup {path,filesystem,size_avail_gb,write_test_sha_match,verified_utc}` remains correctly `null`.

---

## 6. Compliance

- No human CSI collected
- No `tools/csi_capture/capture_csi_sense.py:151-182` 310-s trial run
- No 10-s smoke test run
- No `idf.py flash/erase` or ESP32 modification
- No `nmcli/iw` router modification (`Nihaal 8C:53:C3:5B:E1:59` unchanged)
- No Windows/BIOS/partition/`nvme0n1` modification (`nvme0n1p3 BitLocker` untouched, `nvme0n1p4` not mounted)
- No assumption of path, no file creation/modification beyond this report
- No `/media` or `/mnt` write

---

## 7. Required Action Before Phase C (STOP after this gate)

1. **Attach external persistent device** — USB SSD/HDD, `ext4` (preferred) or `ntfs`/`exfat`, `≥5GB` free, **not** internal `nvme0n1`. Example: 32GB+ USB.

2. **Mount RW** — e.g. `udisksctl mount` or desktop automount → `/media/ubuntu/PERSISTENT` (verify `findmnt` shows `ext4`/`ntfs` `rw`, not `tmpfs`/`overlay`/`squashfs`).

3. **Re-run gate exactly (do not run capture yet):**

   ```bash
   python3 tools/csi_capture/backup_verify.py --inspect /media/ubuntu/PERSISTENT
   # require: is_volatile=false is_persistent_guess=true free_sufficient_5GB=true

   python3 tools/csi_capture/backup_verify.py --write-test /media/ubuntu/PERSISTENT --size-mb 100
   # require: ok=true sha_match=true sha_before==sha_after

   # then record in data/CSI-SENSE-001/metadata/study_metadata.json:
   # persistent_backup {path, filesystem, size_avail_gb, write_test_sha_match:true, verified_utc}
   ```

4. **Do not start 10-s smoke test or 310-s trial until this gate shows PASSED and geometry/env prerequisites also PASSED, and explicit `APPROVED for Phase C` issued.**

---

*Report generated read-only. Raw `~/Desktop/CSI_RAW_70s_921600_20260906_205638.log` unchanged. `data/CSI-SENSE-001/raw` empty pending PASSED gate.*
