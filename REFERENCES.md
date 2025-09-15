ColdWatch Extraction — Phase 1 References

Primary runtime deps (Python):
- pyatspi: AT-SPI2 Python bindings for accessibility tree events and queries
- loguru: Logging with rotation and structured console output
- sqlite3: Standard library database for events and text snapshots
- gi/GTK3 (PyGObject): Required for the GTK mock app
- threading, hashlib, json, datetime, time: Standard library

Test/runtime tools observed in scripts:
- dbus-run-session: Isolated D-Bus session for coordinated logger/mock-app
- xvfb-run: Headless X server for GTK UI in CI-like environments
- accerciser: Ensures the AT-SPI bus is active in test script

Analysis:
- pandas: Used by analyze_data.py to optionally inspect/format data (import present)

Artifacts intentionally excluded:
- accessibility_log.db (SQLite DB) and generated logs

