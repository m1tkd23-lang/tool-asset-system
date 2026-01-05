from __future__ import annotations

import sqlite3
from pathlib import Path

# プロジェクトルートを基準に data/tool_asset.db を指す
BASE_DIR = Path(__file__).resolve().parents[3]
DB_PATH = BASE_DIR / "data" / "tool_asset.db"


def connect() -> sqlite3.Connection:
    """
    SQLite connection factory.
    foreign_keys ON を保証する。
    """
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON;")
    return con
