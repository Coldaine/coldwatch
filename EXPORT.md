ColdWatch Export Guide (No History)

You asked for a from-scratch export without Git history. This folder contains an export-ready snapshot you can copy elsewhere and rename to `coldwatch`.

Minimal export (no packaging):
1) Copy the folder:
   cp -R staging/coldwatch/export ~/code/coldwatch
2) Initialize Git (optional):
   cd ~/code/coldwatch && git init && git add . && git commit -m "ColdWatch v0.0.0 snapshot"
3) Run locally (Linux desktop with AT-SPI):
   python3 accessibility_logger.py

Headless E2E test (requires dbus, xvfb, accerciser, GTK):
   python3 run_test.py

Analyze captured DB:
   python3 analyze_data.py

Notes:
- This export preserves the original single-file logger and helper scripts; no refactor.
- Next step (Phase 2) would split into a proper Python package/CLI.

