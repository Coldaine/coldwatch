# CI Overview and Next Steps

## What’s In Place
- Reusable pre-commit workflow: `.github/workflows/precommit.yml` runs `uvx pre-commit run --all-files` on Ubuntu with Python 3.10 and caches both uv and pre-commit downloads.
- Push workflow (`ci-commit.yml`): lint matrix (Black + Ruff) plus a Python 3.10–3.12 unit-test matrix that publishes `coverage.xml` from 3.12. An optional integration job (guarded by `vars.RUN_ATSPI_TESTS`) provisions AT-SPI dependencies and executes `pytest -m integration`, archiving the collected SQLite/log artifacts.
- PR workflow (`ci-pr.yml`): mirrors the unit matrix with coverage on 3.12, uploads the report, and exposes the same optional integration job for first-party PRs when the repo variable is enabled.
- Tooling uses `uv`/`uvx` for ephemeral installs; `pytest` markers and hooks live in `pyproject.toml` and `.pre-commit-config.yaml`.

## Live Accessibility Regression Coverage
- `tests/test_integration_headless.py` drives the headless harness. It shells into `dbus-run-session`/`xvfb-run`, launches `coldwatch.cli run`, and feeds the GTK mock app. The test asserts that:
  - `text_snapshots` contains AT-SPI text that references “ColdWatch”.
  - `object_registry` flags the widgets as text entries and stores hashes.
  - `events` rows exist, proving we saw live bus activity.
- Artifacts (SQLite DB + logger output) are copied into `$COLDWATCH_INTEGRATION_ARTIFACTS` when set, allowing the CI job to upload them.
- Environment guards skip the test on non-Linux hosts or when `pyatspi`, `Gtk 3`, `dbus-run-session`, `xvfb-run`, or `accerciser` are unavailable, so developers without AT-SPI tooling are not blocked.

## Remaining Enhancements
- **Nightly deep run**: add a scheduled workflow for a longer soak (e.g., 60-second capture) to catch intermittent DBus failures.
- **Secret scanning**: add `gitleaks` or enable GitHub Advanced Security to prevent accidental leakage of captured accessibility text.
- **Docs**: expand README (or add `docs/testing.md`) with guided troubleshooting for the integration harness and artifact inspection tips.

## Hooks & Local Workflow
- `.pre-commit-config.yaml` runs Ruff (with autofix) and Black on commit, then executes `uvx pytest -m "not integration"`. On push it triggers `uvx pytest -m integration` so live coverage mirrors CI.
- Developers can run `uvx pytest -m "not integration"` for fast feedback and `uvx pytest -m integration` on Linux with AT-SPI packages installed.
- For manual desktop validation, run `python3 export/accessibility_logger.py` then `python3 export/mock_app.py`.
