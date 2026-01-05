#src/tool_asset_system/web/routes_api.py
from __future__ import annotations

from flask import Blueprint, request, jsonify

from tool_asset_system.db.db import connect

bp = Blueprint("api", __name__)

@bp.get("/categories")
def categories():
    layer = request.args.get("layer")
    if not layer:
        return jsonify([])

    with connect() as con:
        rows = con.execute(
            """
            SELECT code,label,is_active
            FROM categories
            WHERE layer_code = ?
            ORDER BY sort_order, code
            """,
            (layer,),
        ).fetchall()

    return jsonify([dict(r) for r in rows])
