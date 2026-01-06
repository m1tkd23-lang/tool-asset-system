# src/tool_asset_system/services/parts.py
from __future__ import annotations

import json
import os
import sqlite3
from typing import Any

from tool_asset_system.db.db import connect
from tool_asset_system.services.idgen import issue_asset_code


def _actor() -> str:
    # Windows想定：USERNAME優先、取れなければunknown
    return (
        os.environ.get("USERNAME")
        or os.environ.get("USER")
        or "unknown"
    )


def _row_to_dict(row: sqlite3.Row | None) -> dict[str, Any] | None:
    if row is None:
        return None
    return {k: row[k] for k in row.keys()}


def _validate_category(con: sqlite3.Connection, layer_code: str, category_code: str | None) -> None:
    layer = con.execute(
        "SELECT allow_free_category FROM layers WHERE code = ?",
        (layer_code,),
    ).fetchone()
    if layer is None:
        raise ValueError(f"unknown layer_code={layer_code!r}")

    allow_free = int(layer["allow_free_category"]) == 1

    if category_code is None:
        if not allow_free:
            raise ValueError("category_code is required for this layer")
        return

    cat = con.execute(
        "SELECT 1 FROM categories WHERE code = ? AND layer_code = ?",
        (category_code, layer_code),
    ).fetchone()
    if cat is None:
        raise ValueError("category_code not found in categories for the given layer")


def add_part(
    layer_code: str,
    category_code: str | None,
    part_no: str,
    maker: str,
    stock_unit: str = "EA",
    maker_part_name: str | None = None,
    display_name: str | None = None,
    category_free_text: str | None = None,
) -> str:
    """
    Add a part and return issued asset_code.
    asset_code is auto-issued from id_sequences per layer.
    """
    if display_name is None or display_name.strip() == "":
        display_name = part_no

    with connect() as con:
        con.execute("BEGIN IMMEDIATE")

        # policy: category_code can be NULL only if allow_free_category=1 for the layer
        _validate_category(con, layer_code=layer_code, category_code=category_code)

        asset_code = issue_asset_code(con, layer_code=layer_code)

        con.execute(
            """
            INSERT INTO parts(
              asset_code,
              layer_code, category_code, category_free_text,
              part_no,
              maker, maker_part_name,
              display_name,
              stock_unit,
              status
            )
            VALUES(?,?,?,?,?,?,?,?,?,?)
            """,
            (
                asset_code,
                layer_code, category_code, category_free_text,
                part_no,
                maker, maker_part_name,
                display_name,
                stock_unit,
                "ACTIVE",
            ),
        )

        # operation log (ADD)
        after = con.execute("SELECT * FROM parts WHERE asset_code = ?", (asset_code,)).fetchone()
        con.execute(
            """
            INSERT INTO operation_logs(
              action, target_type, target_code,
              actor, reason,
              patch_json, before_json, after_json
            ) VALUES(?,?,?,?,?,?,?,?)
            """,
            (
                "PART_ADD", "PART", asset_code,
                _actor(), None,
                json.dumps({"layer_code": layer_code, "category_code": category_code}, ensure_ascii=False),
                None,
                json.dumps(_row_to_dict(after), ensure_ascii=False),
            ),
        )

        con.commit()
        return asset_code


def get_part(asset_code: str) -> dict[str, Any]:
    with connect() as con:
        row = con.execute("SELECT * FROM parts WHERE asset_code = ?", (asset_code,)).fetchone()
        if row is None:
            raise ValueError(f"part not found: {asset_code}")
        return _row_to_dict(row)  # type: ignore[return-value]


def list_parts(
    layer_code: str | None = None,
    category_code: str | None = None,
    status: str | None = None,
    q: str | None = None,
    limit: int = 200,
) -> list[dict[str, Any]]:
    sql = "SELECT * FROM parts WHERE 1=1"
    params: list[Any] = []

    if layer_code:
        sql += " AND layer_code = ?"
        params.append(layer_code)

    if category_code:
        sql += " AND category_code = ?"
        params.append(category_code)

    if status:
        sql += " AND status = ?"
        params.append(status.upper())

    if q and q.strip():
        kw = f"%{q.strip()}%"
        sql += " AND (asset_code LIKE ? OR display_name LIKE ? OR part_no LIKE ? OR maker LIKE ?)"
        params.extend([kw, kw, kw, kw])

    sql += " ORDER BY layer_code, category_code, asset_code LIMIT ?"
    params.append(int(limit))

    with connect() as con:
        rows = con.execute(sql, params).fetchall()
        return [_row_to_dict(r) for r in rows]  # type: ignore[misc]

def update_part(
    asset_code: str,
    *,
    display_name: str | None = None,
    maker_part_name: str | None = None,
    note: str | None = None,
    stock_qty: float | None = None,
    stock_unit: str | None = None,
    unit_price: float | None = None,
    supplier: str | None = None,
    lead_time_days: int | None = None,
    min_stock_qty: float | None = None,
    actor: str | None = None,
) -> None:
    actor = actor or os.environ.get("USERNAME") or "unknown"

    fields: list[tuple[str, object]] = []
    if display_name is not None: fields.append(("display_name", display_name))
    if maker_part_name is not None: fields.append(("maker_part_name", maker_part_name))
    if note is not None: fields.append(("note", note))
    if stock_qty is not None: fields.append(("stock_qty", stock_qty))
    if stock_unit is not None: fields.append(("stock_unit", stock_unit))
    if unit_price is not None: fields.append(("unit_price", unit_price))
    if supplier is not None: fields.append(("supplier", supplier))
    if lead_time_days is not None: fields.append(("lead_time_days", lead_time_days))
    if min_stock_qty is not None: fields.append(("min_stock_qty", min_stock_qty))

    if not fields:
        return

    set_sql = ", ".join([f"{k} = ?" for k, _ in fields] + ["updated_at = CURRENT_TIMESTAMP"])
    params = [v for _, v in fields] + [asset_code]

    with connect() as con:
        con.execute("BEGIN IMMEDIATE")
        cur = con.execute(f"UPDATE parts SET {set_sql} WHERE asset_code = ?", params)
        if cur.rowcount != 1:
            raise ValueError(f"part not found: {asset_code}")

        # ここで必ずログを残す（トリガーで既に残してる場合は二重になるので後で整理OK）
        con.execute(
            "INSERT INTO operation_logs(action,target_type,target_code,actor) VALUES(?,?,?,?)",
            ("PART_UPDATE", "PART", asset_code, actor),
        )
        con.commit()


def archive_part(asset_code: str, *, actor: str | None = None) -> None:
    actor = actor or os.environ.get("USERNAME") or "unknown"
    with connect() as con:
        con.execute("BEGIN IMMEDIATE")
        cur = con.execute(
            "UPDATE parts SET status='ARCHIVED', updated_at=CURRENT_TIMESTAMP WHERE asset_code=?",
            (asset_code,),
        )
        if cur.rowcount != 1:
            raise ValueError(f"part not found: {asset_code}")

        con.execute(
            "INSERT INTO operation_logs(action,target_type,target_code,actor) VALUES(?,?,?,?)",
            ("PART_ARCHIVE", "PART", asset_code, actor),
        )
        con.commit()

def _insert_log(con, *, action: str, target_code: str, actor: str, target_type: str = "PART"):
    cols = [r[1] for r in con.execute("PRAGMA table_info(operation_logs)").fetchall()]  # nameは index=1
    data = {
        "action": action,
        "target_code": target_code,
        "actor": actor,
        "target_type": target_type,
    }
    use = [k for k in ["action", "target_type", "target_code", "actor"] if k in cols]
    sql = f"INSERT INTO operation_logs({', '.join(use)}) VALUES({', '.join(['?']*len(use))})"
    con.execute(sql, [data[k] for k in use])

def restore_part(asset_code: str, *, actor: str | None = None) -> None:
    actor = actor or os.environ.get("USERNAME") or "unknown"
    with connect() as con:
        con.execute("BEGIN IMMEDIATE")
        cur = con.execute(
            "UPDATE parts SET status='ACTIVE', updated_at=CURRENT_TIMESTAMP WHERE asset_code=?",
            (asset_code,),
        )
        if cur.rowcount != 1:
            raise ValueError(f"part not found: {asset_code}")

        con.execute(
            "INSERT INTO operation_logs(action,target_type,target_code,actor) VALUES(?,?,?,?)",
            ("PART_RESTORE", "PART", asset_code, actor),
        )
        con.commit()
