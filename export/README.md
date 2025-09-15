ColdWatch (export snapshot)

This is an export-ready snapshot of the AT-SPI accessibility logger. Copy this folder elsewhere and rename it to `coldwatch` to start from scratch.

What’s included
- accessibility_logger.py — AT-SPI event and text logger storing to SQLite
- run_test.py — Headless end-to-end test harness (xvfb + dbus)
- mock_app.py — GTK3 mock app that changes text to generate events
- analyze_data.py — Quick analysis of the captured SQLite DB

Quickstart (desktop session)
- python3 accessibility_logger.py

End-to-end test (headless)
- python3 run_test.py

Analyze
- python3 analyze_data.py

Dependencies (system/user)
- Python: pyatspi, loguru, gi (GTK3), pandas (optional for analysis)
- Tools: dbus-run-session, xvfb-run, accerciser (test harness)

Next steps (optional)
- Refactor into a package (src/coldwatch), add CLI, tests and CI.

