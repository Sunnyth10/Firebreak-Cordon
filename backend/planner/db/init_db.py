"""Database initializer for Cyber Incident Response Planner."""

import sqlite3
from pathlib import Path

DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "planner.db"
SCHEMA_PATH = Path(__file__).resolve().parent / "schema.sql"


def init_database(db_path: Path | str = DEFAULT_DB_PATH) -> Path:
    """Initialize SQLite database using schema.sql."""
    target_path = Path(db_path)
    target_path.parent.mkdir(parents=True, exist_ok=True)

    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        schema_sql = f.read()

    conn = sqlite3.connect(target_path)
    try:
        conn.executescript(schema_sql)
        conn.commit()
    finally:
        conn.close()

    return target_path


if __name__ == "__main__":
    db_file = init_database()
    print(f"Initialized database schema at {db_file}")
