from __future__ import annotations

from .types import RunConfig


def should_capture_text(cfg: RunConfig) -> bool:
    """Return True if text content should be persisted."""

    return cfg.capture_text
