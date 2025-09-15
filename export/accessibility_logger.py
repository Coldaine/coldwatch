#!/usr/bin/env python3
"""
AT-SPI Accessibility Tree Logger
Captures all text fields and events from running applications
"""

import pyatspi
import sqlite3
import json
import hashlib
import time
from datetime import datetime
from pathlib import Path
from loguru import logger
from typing import Dict, Set, Optional, Any

class AccessibilityLogger:
    def __init__(self, db_path: str = "accessibility_log.db"):
        self.db_path = db_path
        self.init_database()
        self.object_cache: Dict[str, Dict] = {}
        self.text_hashes: Dict[str, str] = {}
        self.focused_objects: Set[str] = set()

        # Configure loguru for console output
        logger.remove()
        logger.add(
            lambda msg: print(msg, end=""),
            format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | {message}",
            level="INFO"
        )
        logger.add("accessibility.log", rotation="10 MB", level="DEBUG")

    def init_database(self):
        """Initialize SQLite database with required tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Events table
        cursor.execute("""
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
            )
        """)

        # Text snapshots table (deduplicated by hash)
        cursor.execute("""
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
                can_read BOOLEAN,
                can_write BOOLEAN,
                interfaces TEXT,
                states TEXT,
                bounds TEXT,
                UNIQUE(object_id, text_hash) ON CONFLICT IGNORE
            )
        """)

        # Object registry (current state)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS object_registry (
                object_id TEXT PRIMARY KEY,
                app_name TEXT,
                object_role TEXT,
                object_name TEXT,
                last_seen TEXT,
                is_text_widget BOOLEAN,
                interfaces TEXT,
                states TEXT,
                bounds TEXT,
                last_text_hash TEXT
            )
        """)

        conn.commit()
        conn.close()

    def get_object_id(self, obj) -> str:
        """Generate stable ID for AT-SPI object"""
        try:
            # Use application name + role + path for stability
            app_name = obj.getApplication().name if obj.getApplication() else "unknown"
            role_name = obj.getRoleName()
            path = str(obj.path) if hasattr(obj, 'path') else str(id(obj))
            return f"{app_name}:{role_name}:{path}"
        except:
            return f"unknown:{id(obj)}"

    def get_object_info(self, obj) -> Dict[str, Any]:
        """Extract comprehensive info from AT-SPI object"""
        info = {
            'app_name': 'unknown',
            'role': 'unknown',
            'name': '',
            'interfaces': [],
            'states': [],
            'bounds': None,
            'text_content': '',
            'char_count': 0,
            'can_read': False,
            'can_write': False
        }
