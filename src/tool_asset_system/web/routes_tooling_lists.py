#src/tool_asset_system/web/routes_tooling_lists.py
from __future__ import annotations

from flask import Blueprint, render_template, request, redirect, url_for, flash, abort

from tool_asset_system.services.assemblies import list_assemblies
from tool_asset_system.services.tooling_lists import (
    add_tooling_list,
    list_tooling_lists,
    get_tooling_list,
    update_tooling_list,
    add_tooling_list_item,
    remove_tooling_list_item,
    list_tooling_list_items,
)

bp = Blueprint("tooling_lists", __name__)


@bp.get("/tooling_lists")
def tooling_lists_list():
    q = request.args.get("q") or None
    rows = list_tooling_lists(q=q, limit=500)
    return render_template("tooling_lists_list.html", rows=rows, current={"q": q})


@bp.route("/tooling_lists/new", methods=["GET", "POST"])
def tooling_lists_new():
    # assemblies 検索（GET）
    q = request.values.get("q") or ""
    asm_rows = list_assemblies(q=q or None, limit=500)

    created = request.args.get("created")  # GET only

    if request.method == "POST":
        title = (request.form.get("title") or "").strip()
        note = (request.form.get("note") or "").strip() or None

        selected_asms = request.form.getlist("selected_assemblies")  # JSがhiddenで作る

        if not title:
            flash("title が未入力です", "err")
            return render_template(
                "tooling_lists_new.html",
                current={"q": q},
                asm_rows=asm_rows,
                form=request.form,
                created=created,
            )

        if not selected_asms:
            flash("選択された ASM がありません（チェックしてください）", "err")
            return render_template(
                "tooling_lists_new.html",
                current={"q": q},
                asm_rows=asm_rows,
                form=request.form,
                created=created,
            )

        try:
            list_code = add_tooling_list(title=title, note=note)

            for ac in selected_asms:
                tool_no = (request.form.get(f"tool_no_{ac}") or "").strip()
                qty_s = (request.form.get(f"qty_{ac}") or "1").strip()
                qty = float(qty_s) if qty_s != "" else 1.0
                add_tooling_list_item(
                    list_code,
                    assembly_code=ac,
                    tool_no=tool_no,
                    qty=qty,
                )

            flash(f"Created: {list_code}", "ok")
            return redirect(url_for("tooling_lists.tooling_lists_new", created=list_code, reset=1))

        except Exception as e:
            flash(str(e), "err")

    return render_template(
        "tooling_lists_new.html",
        current={"q": q},
        asm_rows=asm_rows,
        form=request.form,
        created=created,
    )


@bp.get("/tooling_lists/<list_code>")
def tooling_list_detail(list_code: str):
    try:
        tl = get_tooling_list(list_code)
    except Exception:
        abort(404)

    items = list_tooling_list_items(list_code, limit=500)
    return render_template("tooling_lists_detail.html", tl=tl, items=items)


@bp.post("/tooling_lists/<list_code>/update")
def tooling_list_update(list_code: str):
    title = request.form.get("title")
    note = request.form.get("note")

    try:
        update_tooling_list(list_code, title=title, note=note)
        flash("Updated.", "ok")
    except Exception as e:
        flash(str(e), "err")

    return redirect(url_for("tooling_lists.tooling_list_detail", list_code=list_code))


@bp.post("/tooling_lists/<list_code>/items/<int:item_id>/remove")
def tooling_list_item_remove(list_code: str, item_id: int):
    try:
        remove_tooling_list_item(list_code, item_id=item_id)
        flash("Item removed.", "ok")
    except Exception as e:
        flash(str(e), "err")

    return redirect(url_for("tooling_lists.tooling_list_detail", list_code=list_code))
