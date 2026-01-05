#src/tool_asset_system/web/routes_parts.py

from __future__ import annotations

from flask import Blueprint, render_template, request, redirect, url_for, flash

from tool_asset_system.db.db import connect
from tool_asset_system.services.parts import add_part, list_parts

bp = Blueprint("parts", __name__)

def _get_layers():
    with connect() as con:
        return con.execute(
            "SELECT code,label,allow_free_category FROM layers ORDER BY sort_order"
        ).fetchall()

def _get_categories_for_layer(layer_code: str):
    with connect() as con:
        return con.execute(
            """
            SELECT code,label,is_active
            FROM categories
            WHERE layer_code = ?
            ORDER BY sort_order, code
            """,
            (layer_code,),
        ).fetchall()

@bp.get("/")
def home():
    return redirect(url_for("parts.parts_list"))

@bp.get("/parts")
def parts_list():
    layer = request.args.get("layer") or None
    category = request.args.get("category") or None
    status = request.args.get("status") or None
    q = request.args.get("q") or None

    rows = list_parts(layer_code=layer, category_code=category, status=status, q=q, limit=500)
    layers = _get_layers()
    categories = _get_categories_for_layer(layer) if layer else []

    return render_template(
        "parts_list.html",
        rows=rows,
        layers=layers,
        categories=categories,
        current=dict(layer=layer, category=category, status=status, q=q),
    )

@bp.route("/parts/new", methods=["GET", "POST"])
def parts_new():
    layers = _get_layers()

    if request.method == "POST":
        layer = (request.form.get("layer") or "").strip()
        category = (request.form.get("category") or "").strip() or None
        category_free = (request.form.get("category_free") or "").strip() or None
        maker = (request.form.get("maker") or "").strip()
        part_no = (request.form.get("part_no") or "").strip()
        unit = (request.form.get("unit") or "EA").strip()
        name = (request.form.get("name") or "").strip() or None
        maker_part_name = (request.form.get("maker_part_name") or "").strip() or None

        try:
            asset_code = add_part(
                layer_code=layer,
                category_code=category,
                category_free_text=category_free,
                part_no=part_no,
                maker=maker,
                stock_unit=unit,
                display_name=name,
                maker_part_name=maker_part_name,
            )
            flash(f"Added: {asset_code}", "ok")
            return redirect(url_for("parts.parts_list"))
        except Exception as e:
            flash(str(e), "err")
            # fallthrough to re-render with form values

    # GET or error re-render
    selected_layer = request.values.get("layer") or (layers[0]["code"] if layers else None)
    categories = _get_categories_for_layer(selected_layer) if selected_layer else []

    return render_template(
        "parts_new.html",
        layers=layers,
        categories=categories,
        selected_layer=selected_layer,
        form=request.form,
    )
