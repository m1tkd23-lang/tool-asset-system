# src/tool_asset_system/web/routes_assemblies.py
from __future__ import annotations

from flask import Blueprint, render_template, request, redirect, url_for, flash, abort

from tool_asset_system.db.db import connect
from tool_asset_system.services.parts import list_parts
from tool_asset_system.services.assemblies import (
    add_assembly,
    list_assemblies,
    get_assembly,
    update_assembly,
    list_assembly_items,
    add_assembly_item,
    remove_assembly_item,
    make_signature_from_items,
)

bp = Blueprint("assemblies", __name__)


# =========================
# Dict helpers (SSOT)
# =========================
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


def _get_label_maps():
    """表示用：code -> label（辞書テーブルがSSOT）"""
    with connect() as con:
        layer_labels = {
            r["code"]: r["label"]
            for r in con.execute("SELECT code,label FROM layers").fetchall()
        }
        category_labels = {
            r["code"]: r["label"]
            for r in con.execute("SELECT code,label FROM categories").fetchall()
        }
        status_labels = {
            r["code"]: r["label"]
            for r in con.execute("SELECT code,label FROM statuses").fetchall()
        }
    return layer_labels, category_labels, status_labels


def _role_choices_by_layer() -> dict[str, list[str]]:
    """
    role は「レイヤーに連動したプルダウン」を作るための候補。
    今は最小限でOK（必要なら増やす）。
    """
    return {
        "HOLDER": ["HOLDER"],
        "SUB_HOLDER": ["SUB_HOLDER"],
        "TOOL_BODY": ["TOOL_BODY"],
        "INSERT": ["INSERT"],
        "SOLID_TOOL": ["SOLID_TOOL"],
        "SCREW": ["SCREW"],
        "ACCESSORY": ["ACCESSORY"],
    }


# =========================
# Routes
# =========================
@bp.get("/assemblies")
def assemblies_list():
    q = request.args.get("q") or None
    rows = list_assemblies(q=q, limit=500)
    return render_template("assemblies_list.html", rows=rows, current={"q": q})


@bp.route("/assemblies/new", methods=["GET", "POST"])
def assemblies_new():
    """
    New Assembly:
      - parts を検索して選択（GETパラメータで絞り込み）
      - ASMを作り、選択したpartsを一括で assembly_items に入れる（POST）
      - itemsから signature を作って display_name に反映（display_name未入力時）
      - 成功時は /assemblies/new?created=ASM_xxx に戻す（JSが通知＆リセット）
    """
    # ---- parts 検索条件（GETで渡ってくる想定。POSTでも request.values で拾える）
    layer = request.values.get("layer") or ""
    category = request.values.get("category") or ""
    status = request.values.get("status") or "ACTIVE"
    q = request.values.get("q") or ""

    layers = _get_layers()
    categories = _get_categories_for_layer(layer) if layer else []

    # ---- parts検索結果
    parts_rows = list_parts(
        layer_code=layer or None,
        category_code=category or None,
        status=status or None,
        q=q or None,
        limit=500,
    )

    # ---- labels / roles
    layer_labels, category_labels, status_labels = _get_label_maps()
    role_choices_by_layer = _role_choices_by_layer()

    # ---- 成功通知用（JSが拾う）
    created = request.args.get("created")  # GETだけ

    if request.method == "POST":
        action = (request.form.get("action") or "").strip() or "create"
        if action != "create":
            # いまはPOSTはcreate専用の想定（SearchはGETに分離済み）
            return redirect(url_for("assemblies.assemblies_new", layer=layer, category=category, status=status, q=q))

        display_name = (request.form.get("display_name") or "").strip() or None
        tol_s = (request.form.get("tool_overall_length") or "").strip()
        td_s = (request.form.get("tool_diameter") or "").strip()
        note = (request.form.get("note") or "").strip() or None

        selected_parts = request.form.getlist("selected_parts")  # asset_codeの配列（JSがhiddenで作る）

        def to_float_or_none(s: str):
            if s == "":
                return None
            return float(s)

        if not selected_parts:
            flash("選択された parts がありません（チェックしてください）", "err")
            return render_template(
                "assemblies_new.html",
                form=request.form,
                layers=layers,
                categories=categories,
                current={"layer": layer, "category": category, "status": status, "q": q},
                parts_rows=parts_rows,
                layer_labels=layer_labels,
                category_labels=category_labels,
                status_labels=status_labels,
                role_choices_by_layer=role_choices_by_layer,
                created=created,
            )

        try:
            code = add_assembly(
                display_name=display_name,  # Noneなら仮名（services側）
                tool_overall_length=to_float_or_none(tol_s),
                tool_diameter=to_float_or_none(td_s),
                note=note,
            )

            # items追加
            for ac in selected_parts:
                role = (request.form.get(f"role_{ac}") or "").strip() or None
                qty_s = (request.form.get(f"qty_{ac}") or "1").strip()
                qty = float(qty_s) if qty_s != "" else 1.0
                add_assembly_item(code, part_asset_code=ac, qty=qty, role=role)

            # display_name が未入力なら signature を自動反映
            if display_name is None:
                items = list_assembly_items(code)
                sig = make_signature_from_items(items)
                if sig:
                    update_assembly(code, display_name=sig)

            # ✅ ここが重要：成功時は new へ戻し、created を付与
            # → JSが「通知＋選択解除＋フィルタ初期化」に使う
            flash(f"Created: {code}", "ok")
            return redirect(url_for("assemblies.assemblies_new", created=code, reset=1))

        except Exception as e:
            flash(str(e), "err")
            # fallthrough -> re-render with current state

    return render_template(
        "assemblies_new.html",
        form=request.form,
        layers=layers,
        categories=categories,
        current={"layer": layer, "category": category, "status": status, "q": q},
        parts_rows=parts_rows,
        layer_labels=layer_labels,
        category_labels=category_labels,
        status_labels=status_labels,
        role_choices_by_layer=role_choices_by_layer,
        created=created,
    )


@bp.get("/assemblies/<assembly_code>")
def assembly_detail(assembly_code: str):
    try:
        assembly = get_assembly(assembly_code)
    except Exception:
        abort(404)

    items = list_assembly_items(assembly_code, limit=500)
    signature = make_signature_from_items(items)

    return render_template(
        "assemblies_detail.html",
        assembly=assembly,
        items=items,
        signature=signature,
    )


@bp.post("/assemblies/<assembly_code>/update")
def assembly_update(assembly_code: str):
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

    try:
        update_assembly(
            assembly_code,
            display_name=get_optional("display_name"),
            tool_overall_length=get_float("tool_overall_length"),
            tool_diameter=get_float("tool_diameter"),
            note=get_optional("note"),
        )
        flash("Updated.", "ok")
    except Exception as e:
        flash(str(e), "err")

    return redirect(url_for("assemblies.assembly_detail", assembly_code=assembly_code))


@bp.post("/assemblies/<assembly_code>/items/<int:item_id>/remove")
def assembly_item_remove(assembly_code: str, item_id: int):
    try:
        remove_assembly_item(assembly_code, item_id=item_id)
        flash("Item removed.", "ok")
    except Exception as e:
        flash(str(e), "err")

    return redirect(url_for("assemblies.assembly_detail", assembly_code=assembly_code))
