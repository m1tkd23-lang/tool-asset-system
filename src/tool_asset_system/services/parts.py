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
    patch: dict[str, Any],
    reason: str | None = None,
) -> None:
    """
    Update allowed fields and write operation log (mandatory).
    """
    allowed = {
        "layer_code", "category_code", "category_free_text",
        "display_name", "maker_part_name",
        "stock_qty", "stock_unit",
        "pack_qty", "unit_price", "supplier",
        "lead_time_days", "min_stock_qty",
        "status",
        "note",
    }

    unknown = set(patch.keys()) - allowed
    if unknown:
        raise ValueError(f"unknown fields in patch: {sorted(unknown)}")

    # normalize status
    if "status" in patch and patch["status"] is not None:
        patch["status"] = str(patch["status"]).upper()

    with connect() as con:
        con.execute("BEGIN IMMEDIATE")

        before = con.execute("SELECT * FROM parts WHERE asset_code = ?", (asset_code,)).fetchone()
        if before is None:
            raise ValueError(f"part not found: {asset_code}")

        new_layer = patch.get("layer_code", before["layer_code"])
        new_cat = patch.get("category_code", before["category_code"])

        # enforce policy/consistency
        _validate_category(con, layer_code=str(new_layer), category_code=(None if new_cat is None else str(new_cat)))

        # build SET clause
        sets: list[str] = []
        params: list[Any] = []

        for k, v in patch.items():
            sets.append(f"{k} = ?")
            params.append(v)

        sets.append("updated_at = CURRENT_TIMESTAMP")

        sql = f"UPDATE parts SET {', '.join(sets)} WHERE asset_code = ?"
        params.append(asset_code)

        con.execute(sql, params)

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
                "PART_UPDATE", "PART", asset_code,
                _actor(), reason,
                json.dumps(patch, ensure_ascii=False),
                json.dumps(_row_to_dict(before), ensure_ascii=False),
                json.dumps(_row_to_dict(after), ensure_ascii=False),
            ),
        )

        con.commit()


def archive_part(asset_code: str, *, reason: str) -> None:
    if not reason or not reason.strip():
        raise ValueError("reason is required for archive")

    update_part(asset_code, patch={"status": "ARCHIVED"}, reason=reason)
