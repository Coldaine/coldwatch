from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass


@dataclass(slots=True)
class RunConfig:
    """Runtime configuration for the accessibility logger."""

    db_path: str = "accessibility_log.db"
    once: bool = False
    log_level: str = "INFO"
    interval: float = 0.5
    wait_for_atspi: float = 10.0
    include_apps: Sequence[str] = ()
    exclude_apps: Sequence[str] = ()
    include_roles: Sequence[str] = ()
    exclude_roles: Sequence[str] = ()
    capture_text: bool = True
