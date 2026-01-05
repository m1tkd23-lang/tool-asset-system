from __future__ import annotations

from tool_asset_system.db.db import connect
from tool_asset_system.domain.tool_schema import (
    is_valid_layer,
    is_valid_category,
    allows_free_category,
)

def add_part(
    layer_code: str,
    category_code: str | None,
    category_free_text: str | None,
    part_no: str,
    maker: str,
    display_name: str | None = None,
    stock_unit: str = "EA",
    note: str | None = None,
) -> None:

    if not is_valid_layer(layer_code):
        raise SystemExit(f"[parts] invalid layer: {layer_code}")

    if allows_free_category(layer_code):
        if not (category_code or category_free_text):
            raise SystemExit("[parts] category required (code or free text)")
    else:
        if not category_code:
            raise SystemExit("[parts] category_code required for this layer")
        if not is_valid_category(layer_code, category_code):
            raise SystemExit(f"[parts] invalid category {category_code} for {layer_code}")

    dn = display_name or part_no

    with connect() as con:
        con.execute(
            """
            INSERT INTO parts(
              layer_code,
              category_code,
              category_free_text,
              part_no,
              display_name,
              maker,
              stock_unit,
              note
            )
            VALUES(?,?,?,?,?,?,?,?)
            """,
            (
                layer_code,
                category_code,
                category_free_text,
                part_no,
                dn,
                maker,
                stock_unit,
                note,
            ),
        )
        con.commit()

    print(f"[parts] added: {part_no}")
