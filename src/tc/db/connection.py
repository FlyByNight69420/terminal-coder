"""SQLite connection management."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from tc.db.schema import SCHEMA_DDL


def _row_factory(cursor: sqlite3.Cursor, row: tuple[object, ...]) -> dict[str, object]:
    """Convert rows to dictionaries keyed by column name."""
    columns = [description[0] for description in cursor.description]
    return dict(zip(columns, row))


def create_connection(db_path: Path | str) -> sqlite3.Connection:
    """Create a SQLite connection with WAL mode and foreign keys enabled."""
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = _row_factory  # type: ignore[assignment]
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def initialize_db(db_path: Path | str) -> None:
    """Run the full schema DDL against the database."""
    conn = create_connection(db_path)
    try:
        conn.executescript(SCHEMA_DDL)
        conn.commit()
    finally:
        conn.close()
