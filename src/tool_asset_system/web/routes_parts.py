#src/tool_asset_system/web/routes_parts.py

from __future__ import annotations

from flask import Blueprint, render_template, request, redirect, url_for, flash

from tool_asset_system.db.db import connect
from tool_asset_system.services.parts import update_part, archive_part
from tool_asset_system.services.parts import add_part, list_parts
from flask import abort



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

@bp.get("/parts/<asset_code>")
def part_detail(asset_code: str):
    with connect() as con:
        part = con.execute(
            """
            SELECT
              asset_code,
              layer_code, category_code, category_free_text,
              status,
              maker, part_no, maker_part_name,
              display_name,
              stock_qty, stock_unit,
              pack_qty, unit_price, supplier,
              lead_time_days, min_stock_qty,
              note,
              created_at, updated_at
            FROM parts
            WHERE asset_code = ?
            """,
            (asset_code,),
        ).fetchone()

        if part is None:
            abort(404)

        # operation_logs の列は将来変わる可能性があるので、存在する列だけ表示する
        cols = [r["name"] for r in con.execute("PRAGMA table_info(operation_logs)").fetchall()]
        want = ["id", "action", "target_code", "actor", "created_at"]
        select_cols = [c for c in want if c in cols]
        if not select_cols:
            # 最低限の保険：テーブルがあっても想定列が無い場合
            logs = []
        else:
            sql = f"""
            SELECT {", ".join(select_cols)}
            FROM operation_logs
            WHERE target_code = ?
            ORDER BY id DESC
            LIMIT 50
            """
            logs = con.execute(sql, (asset_code,)).fetchall()

    return render_template("parts_detail.html", part=part, logs=logs)

@bp.route("/parts/<asset_code>/edit", methods=["GET", "POST"])
def part_edit(asset_code: str):
    if request.method == "POST":
        # 空欄は「変更なし」にしたいので、フォーム値の取り扱いを丁寧に
        def get_optional(name: str):
            v = request.form.get(name)
            if v is None:
                return None
            v = v.strip()
            return v if v != "" else None

        def get_float(name: str):
            v = request.form.get(name, "").strip()
            if v == "":
                return None
            return float(v)

        def get_int(name: str):
            v = request.form.get(name, "").strip()
            if v == "":
                return None
            return int(v)

        update_part(
            asset_code,
            display_name=get_optional("display_name"),
            maker_part_name=get_optional("maker_part_name"),
            note=get_optional("note"),
            stock_qty=get_float("stock_qty"),
            stock_unit=get_optional("stock_unit"),
            unit_price=get_float("unit_price"),
            supplier=get_optional("supplier"),
            lead_time_days=get_int("lead_time_days"),
            min_stock_qty=get_float("min_stock_qty"),
        )
        flash("Updated.", "ok")
        return redirect(url_for("parts.part_detail", asset_code=asset_code))

    # GET: 現在値を読み込み
    with connect() as con:
        part = con.execute("SELECT * FROM parts WHERE asset_code=?", (asset_code,)).fetchone()
    if part is None:
        abort(404)
    return render_template("parts_edit.html", part=part)

@bp.post("/parts/<asset_code>/archive")
def part_archive(asset_code: str):
    archive_part(asset_code)
    flash("Archived.", "ok")
    return redirect(url_for("parts.part_detail", asset_code=asset_code))
