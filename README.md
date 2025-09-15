ColdWatch Staging (Phase 1)

This folder contains a mechanical snapshot of the in-repo AT-SPI accessibility logger to prepare for extraction into a standalone app named ColdWatch.

Contents:
- orig/: Verbatim copies of the current Python sources (no edits)
- INVENTORY.md: File list and sizes
- SUMMARIES.md: One-line descriptions
- REFERENCES.md: Dependencies and tools referenced
- DRY_RUN_PATCH.txt: Proposed file move/rename plan for extraction

Rules for Phase 1:
- Do not alter logic or behavior.
- Do not restructure modules beyond copying into `orig/`.
- No packaging or CLI changes yet.

Quick bootstrap (don’t forget anything)
- One-liner with Make: `make setup` (installs dev tools and hooks)
- Or script: `sh scripts/bootstrap.sh`

Developer setup (tools via uv)
- Use uv to run dev tooling without a virtualenv:
  - Install pre-commit hooks: `uvx pre-commit install`
  - Run hooks on all files: `uvx pre-commit run --all-files`
  - Ad-hoc lint/format: `uvx ruff check --fix .` and `uvx black .`
- Alternatively, create a local venv and install tools:
  - `uv venv && source .venv/bin/activate`
  - `uv pip install pre-commit ruff black`
  - `pre-commit install && pre-commit run --all-files`
 - Dev extra (single install): `uv pip install -e .[dev]`

Pre-commit configuration
- Hooks: Ruff (lint, autofix) and Black (format).
- Config files: `.pre-commit-config.yaml`, `pyproject.toml` (Ruff/Black settings).
- Lint scope excludes `orig/`; Black/line length is 88 to match Ruff.
