from __future__ import annotations

import sqlite3
from pathlib import Path

from loguru import logger


def summarize_db(path: str = "accessibility_log.db") -> None:
    db_path = Path(path)
    if not db_path.exists():
        logger.error("Database not found at {}", db_path)
        return

    with sqlite3.connect(db_path) as conn:
        logger.info("📊 Summary statistics")
        events_count = conn.execute("SELECT COUNT(*) FROM events").fetchone()[0]
        snapshots_count = conn.execute(
            "SELECT COUNT(*) FROM text_snapshots"
        ).fetchone()[0]
        apps_count = conn.execute(
            "SELECT COUNT(DISTINCT app_name) FROM object_registry"
        ).fetchone()[0]

        logger.info("Events: {}", events_count)
        logger.info("Text snapshots: {}", snapshots_count)
        logger.info("Applications: {}", apps_count)

        logger.info("\n📄 Recent text captures")
        rows = conn.execute(
            """
            SELECT timestamp, app_name, object_role, char_count, substr(text_content, 1, 120)
            FROM text_snapshots
            ORDER BY timestamp DESC
            LIMIT 10
            """
        ).fetchall()
        for timestamp, app_name, role, length, preview in rows:
            logger.info(
                "[{timestamp}] {app} ({role}) - {chars} chars: {preview}",
                timestamp=timestamp,
                app=app_name,
                role=role,
                chars=length,
                preview=(preview or "").replace("\n", "\\n"),
            )

        logger.info("\n🔤 Text field roles")
        roles = conn.execute(
            """
            SELECT object_role, COUNT(*)
            FROM text_snapshots
            GROUP BY object_role
            ORDER BY COUNT(*) DESC
            LIMIT 10
            """
        ).fetchall()
        for role, count in roles:
            logger.info("{role}: {count}", role=role, count=count)
