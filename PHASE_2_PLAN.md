# ColdWatch Extraction — Phase 2 Plan (Ready)

Status: Ready to execute
Source: Derived from PLAN_coldwatch.md at repo root

Context
- Phase 1 is complete. Staging is available under `staging/coldwatch/` with:
  - `orig/` verbatim sources
  - `export/` copy-ready snapshot for from-scratch start
  - `INVENTORY.md`, `SUMMARIES.md`, `REFERENCES.md`, `DRY_RUN_PATCH.txt`, `EXPORT.md`

Objective
- Perform the actual refactor and packaging in a new repo named `coldwatch`, using the staged files as inputs. No history required.

Tasks
- Repository bootstrap (new repo):
  - Create `coldwatch/` repo; `git init` (no history).
  - Copy contents from `staging/coldwatch/export/` as seed.
  - Add `pyproject.toml` (PEP 621; Python >= 3.10) and basic tooling (ruff/black) with pre-commit hooks.
- Package structure:
  - Create `src/coldwatch/{cli.py, core.py, db.py, scanner.py, privacy.py, types.py}`.
  - Split logic from `accessibility_logger.py` into `core`, `db`, `scanner`; keep behavior identical initially.
- CLI (`coldwatch`):
  - Subcommands: `run`, `scan`, `analyze`.
  - Flags: `--db`, `--log-level`, `--interval`, include/exclude app/roles, `--capture-content` (opt-in), `--jsonl`, `--wait-for-atspi`.
  - Exit codes: 0 ok; 2 AT‑SPI unavailable; 3 DB init; 4 bad args.
- Privacy defaults:
  - Default metadata-only (do not persist `text_content`).
  - Always exclude password/secret roles regardless of flags.
  - Optional redaction heuristics when capture is enabled.
- Persistence:
  - Move schema creation into `db.py`; keep current tables and dedupe by `text_hash`.
  - Add JSONL emitter as optional sink.
- Testing:
  - Unit tests for db schema ops, dedupe, privacy filters, CLI arg parsing.
  - Optional integration with Xvfb + dbus + at‑spi2‑core using `examples/mock_app.py`.
- Docs:
  - README (quickstart, dependencies, privacy stance, CLI usage).
  - PRIVACY.md, TROUBLESHOOTING.md.
  - Example scripts: `examples/mock_app.py`, `examples/analyze_data.py`.
- CI:
  - Lint + unit tests.
  - Optional job matrix enabling AT‑SPI integration on Linux.
  - Release:
  - Tag v0.1.0 and prepare a GitHub Release; PyPI optional later.

ColdVox follow-up (after ColdWatch exists)
- Remove `accessibility-logger/` from ColdVox repo.
- Update ColdVox README to link to ColdWatch.
- Add CHANGELOG entry noting the extraction.

Inputs from staging
- `orig/` sources are authoritative; use them to ensure behavior parity.
- `INVENTORY.md`, `SUMMARIES.md`, and `REFERENCES.md` accelerate safe refactor.

Ready signal
- This plan is marked Ready. Begin Phase 2 work in the new repo using the `export/` snapshot.

Tooling & package management (uv)
- Use uv to manage dev tools and reproducible execution without pinning a venv to the repo.
  - One-shot runners: `uvx pre-commit install`, `uvx pre-commit run --all-files`, `uvx ruff check --fix .`, `uvx black .`
  - For a local environment: `uv venv && source .venv/bin/activate && uv pip install -e .[dev]` (once packaging lands)
- Pre-commit should run Ruff (autofix) then Black. Configure Ruff with `target-version = "py310"`, `line-length = 88`, select `E,F,B,UP,I`, and ignore `E501` to defer line length to Black. Exclude `orig/` from linting.
