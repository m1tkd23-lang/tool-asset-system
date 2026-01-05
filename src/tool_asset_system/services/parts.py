# src/tool_asset_system/services/parts.py
from __future__ import annotations
from tool_asset_system.db.db import connect
from tool_asset_system.services.idgen import issue_asset_code

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
        # lock for safe sequence + atomic insert
        con.execute("BEGIN IMMEDIATE")

        asset_code = issue_asset_code(con, layer_code=layer_code)

        con.execute(
            """
            INSERT INTO parts(
              asset_code,
              layer_code, category_code, category_free_text,
              part_no,
              maker, maker_part_name,
              display_name,
              stock_unit
            )
            VALUES(?,?,?,?,?,?,?,?,?)
            """,
            (
                asset_code,
                layer_code, category_code, category_free_text,
                part_no,
                maker, maker_part_name,
                display_name,
                stock_unit,
            ),
        )

        con.commit()
        return asset_code