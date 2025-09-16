from __future__ import annotations

import argparse
import sys

from loguru import logger

from .analyze import summarize_db
from .core import run_logger
from .types import RunConfig


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="coldwatch")
    sub = parser.add_subparsers(dest="command", required=True)

    run_cmd = sub.add_parser("run", help="Capture accessibility events")
    run_cmd.add_argument("--db", default="accessibility_log.db")
    run_cmd.add_argument(
        "--once", action="store_true", help="Perform a single scan and exit"
    )
    run_cmd.add_argument("--log-level", default="INFO")
    run_cmd.add_argument(
        "--interval", type=float, default=0.5, help="Rescan interval in seconds"
    )
    run_cmd.add_argument(
        "--wait-for-atspi",
        type=float,
        default=10.0,
        help="Seconds to wait for the AT-SPI bus",
    )
    run_cmd.add_argument(
        "--include",
        action="append",
        dest="include_apps",
        help="Limit logging to these application names",
    )
    run_cmd.add_argument(
        "--exclude",
        action="append",
        dest="exclude_apps",
        help="Skip these application names",
    )
    run_cmd.add_argument(
        "--include-role",
        action="append",
        dest="include_roles",
        help="Limit logging to these roles",
    )
    run_cmd.add_argument(
        "--exclude-role",
        action="append",
        dest="exclude_roles",
        help="Skip these roles",
    )
    run_cmd.add_argument(
        "--no-text",
        action="store_true",
        help="Do not persist text content (metadata only)",
    )

    analyze_cmd = sub.add_parser("analyze", help="Summarize a log database")
    analyze_cmd.add_argument("db", nargs="?", default="accessibility_log.db")

    return parser


def _config_from_args(ns: argparse.Namespace) -> RunConfig:
    return RunConfig(
        db_path=ns.db,
        once=ns.once,
        log_level=ns.log_level,
        interval=ns.interval,
        wait_for_atspi=ns.wait_for_atspi,
        include_apps=tuple(ns.include_apps or ()),
        exclude_apps=tuple(ns.exclude_apps or ()),
        include_roles=tuple(ns.include_roles or ()),
        exclude_roles=tuple(ns.exclude_roles or ()),
        capture_text=not ns.no_text,
    )


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "run":
        cfg = _config_from_args(args)
        return run_logger(cfg)

    if args.command == "analyze":
        summarize_db(args.db)
        return 0

    logger.error("Unknown command: {}", args.command)
    return 4


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
