# src/tool_asset_system/db/scripts/manage.py
from __future__ import annotations

import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]  # tool-asset-system/
MIG_DIR = ROOT / "src" / "tool_asset_system" / "db" / "migrations"
DB_PATH = ROOT / "data" / "tool_asset.db"


def connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON;")
    return con


def ensure_schema_migrations(con: sqlite3.Connection) -> None:
    con.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_migrations (
          version TEXT PRIMARY KEY,
          applied_at TEXT NOT NULL DEFAULT (datetime('now'))
        );
        """
    )


def applied_versions(con: sqlite3.Connection) -> set[str]:
    ensure_schema_migrations(con)
    rows = con.execute("SELECT version FROM schema_migrations").fetchall()
    return {r["version"] for r in rows}


def upgrade() -> None:
    with connect() as con:
        done = applied_versions(con)

        for p in sorted(MIG_DIR.glob("*.sql")):
            ver = p.stem
            if ver in done:
                continue

            sql = p.read_text(encoding="utf-8")

            # NOTE:
            # executescript() は暗黙COMMITすることがあるので、
            # 適用記録は「実行後に必ず」INSERTして同一コネクションで確定させる
            con.executescript(sql)
            con.execute("INSERT INTO schema_migrations(version) VALUES (?)", (ver,))
            con.commit()

            print(f"[upgrade] applied {p.name}")

        print(f"[upgrade] DB: {DB_PATH}")


if __name__ == "__main__":
    upgrade()
