# src/tool_asset_system/services/tooling_lists.py
from __future__ import annotations

import os
import sqlite3
from typing import Any

from tool_asset_system.db.db import connect
from tool_asset_system.services.idgen import issue_asset_code


def _actor() -> str:
    return os.environ.get("USERNAME") or os.environ.get("USER") or "unknown"


def _row_to_dict(row: sqlite3.Row | None) -> dict[str, Any] | None:
    if row is None:
        return None
    return {k: row[k] for k in row.keys()}


def add_tooling_list(*, title: str, note: str | None = None) -> str:
    t = (title or "").strip()
    if t == "":
        raise ValueError("title is required")

    with connect() as con:
        con.execute("BEGIN IMMEDIATE")
        list_code = issue_asset_code(con, layer_code="TL")

        con.execute(
            """
            INSERT INTO tooling_lists(list_code, title, note)
            VALUES(?,?,?)
            """,
            (list_code, t, note),
        )
        con.commit()
        return list_code


def get_tooling_list(list_code: str) -> dict[str, Any]:
    with connect() as con:
        row = con.execute(
            "SELECT * FROM tooling_lists WHERE list_code=?",
            (list_code,),
        ).fetchone()
        if row is None:
            raise ValueError(f"tooling_list not found: {list_code}")
        return _row_to_dict(row)  # type: ignore[return-value]


def list_tooling_lists(*, q: str | None = None, limit: int = 200) -> list[dict[str, Any]]:
    sql = "SELECT * FROM tooling_lists WHERE 1=1"
    params: list[Any] = []

    if q and q.strip():
        kw = f"%{q.strip()}%"
        sql += " AND (list_code LIKE ? OR title LIKE ? OR note LIKE ?)"
        params.extend([kw, kw, kw])

    sql += " ORDER BY updated_at DESC, list_code DESC LIMIT ?"
    params.append(int(limit))

    with connect() as con:
        rows = con.execute(sql, params).fetchall()
        return [_row_to_dict(r) for r in rows]  # type: ignore[misc]


def update_tooling_list(
    list_code: str,
    *,
    title: str | None = None,
    note: str | None = None,
) -> None:
    fields: list[tuple[str, object]] = []

    if title is not None:
        t = title.strip()
        if t == "":
            raise ValueError("title cannot be empty")
        fields.append(("title", t))

    if note is not None:
        n = note.strip()
        fields.append(("note", n if n != "" else None))

    if not fields:
        return

    with connect() as con:
        con.execute("BEGIN IMMEDIATE")

        cur = con.execute(
            "SELECT 1 FROM tooling_lists WHERE list_code=?",
            (list_code,),
        ).fetchone()
        if cur is None:
            raise ValueError(f"tooling_list not found: {list_code}")

        set_sql = ", ".join([f"{k} = ?" for k, _ in fields] + ["updated_at = CURRENT_TIMESTAMP"])
        params = [v for _, v in fields] + [list_code]

        con.execute(
            f"UPDATE tooling_lists SET {set_sql} WHERE list_code = ?",
            params,
        )
        con.commit()


def _get_tooling_list_id(con: sqlite3.Connection, list_code: str) -> int:
    row = con.execute(
        "SELECT id FROM tooling_lists WHERE list_code=?",
        (list_code,),
    ).fetchone()
    if row is None:
        raise ValueError(f"tooling_list not found: {list_code}")
    return int(row["id"])


def _get_assembly_id_by_code(con: sqlite3.Connection, assembly_code: str) -> int:
    row = con.execute(
        "SELECT id FROM assemblies WHERE assembly_code=?",
        (assembly_code,),
    ).fetchone()
    if row is None:
        raise ValueError(f"assembly not found: {assembly_code}")
    return int(row["id"])


def add_tooling_list_item(
    list_code: str,
    *,
    assembly_code: str,
    tool_no: str,
    qty: float = 1.0,
    note: str | None = None,
) -> int:
    tn = (tool_no or "").strip()
    if tn == "":
        raise ValueError("tool_no is required")
    if qty <= 0:
        raise ValueError("qty must be > 0")

    with connect() as con:
        con.execute("BEGIN IMMEDIATE")

        list_id = _get_tooling_list_id(con, list_code)
        asm_id = _get_assembly_id_by_code(con, assembly_code)

        con.execute(
            """
            INSERT INTO tooling_list_items(
              tooling_list_id, assembly_id, tool_no, qty, note
            ) VALUES(?,?,?,?,?)
            """,
            (list_id, asm_id, tn, float(qty), note),
        )

        item_id = int(con.execute("SELECT last_insert_rowid() AS id").fetchone()["id"])
        con.commit()
        return item_id


def remove_tooling_list_item(list_code: str, *, item_id: int) -> None:
    with connect() as con:
        con.execute("BEGIN IMMEDIATE")
        list_id = _get_tooling_list_id(con, list_code)

        cur = con.execute(
            "DELETE FROM tooling_list_items WHERE id=? AND tooling_list_id=?",
            (int(item_id), list_id),
        )
        if cur.rowcount != 1:
            raise ValueError(f"tooling_list_item not found: id={item_id} in {list_code}")

        con.commit()


def replace_tooling_list_items(
    list_code: str,
    *,
    items: list[dict[str, Any]],
) -> None:
    """
    Replace tooling_list_items entirely for a tooling list.
    items: [{"assembly_code": "...", "tool_no": "...", "qty": 1.0}, ...]
    Enforces:
      - tool_no required
      - qty > 0
      - no duplicates (tool_no, assembly_code) inside the payload
    """
    # payload validation (friendly errors before hitting UNIQUE)
    seen_tool_no: set[str] = set()
    seen_asm: set[str] = set()

    normalized: list[tuple[str, str, float]] = []
    for it in items:
        ac = str(it.get("assembly_code") or "").strip()
        tn = str(it.get("tool_no") or "").strip()
        qty_raw = it.get("qty", 1.0)

        if ac == "":
            raise ValueError("assembly_code is required")
        if tn == "":
            raise ValueError(f"tool_no is required: {ac}")

        try:
            qty = float(qty_raw)
        except Exception:
            qty = 1.0
        if qty <= 0:
            raise ValueError(f"qty must be > 0: {ac}")

        if tn in seen_tool_no:
            raise ValueError(f"duplicate tool_no in the same list: {tn}")
        if ac in seen_asm:
            raise ValueError(f"duplicate assembly_code in the same list: {ac}")

        seen_tool_no.add(tn)
        seen_asm.add(ac)
        normalized.append((ac, tn, qty))

    with connect() as con:
        con.execute("BEGIN IMMEDIATE")
        list_id = _get_tooling_list_id(con, list_code)

        # delete all
        con.execute("DELETE FROM tooling_list_items WHERE tooling_list_id=?", (list_id,))

        # insert all
        for (assembly_code, tool_no, qty) in normalized:
            asm_id = _get_assembly_id_by_code(con, assembly_code)
            con.execute(
                """
                INSERT INTO tooling_list_items(
                  tooling_list_id, assembly_id, tool_no, qty
                ) VALUES(?,?,?,?)
                """,
                (list_id, asm_id, tool_no, float(qty)),
            )

        # parent updated_at を更新（items変更も更新扱いにする）
        con.execute(
            "UPDATE tooling_lists SET updated_at = CURRENT_TIMESTAMP WHERE id=?",
            (list_id,),
        )

        con.commit()


def list_tooling_list_items(list_code: str, *, limit: int = 500) -> list[dict[str, Any]]:
    with connect() as con:
        list_id = _get_tooling_list_id(con, list_code)

        rows = con.execute(
            """
            SELECT
              tli.id AS item_id,
              tli.tool_no,
              tli.qty,
              tli.note AS item_note,

              a.assembly_code,
              a.display_name AS assembly_name,
              a.tool_diameter,
              a.tool_overall_length,
              a.note AS assembly_note,
              a.updated_at AS assembly_updated_at
            FROM tooling_list_items tli
            JOIN assemblies a ON a.id = tli.assembly_id
            WHERE tli.tooling_list_id = ?
            ORDER BY
              CAST(tli.tool_no AS INTEGER) ASC,
              tli.tool_no ASC,
              a.assembly_code ASC,
              tli.id ASC
            LIMIT ?
            """,
            (list_id, int(limit)),
        ).fetchall()

        return [{k: r[k] for k in r.keys()} for r in rows]
