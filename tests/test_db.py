import sqlite3

from coldwatch import db


def test_schema_and_snapshot_dedupe(tmp_path):
    path = tmp_path / "test.db"
    db.initialize(path)

    timestamp = db.utcnow()
    snapshot = db.SnapshotRecord(
        timestamp=timestamp,
        object_id="app:role:1",
        app_name="Example",
        object_role="text",
        object_name="Widget",
        text_content="hello",
        text_hash="hash",
        char_count=5,
        can_read=True,
        can_write=True,
        interfaces=["Text"],
        states=["enabled"],
        bounds={"x": 0, "y": 0, "width": 10, "height": 10},
    )

    registry = db.RegistryRecord(
        object_id="app:role:1",
        app_name="Example",
        object_role="text",
        object_name="Widget",
        last_seen=timestamp,
        is_text_widget=True,
        interfaces=["Text"],
        states=["enabled"],
        bounds={"x": 0, "y": 0, "width": 10, "height": 10},
        last_text_hash="hash",
    )

    with db.db(path) as conn:
        stored_first = db.store_snapshot(conn, snapshot)
        stored_second = db.store_snapshot(conn, snapshot)
        db.update_registry(conn, registry)

    assert stored_first is True
    assert stored_second is False

    with sqlite3.connect(path) as conn:
        count = conn.execute("SELECT COUNT(*) FROM text_snapshots").fetchone()[0]
        assert count == 1
        reg = conn.execute(
            "SELECT last_text_hash FROM object_registry WHERE object_id=?",
            ("app:role:1",),
        ).fetchone()
        assert reg[0] == "hash"
