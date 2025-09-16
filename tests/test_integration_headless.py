from __future__ import annotations

import os
import platform
import shutil
import sqlite3
import subprocess
from pathlib import Path

import pytest

pytestmark = pytest.mark.integration

REPO_ROOT = Path(__file__).resolve().parent.parent
HEADLESS_SCRIPT = REPO_ROOT / "examples" / "run_headless_test.py"
REQUIRED_BINARIES = ("dbus-run-session", "xvfb-run", "accerciser")


def _ensure_environment() -> None:
    if platform.system() != "Linux":
        pytest.skip("integration test requires Linux")

    missing = [tool for tool in REQUIRED_BINARIES if shutil.which(tool) is None]
    if missing:
        pytest.skip(f"missing required binaries: {', '.join(missing)}")

    pytest.importorskip("pyatspi")
    gi = pytest.importorskip("gi")
    try:
        gi.require_version("Gtk", "3.0")
    except ValueError as exc:
        pytest.skip(f"GTK 3 not available: {exc}")


def test_headless_logger_captures_text(tmp_path: Path) -> None:
    _ensure_environment()

    db_path = tmp_path / "integration.db"
    log_path = tmp_path / "headless.log"

    env = os.environ.copy()
    # Ensure the installed package under src/ is importable when running the script
    env["PYTHONPATH"] = os.pathsep.join(
        [str(REPO_ROOT / "src"), env.get("PYTHONPATH", "")]
    ).rstrip(os.pathsep)

    result = subprocess.run(
        [
            "python3",
            str(HEADLESS_SCRIPT),
            "--db",
            str(db_path),
            "--log",
            str(log_path),
        ],
        env=env,
        cwd=str(REPO_ROOT),
        check=False,
    )

    if result.returncode != 0:
        log_excerpt = log_path.read_text() if log_path.exists() else "<missing>"
        pytest.fail(
            f"headless harness exited with {result.returncode}\nLog output:\n{log_excerpt}"
        )

    assert db_path.exists(), "expected SQLite log file to be created"

    with sqlite3.connect(db_path) as conn:
        snapshot_rows = conn.execute(
            "SELECT text_content, text_hash FROM text_snapshots"
        ).fetchall()
        assert snapshot_rows, "no text snapshots persisted"
        combined_text = " ".join((text or "") for text, _ in snapshot_rows)
        assert "ColdWatch" in combined_text, "expected demo text to be captured"
        assert any(hash_value for _, hash_value in snapshot_rows)

        registry_rows = conn.execute(
            "SELECT is_text_widget, last_text_hash FROM object_registry"
        ).fetchall()
        assert registry_rows, "registry table should contain entries"
        assert any(row[0] for row in registry_rows), "missing text widget flags"
        assert any(row[1] for row in registry_rows), "missing registry hash data"

        event_count = conn.execute("SELECT COUNT(*) FROM events").fetchone()[0]
        assert event_count > 0, "no AT-SPI events recorded"

    assert log_path.exists(), "logger output log not found"

    artifact_dir = os.environ.get("COLDWATCH_INTEGRATION_ARTIFACTS")
    if artifact_dir:
        target = Path(artifact_dir)
        target.mkdir(parents=True, exist_ok=True)
        shutil.copy2(db_path, target / db_path.name)
        shutil.copy2(log_path, target / log_path.name)
