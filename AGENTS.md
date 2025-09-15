# Repository Guidelines

## Project Structure & Module Organization
- `export/` — Active Python snapshot for ColdWatch:
  - `accessibility_logger.py` (AT‑SPI logger, writes `accessibility_log.db`)
  - `run_test.py` (headless E2E harness; dbus + Xvfb)
  - `mock_app.py` (GTK3 demo to generate text changes)
  - `analyze_data.py` (SQLite analysis/summary)
- `orig/` — Read‑only source copies and utilities (do not modify; use for reference only).
- Top‑level docs: `README.md`, `PHASE_2_PLAN.md`, inventories and references.

## Build, Test, and Development Commands
- Run logger (desktop session): `python3 export/accessibility_logger.py`
- Headless E2E test: `python3 export/run_test.py`
  - Uses `dbus-run-session` and `xvfb-run`; ensures the logger and GTK app share a bus.
- Analyze captured data: `python3 export/analyze_data.py`
Notes: Ensure `pyatspi`, `gi` (GTK3), and `loguru` are installed; tools: `dbus-run-session`, `xvfb-run`, `accerciser`.

## Coding Style & Naming Conventions
- Python 3.x; 4‑space indentation; UTF‑8; prefer type hints.
- Files and functions: `snake_case`; classes: `CamelCase`; constants: `UPPER_SNAKE`.
- Keep modules focused; avoid side effects at import time.
- Logging: use `loguru` as in `accessibility_logger.py`; avoid print except in scripts.
- Optional tools if present: `black` (88 cols), `ruff`, `isort`.

## Testing Guidelines
- Primary path is integration: `python3 export/run_test.py`.
  - Verifies DB creation and expected text snapshots; event counts may be environment‑sensitive under Xvfb.
- Manual desktop check: run logger, then `mock_app.py`, confirm snapshots and events recorded.
- If adding unit tests later, place under `tests/` mirroring module names (e.g., `tests/test_accessibility_logger.py`).

## Commit & Pull Request Guidelines
- Use Conventional Commits: `feat:`, `fix:`, `chore:`, `docs:`, `refactor:`, `test:`.
- Scope PRs narrowly; do not modify `orig/` contents.
- PR checklist:
  - Clear summary and rationale; link issues.
  - Repro steps and commands run (paste key output from `run_test.py`/`analyze_data.py`).
  - Note environment (desktop vs. headless) and any dependencies.

## Agent‑Specific Instructions
- Treat `orig/` as immutable; implement changes under `export/` unless Phase 2 explicitly restructures.
- Prefer small, reviewable patches; preserve runtime behavior when touching the logger.
- When scripts invoke external tools, keep commands explicit and portable; surface stderr in logs.

## Tooling via uv
- First-time setup (one command): `make setup` or `sh scripts/bootstrap.sh`.
- Use uv to run dev tools without managing a venv:
  - `uvx pre-commit install` then `uvx pre-commit run --all-files`
  - `uvx ruff check --fix .` and `uvx black .`
- Pre-commit hooks are configured in `.pre-commit-config.yaml` (Ruff then Black). Ruff/Black settings live in `pyproject.toml`. Lint excludes `orig/`.

## Security & Configuration Tips
- AT‑SPI requires a user session; set `XDG_RUNTIME_DIR` appropriately. Avoid running as root.
- Database path defaults to `accessibility_log.db` in CWD; allow overriding via parameters where practical.
