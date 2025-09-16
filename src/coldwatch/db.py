from __future__ import annotations

import json
import sqlite3
from collections.abc import Generator
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

SCHEMA = """
CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    event_type TEXT NOT NULL,
    app_name TEXT,
    object_id TEXT,
    object_role TEXT,
    object_name TEXT,
    detail1 INTEGER,
    detail2 INTEGER,
    source_info TEXT,
    UNIQUE(timestamp, event_type, object_id) ON CONFLICT IGNORE
);

CREATE INDEX IF NOT EXISTS idx_events_timestamp
    ON events (timestamp);

CREATE TABLE IF NOT EXISTS text_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    object_id TEXT NOT NULL,
    app_name TEXT,
    object_role TEXT,
    object_name TEXT,
    text_content TEXT,
    text_hash TEXT NOT NULL,
    char_count INTEGER,
    can_read INTEGER,
    can_write INTEGER,
    interfaces TEXT,
    states TEXT,
    bounds TEXT,
    UNIQUE(object_id, text_hash) ON CONFLICT IGNORE
);

CREATE INDEX IF NOT EXISTS idx_snapshots_timestamp
    ON text_snapshots (timestamp);
CREATE INDEX IF NOT EXISTS idx_snapshots_object
    ON text_snapshots (object_id);

CREATE TABLE IF NOT EXISTS object_registry (
    object_id TEXT PRIMARY KEY,
    app_name TEXT,
    object_role TEXT,
    object_name TEXT,
    last_seen TEXT,
    is_text_widget INTEGER,
    interfaces TEXT,
    states TEXT,
    bounds TEXT,
    last_text_hash TEXT
);
"""


@contextmanager
def db(path: str) -> Generator[sqlite3.Connection, None, None]:
    conn = sqlite3.connect(path)
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def initialize(path: str) -> None:
    with sqlite3.connect(path) as conn:
        conn.executescript(SCHEMA)


@dataclass(slots=True)
class EventRecord:
    timestamp: str
    event_type: str
    app_name: str | None
    object_id: str | None
    object_role: str | None
    object_name: str | None
    detail1: int | None
    detail2: int | None
    source_info: dict[str, Any]


@dataclass(slots=True)
class SnapshotRecord:
    timestamp: str
    object_id: str
    app_name: str | None
    object_role: str | None
    object_name: str | None
    text_content: str
    text_hash: str
    char_count: int
    can_read: bool
    can_write: bool
    interfaces: list[str]
    states: list[str]
    bounds: dict[str, Any] | None


@dataclass(slots=True)
class RegistryRecord:
    object_id: str
    app_name: str | None
    object_role: str | None
    object_name: str | None
    last_seen: str
    is_text_widget: bool
    interfaces: list[str]
    states: list[str]
    bounds: dict[str, Any] | None
    last_text_hash: str | None


def _dump_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False)


def log_event(conn: sqlite3.Connection, record: EventRecord) -> None:
    conn.execute(
        """
        INSERT OR IGNORE INTO events
        (timestamp, event_type, app_name, object_id, object_role, object_name,
         detail1, detail2, source_info)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            record.timestamp,
            record.event_type,
            record.app_name,
            record.object_id,
            record.object_role,
            record.object_name,
            record.detail1,
            record.detail2,
            _dump_json(record.source_info),
        ),
    )


def store_snapshot(conn: sqlite3.Connection, record: SnapshotRecord) -> bool:
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT OR IGNORE INTO text_snapshots
        (timestamp, object_id, app_name, object_role, object_name, text_content,
         text_hash, char_count, can_read, can_write, interfaces, states, bounds)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            record.timestamp,
            record.object_id,
            record.app_name,
            record.object_role,
            record.object_name,
            record.text_content,
            record.text_hash,
            record.char_count,
            int(record.can_read),
            int(record.can_write),
            _dump_json(record.interfaces),
            _dump_json(record.states),
            _dump_json(record.bounds),
        ),
    )
    return cursor.rowcount > 0


def update_registry(conn: sqlite3.Connection, record: RegistryRecord) -> None:
    conn.execute(
        """
        INSERT INTO object_registry
        (object_id, app_name, object_role, object_name, last_seen,
         is_text_widget, interfaces, states, bounds, last_text_hash)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(object_id) DO UPDATE SET
         app_name=excluded.app_name,
         object_role=excluded.object_role,
         object_name=excluded.object_name,
         last_seen=excluded.last_seen,
         is_text_widget=excluded.is_text_widget,
         interfaces=excluded.interfaces,
         states=excluded.states,
         bounds=excluded.bounds,
         last_text_hash=excluded.last_text_hash
        """,
        (
            record.object_id,
            record.app_name,
            record.object_role,
            record.object_name,
            record.last_seen,
            int(record.is_text_widget),
            _dump_json(record.interfaces),
            _dump_json(record.states),
            _dump_json(record.bounds),
            record.last_text_hash,
        ),
    )


def utcnow() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")
