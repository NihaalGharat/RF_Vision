# docs/reference — upstream files kept for study (NOT built)

| File | Source | Purpose |
|---|---|---|
| `csi_data_read_parse.py` | esp-csi tools | Serial→CSV/amp/phase reference (AGC-index quirk on legacy frames noted in WIRE_FORMATS) |
| `requirements.txt` | esp-csi tools | Host-tool pins, reference |
| `csi_send_app_main.c` / `csi_recv_app_main.c` | esp-csi get-started | Two-board ESP-NOW variant + gain-comp reference |
| `esp32_receiver.ino` + `README.md` | Human-Sensing firmware | Alt 2-board Arduino receiver study (NOT default) |
| `example_csi.csv` | CSI-Tool python_utils | 128/384-B legacy format specimen |
| `human_sensing_requirements.txt` | Human-Sensing | Original dependency floors, reference |

Nothing here is imported, built, or shipped. Canonical code lives in the
top-level packages; canonical specs in `csi/formats/WIRE_FORMATS.md`.
