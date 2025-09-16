#!/usr/bin/env python3
"""Headless smoke test combining the logger and mock app."""

from __future__ import annotations

import argparse
import os
import shlex
import subprocess
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MOCK_APP = ROOT / "examples" / "mock_app.py"


def _script(db_path: Path, log_path: Path) -> str:
    return textwrap.dedent(
        f"""
        set -e
        export XDG_RUNTIME_DIR=${{XDG_RUNTIME_DIR:-/run/user/$(id -u)}}
        accerciser >/dev/null 2>&1 &
        ACC_PID=$!
        sleep 2
        python3 -m coldwatch.cli run --db {shlex.quote(str(db_path))} > {shlex.quote(str(log_path))} 2>&1 &
        LOGGER_PID=$!
        sleep 5
        xvfb-run --auto-servernum python3 {shlex.quote(str(MOCK_APP))}
        kill $LOGGER_PID || true
        wait $LOGGER_PID 2>/dev/null || true
        kill $ACC_PID 2>/dev/null || true
        """
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", default="accessibility_log.db")
    parser.add_argument("--log", default="logger.log")
    args = parser.parse_args(argv)

    db_path = Path(args.db).resolve()
    log_path = Path(args.log).resolve()

    cmd = ["dbus-run-session", "bash", "-lc", _script(db_path, log_path)]
    env = os.environ.copy()
    env.setdefault("XDG_RUNTIME_DIR", f"/run/user/{os.getuid()}")

    result = subprocess.run(cmd, check=False, env=env, cwd=str(ROOT))
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
