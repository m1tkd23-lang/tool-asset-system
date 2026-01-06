#services/assemblies.py
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


# 並び順（signature生成などで使用）
ROLE_ORDER = [
    "HOLDER",
    "SUB_HOLDER",
    "TOOL_BODY",
    "INSERT",
    "SOLID_TOOL",
    "SCREW",
    "ACCESSORY",
]


def _role_rank(role: str | None) -> int:
    if not role:
        return 999
    try:
        return ROLE_ORDER.index(role)  # 0..n
    except ValueError:
        return 998  # 未知roleは末尾寄り


def make_signature_from_items(items: list[dict[str, Any]]) -> str:
    """
    items(list_assembly_itemsの戻り)から
    asset_codeを '_' で連結した signature を作る。

    並び順は「parts.layer_code（レイヤー）」で強制する：
    HOLDER → SUB_HOLDER → TOOL_BODY → INSERT → SOLID_TOOL → SCREW → ACCESSORY
    """
    def layer_rank(it: dict[str, Any]) -> int:
        lc = (it.get("layer_code") or "").strip()
        return _role_rank(lc)  # ROLE_ORDERを流用

    ordered = sorted(
        items,
        key=lambda it: (layer_rank(it), str(it.get("asset_code", "")))
    )
    codes = [str(it.get("asset_code")) for it in ordered if it.get("asset_code")]
    return "_".join(codes)

# ============================================================
# Assemblies: basic CRUD
# ============================================================

def add_assembly(
    *,
    display_name: str | None = None,
    tool_overall_length: float | None = None,
    tool_diameter: float | None = None,
    note: str | None = None,
    actor: str | None = None,
) -> str:
    """
    Create an assembly and return issued assembly_code (ASM_00000001).
    display_name can be None/blank. In that case, caller may update later.
    """
    actor = actor or _actor()

    dn = (display_name or "").strip()
    if dn == "":
        dn = "NEW_ASSEMBLY"  # 仮（後でitems追加後に update_assembly でsignatureに置き換えOK）

    with connect() as con:
        con.execute("BEGIN IMMEDIATE")

        assembly_code = issue_asset_code(con, layer_code="ASM")

        con.execute(
            """
            INSERT INTO assemblies(
              assembly_code,
              display_name,
              tool_overall_length,
              tool_diameter,
              note
            ) VALUES(?,?,?,?,?)
            """,
            (assembly_code, dn, tool_overall_length, tool_diameter, note),
        )

        con.commit()
        return assembly_code


def get_assembly(assembly_code: str) -> dict[str, Any]:
    with connect() as con:
        row = con.execute(
            "SELECT * FROM assemblies WHERE assembly_code = ?",
            (assembly_code,),
        ).fetchone()
        if row is None:
            raise ValueError(f"assembly not found: {assembly_code}")
        return _row_to_dict(row)  # type: ignore[return-value]


def list_assemblies(
    *,
    q: str | None = None,
    limit: int = 200,
) -> list[dict[str, Any]]:
    sql = "SELECT * FROM assemblies WHERE 1=1"
    params: list[Any] = []

    if q and q.strip():
        kw = f"%{q.strip()}%"
        sql += " AND (assembly_code LIKE ? OR display_name LIKE ? OR note LIKE ?)"
        params.extend([kw, kw, kw])

    sql += " ORDER BY assembly_code LIMIT ?"
    params.append(int(limit))

    with connect() as con:
        rows = con.execute(sql, params).fetchall()
        return [_row_to_dict(r) for r in rows]  # type: ignore[misc]


def update_assembly(
    assembly_code: str,
    *,
    display_name: str | None = None,
    tool_overall_length: float | None = None,
    tool_diameter: float | None = None,
    note: str | None = None,
    actor: str | None = None,
) -> None:
    actor = actor or _actor()

    fields: list[tuple[str, object]] = []
    if display_name is not None:
        dn = display_name.strip()
        if dn == "":
            raise ValueError("display_name cannot be empty")
        fields.append(("display_name", dn))
    if tool_overall_length is not None:
        fields.append(("tool_overall_length", tool_overall_length))
    if tool_diameter is not None:
        fields.append(("tool_diameter", tool_diameter))
    if note is not None:
        fields.append(("note", note))

    if not fields:
        return

    with connect() as con:
        con.execute("BEGIN IMMEDIATE")

        cur = con.execute(
            "SELECT 1 FROM assemblies WHERE assembly_code=?",
            (assembly_code,),
        ).fetchone()
        if cur is None:
            raise ValueError(f"assembly not found: {assembly_code}")

        set_sql = ", ".join([f"{k} = ?" for k, _ in fields] + ["updated_at = CURRENT_TIMESTAMP"])
        params = [v for _, v in fields] + [assembly_code]

        cur2 = con.execute(
            f"UPDATE assemblies SET {set_sql} WHERE assembly_code = ?",
            params,
        )
        if cur2.rowcount != 1:
            raise ValueError(f"assembly not found: {assembly_code}")

        con.commit()


# ============================================================
# Assembly items: add/remove/list
# ============================================================

def _get_assembly_id(con: sqlite3.Connection, assembly_code: str) -> int:
    row = con.execute(
        "SELECT id FROM assemblies WHERE assembly_code = ?",
        (assembly_code,),
    ).fetchone()
    if row is None:
        raise ValueError(f"assembly not found: {assembly_code}")
    return int(row["id"])


def _get_part_id_by_asset_code(con: sqlite3.Connection, part_asset_code: str) -> int:
    row = con.execute(
        "SELECT id FROM parts WHERE asset_code = ?",
        (part_asset_code,),
    ).fetchone()
    if row is None:
        raise ValueError(f"part not found: {part_asset_code}")
    return int(row["id"])


def add_assembly_item(
    assembly_code: str,
    *,
    part_asset_code: str,
    qty: float = 1.0,
    role: str | None = None,
    note: str | None = None,
    actor: str | None = None,
) -> int:
    actor = actor or _actor()
    if qty <= 0:
        raise ValueError("qty must be > 0")

    with connect() as con:
        con.execute("BEGIN IMMEDIATE")

        assembly_id = _get_assembly_id(con, assembly_code)
        part_id = _get_part_id_by_asset_code(con, part_asset_code)

        con.execute(
            """
            INSERT INTO assembly_items(
              assembly_id,
              part_id,
              qty,
              role,
              note
            ) VALUES(?,?,?,?,?)
            """,
            (assembly_id, part_id, float(qty), role, note),
        )

        item_id = int(con.execute("SELECT last_insert_rowid() AS id").fetchone()["id"])
        con.commit()
        return item_id


def remove_assembly_item(
    assembly_code: str,
    *,
    item_id: int,
    actor: str | None = None,
) -> None:
    actor = actor or _actor()

    with connect() as con:
        con.execute("BEGIN IMMEDIATE")
        assembly_id = _get_assembly_id(con, assembly_code)

        cur = con.execute(
            "DELETE FROM assembly_items WHERE id = ? AND assembly_id = ?",
            (int(item_id), assembly_id),
        )
        if cur.rowcount != 1:
            raise ValueError(f"assembly item not found: id={item_id} in {assembly_code}")

        con.commit()


def list_assembly_items(
    assembly_code: str,
    *,
    limit: int = 500,
) -> list[dict[str, Any]]:
    with connect() as con:
        assembly_id = _get_assembly_id(con, assembly_code)

        rows = con.execute(
            """
            SELECT
              ai.id AS item_id,
              ai.qty,
              ai.role,
              ai.note AS item_note,

              p.asset_code,
              p.layer_code,
              p.category_code,
              p.category_free_text,
              p.status,
              p.maker,
              p.part_no,
              p.maker_part_name,
              p.display_name,
              p.stock_qty,
              p.stock_unit
            FROM assembly_items ai
            JOIN parts p ON p.id = ai.part_id
            WHERE ai.assembly_id = ?
            ORDER BY ai.id
            LIMIT ?
            """,
            (assembly_id, int(limit)),
        ).fetchall()

        return [{k: r[k] for k in r.keys()} for r in rows]
