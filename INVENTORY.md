ColdWatch Extraction — Phase 1 Inventory

Scope: Mechanical snapshot of in-repo AT-SPI logger sources with no logic changes.

Source files captured from `accessibility-logger/`:
- accessibility_logger.py (13099 bytes)
- run_test.py (4057 bytes)
- mock_app.py (1515 bytes)
- analyze_data.py (2071 bytes)
- test-features.py (13895 bytes)

Notes:
- These are verbatim copies placed under `staging/coldwatch/orig/`.
- Database files, logs, and other generated artifacts are intentionally excluded.
- Dependencies referenced by these files (non-exhaustive): pyatspi, loguru, sqlite3, gi/GTK3, pandas, dbus-run-session, xvfb, accerciser.

