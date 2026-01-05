# src/tool_asset_system/services/idgen.py
from __future__ import annotations
import sqlite3

def issue_asset_code(con: sqlite3.Connection, layer_code: str, width: int = 8, sep: str = "_") -> str:
    """
    Issue unique asset_code like INSERT_00000001.
    Assumes id_sequences(layer_code, next_no) exists.
    Must be called inside a transaction.
    """
    row = con.execute(
        "SELECT next_no FROM id_sequences WHERE layer_code = ?",
        (layer_code,),
    ).fetchone()

    if row is None:
        raise ValueError(f"id_sequences has no row for layer_code={layer_code!r}")

    next_no = int(row[0])
    asset_code = f"{layer_code}{sep}{next_no:0{width}d}"

    con.execute(
        "UPDATE id_sequences SET next_no = next_no + 1 WHERE layer_code = ?",
        (layer_code,),
    )
    return asset_code
