from __future__ import annotations

import signal
import sqlite3
import sys
from contextlib import suppress

from loguru import logger

from . import db, privacy, scanner
from .types import RunConfig


class AccessibilityLogger:
    """High-level orchestration for the ColdWatch logger."""

    def __init__(self, cfg: RunConfig) -> None:
        self.cfg = cfg
        self._state = scanner.ScannerState()
        self._configure_logging()

    def run(self) -> int:
        try:
            db.initialize(self.cfg.db_path)
        except sqlite3.Error as exc:  # pragma: no cover - sqlite failures are rare
            logger.error("Failed to initialize database: {}", exc)
            return 3

        if not scanner.wait_for_registry(self.cfg.wait_for_atspi, self.cfg.interval):
            logger.error(
                "AT-SPI registry unavailable after {:.1f}s", self.cfg.wait_for_atspi
            )
            return 2

        with db.db(self.cfg.db_path) as conn:
            if self.cfg.once:
                logger.info("🔍 Performing single tree scan")
                scanner.walk_tree(conn, self.cfg, self._state)
                return 0

            logger.info("🚀 Starting ColdWatch logger")

            stop_requested = False

            def _request_stop(signum: int, frame) -> None:  # type: ignore[misc]
                nonlocal stop_requested
                stop_requested = True
                logger.info(
                    "Received signal %s, stopping...", signal.Signals(signum).name
                )
                with suppress(Exception):
                    import pyatspi

                    pyatspi.Registry.stop()

            original_int = signal.getsignal(signal.SIGINT)
            original_term = signal.getsignal(signal.SIGTERM)
            signal.signal(signal.SIGINT, _request_stop)
            signal.signal(signal.SIGTERM, _request_stop)
            try:
                scanner.walk_tree(conn, self.cfg, self._state)
                scanner.subscribe_events(conn, self.cfg, self._state)
            finally:
                signal.signal(signal.SIGINT, original_int)
                signal.signal(signal.SIGTERM, original_term)

            return 0 if not stop_requested else 0

    def _configure_logging(self) -> None:
        logger.remove()
        logger.add(sys.stderr, level=self.cfg.log_level.upper(), enqueue=True)


def run_logger(cfg: RunConfig | None = None) -> int:
    config = cfg or RunConfig()
    try:
        import pyatspi  # noqa: F401  # Ensure the dependency is present
    except Exception as exc:  # pragma: no cover - depends on environment
        logger.error("AT-SPI bindings unavailable: {}", exc)
        return 2

    if not privacy.should_capture_text(config):
        logger.warning("Text capture disabled; only metadata will be stored.")

    logger_instance = AccessibilityLogger(config)
    try:
        return logger_instance.run()
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        return 0
    except sqlite3.Error as exc:  # pragma: no cover - handled above, fallback safety
        logger.error("Database error: {}", exc)
        return 3
