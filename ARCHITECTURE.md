# ColdWatch Architecture

## Event Flow
1. `core.AccessibilityLogger` configures logging and initializes the SQLite schema.
2. `scanner.walk_tree` performs an initial traversal of the AT-SPI desktop, capturing text snapshots for matching widgets.
3. `scanner.subscribe_events` registers listeners for `object:text-changed`, `object:state-changed:focused`, and `object:children-changed` events. Each event is stored via `db.log_event` and triggers conditional text capture.
4. `db.store_snapshot` writes deduplicated text entries keyed by object ID and text hash, while `db.update_registry` keeps the `object_registry` table current.

## Modules
- `coldwatch.types`: Defines the `RunConfig` dataclass used across the package.
- `coldwatch.cli`: Parses CLI flags and dispatches to `run` or `analyze` handlers.
- `coldwatch.core`: High-level orchestration, signal handling, and lifecycle management.
- `coldwatch.scanner`: AT-SPI integration, traversal, event listeners, and filtering logic.
- `coldwatch.db`: SQLite schema, connection helpers, and persistence primitives.
- `coldwatch.analyze`: Convenience reporting for captured data.
- `coldwatch.privacy`: Central place for privacy toggles such as `capture_text`.

## Extension Points
- Additional sinks: Implement alternative writers in `db.py` or append new modules.
- Privacy: Expand `privacy.py` to add per-field redaction or hashing strategies.
- CLI: Introduce more subcommands (e.g., `coldwatch web`) without touching the logger core.
