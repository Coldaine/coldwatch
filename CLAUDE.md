# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ColdWatch is a Linux-first accessibility logger built on AT-SPI that captures text widgets and related events from running applications. It stores data in SQLite and provides CLI tools for runtime control and database analysis.

## Key Dependencies

- **System packages required**: `pyatspi`, `PyGObject`, `dbus-run-session`, `xvfb-run`
- **Python**: 3.10+
- **Main libraries**: `loguru` for logging, SQLite for storage
- **Development tools**: `ruff` (linting), `black` (formatting), `pytest` (testing), `pre-commit` (git hooks)

## Development Commands

### Installation
```bash
# Install the package in development mode with dev tools
pip install -e .[dev]

# Install pre-commit hooks
pre-commit install
```

### Code Quality
```bash
# Run all pre-commit checks
uvx pre-commit run --all-files

# Run linter
uvx ruff check .

# Run formatter check
uvx black --check .

# Format code
uvx black .
```

### Testing
```bash
# Run unit tests only (fast, no AT-SPI required)
uvx pytest -m "not integration"

# Run integration tests (requires Linux with AT-SPI)
uvx pytest -m integration

# Run all tests
uvx pytest

# Run specific test file
uvx pytest tests/test_scanner.py

# Run with coverage
uvx pytest --cov=coldwatch
```

### Running ColdWatch
```bash
# Standard run (captures to accessibility_log.db)
coldwatch run

# Custom database and log level
coldwatch run --db custom.db --log-level DEBUG

# Single scan mode
coldwatch run --once

# Metadata only (no text capture)
coldwatch run --no-text

# Analyze captured data
coldwatch analyze accessibility_log.db
```

## Architecture

### Module Structure
- `coldwatch.types`: Core dataclasses (RunConfig)
- `coldwatch.cli`: Command-line interface and argument parsing
- `coldwatch.core`: High-level orchestration and lifecycle management
- `coldwatch.scanner`: AT-SPI integration, tree traversal, and event handling
- `coldwatch.db`: SQLite schema, storage, and deduplication logic
- `coldwatch.analyze`: Database analysis and reporting utilities
- `coldwatch.privacy`: Privacy controls for text capture
- `coldwatch.logging_config`: Centralized logging setup

### Event Processing Flow
1. `AccessibilityLogger` initializes the SQLite database with schema
2. `walk_tree()` performs initial AT-SPI desktop traversal, capturing text snapshots
3. Event listeners monitor:
   - `object:text-changed`: Text widget modifications
   - `object:state-changed:focused`: Focus changes
   - `object:children-changed`: Structural changes
4. Events are stored via `log_event()` with conditional text capture based on privacy settings
5. `store_snapshot()` deduplicates text entries using object ID and text hash
6. `update_registry()` maintains the object registry table

### Database Schema
- **snapshots**: Deduplicated text captures (object_id, text_hash, text_content, timestamp)
- **events**: All accessibility events with metadata
- **object_registry**: Tracked objects with application context
- **app_handlers**: Application-specific configuration (future use)

### Key Design Patterns
- Event-driven architecture using AT-SPI callbacks
- Text deduplication via SHA-256 hashing
- Configurable privacy controls (--no-text flag)
- Modular filtering system for apps and roles
- Graceful shutdown handling with signal management

## Testing Approach

Integration tests require a Linux environment with AT-SPI support. They use `dbus-run-session` and `xvfb-run` to create a headless testing environment with mock GTK applications.

Unit tests focus on database operations, configuration parsing, and utility functions that don't require AT-SPI.

## Common Development Tasks

### Adding Event Types
New event types should be registered in `scanner.subscribe_events()` and handled appropriately in the event callback system.

### Extending Filtering
Application and role filters are processed in `scanner.py`. Add new filter logic to `_should_process_object()`.

### Database Migrations
Schema changes should be handled in `db.setup_database()`. Consider backwards compatibility when modifying existing tables.