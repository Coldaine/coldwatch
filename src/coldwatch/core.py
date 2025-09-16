from __future__ import annotations

import signal
import sqlite3
import sys
from contextlib import suppress

from loguru import logger

from . import db, privacy, scanner
from .logging_config import setup_logging, get_logger, log_exception, log_database_operation
from .types import RunConfig


class AccessibilityLogger:
    """High-level orchestration for the ColdWatch logger."""

    def __init__(self, cfg: RunConfig) -> None:
        self.cfg = cfg
        self._state = scanner.ScannerState()
        self._configure_logging()
        self._app_logger = get_logger("core")

    def run(self) -> int:
        self._app_logger.info("Starting coldwatch accessibility logger")
        self._app_logger.debug(f"Configuration: db_path={self.cfg.db_path}, log_level={self.cfg.log_level}")

        try:
            self._app_logger.debug(f"Initializing database at {self.cfg.db_path}")
            db.initialize(self.cfg.db_path)
            self._app_logger.info(f"Database initialized successfully at {self.cfg.db_path}")
        except sqlite3.Error as exc:  # pragma: no cover - sqlite failures are rare
            log_exception(self._app_logger, f"Failed to initialize database at {self.cfg.db_path}")
            logger.error("Failed to initialize database: {}", exc)
            return 3

        self._app_logger.debug(f"Waiting for AT-SPI registry (timeout: {self.cfg.wait_for_atspi}s)")
        if not scanner.wait_for_registry(self.cfg.wait_for_atspi, self.cfg.interval):
            self._app_logger.error(f"AT-SPI registry unavailable after {self.cfg.wait_for_atspi}s - check AT-SPI setup")
            logger.error(
                "AT-SPI registry unavailable after {:.1f}s", self.cfg.wait_for_atspi
            )
            return 2

        self._app_logger.info("AT-SPI registry connection established")

        with db.db(self.cfg.db_path) as conn:
            if self.cfg.once:
                self._app_logger.info("Performing single accessibility tree scan")
                logger.info("🔍 Performing single tree scan")
                scanner.walk_tree(conn, self.cfg, self._state)
                self._app_logger.info("Single tree scan completed successfully")
                return 0

            self._app_logger.info("Starting continuous accessibility monitoring")
            logger.info("🚀 Starting ColdWatch logger")

            stop_requested = False

            def _request_stop(signum: int, frame) -> None:  # type: ignore[misc]
                nonlocal stop_requested
                stop_requested = True
                signal_name = signal.Signals(signum).name
                self._app_logger.info(f"Received {signal_name} signal, initiating graceful shutdown")
                logger.info(
                    "Received signal %s, stopping...", signal_name
                )
                with suppress(Exception):
                    import pyatspi

                    self._app_logger.debug("Stopping AT-SPI registry")
                    pyatspi.Registry.stop()

            original_int = signal.getsignal(signal.SIGINT)
            original_term = signal.getsignal(signal.SIGTERM)
            signal.signal(signal.SIGINT, _request_stop)
            signal.signal(signal.SIGTERM, _request_stop)

            self._app_logger.debug("Signal handlers configured")

            try:
                self._app_logger.debug("Starting initial accessibility tree walk")
                scanner.walk_tree(conn, self.cfg, self._state)
                self._app_logger.info("Initial tree scan completed, starting event subscription")
                scanner.subscribe_events(conn, self.cfg, self._state)
                self._app_logger.info("Event monitoring started successfully")
            except Exception as exc:
                log_exception(self._app_logger, "Error during scanner operation", exc_info=True)
                raise
            finally:
                self._app_logger.debug("Restoring original signal handlers")
                signal.signal(signal.SIGINT, original_int)
                signal.signal(signal.SIGTERM, original_term)

            exit_code = 0 if not stop_requested else 0
            self._app_logger.info(f"Accessibility logger stopped (exit code: {exit_code})")
            return exit_code

    def _configure_logging(self) -> None:
        # Configure loguru for backward compatibility
        logger.remove()
        logger.add(sys.stderr, level=self.cfg.log_level.upper(), enqueue=True)

        # Configure comprehensive logging
        setup_logging(
            log_level=self.cfg.log_level,
            log_file=self.cfg.db_path.parent / "coldwatch.log" if hasattr(self.cfg.db_path, 'parent') else None,
            enable_console=True,
            enable_file_rotation=True
        )


def run_logger(cfg: RunConfig | None = None) -> int:
    config = cfg or RunConfig()
    app_logger = get_logger("main")

    app_logger.info("ColdWatch AT-SPI accessibility logger starting up")
    app_logger.debug(f"Python version: {sys.version}")

    try:
        import pyatspi  # noqa: F401  # Ensure the dependency is present
        app_logger.debug("AT-SPI Python bindings loaded successfully")
    except Exception as exc:  # pragma: no cover - depends on environment
        log_exception(app_logger, "Failed to load AT-SPI Python bindings - ensure python3-pyatspi is installed")
        logger.error("AT-SPI bindings unavailable: {}", exc)
        return 2

    if not privacy.should_capture_text(config):
        app_logger.warning("Text capture disabled by privacy settings - only metadata will be stored")
        logger.warning("Text capture disabled; only metadata will be stored.")

    logger_instance = AccessibilityLogger(config)
    try:
        return logger_instance.run()
    except KeyboardInterrupt:
        app_logger.info("Logger interrupted by user (Ctrl+C)")
        logger.info("Interrupted by user")
        return 0
    except sqlite3.Error as exc:  # pragma: no cover - handled above, fallback safety
        log_exception(app_logger, f"SQLite database error occurred")
        logger.error("Database error: {}", exc)
        return 3
    except Exception as exc:
        log_exception(app_logger, "Unexpected error occurred during logger execution")
        return 1
