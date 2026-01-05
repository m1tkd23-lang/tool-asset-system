# src/tool_asset_system/cli.py
from __future__ import annotations

import argparse
import json

from tool_asset_system.services.parts import (
    add_part,
    list_parts,
    get_part,
    update_part,
    archive_part,
)


def main(argv=None):
    p = argparse.ArgumentParser("tool-asset")
    sub = p.add_subparsers(dest="cmd", required=True)

    p_parts = sub.add_parser("parts")
    sub_parts = p_parts.add_subparsers(dest="sub", required=True)

    # parts add
    p_add = sub_parts.add_parser("add")
    p_add.add_argument("--layer", required=True)
    p_add.add_argument("--category")
    p_add.add_argument("--category-free")
    p_add.add_argument("--part-no", required=True)
    p_add.add_argument("--maker", required=True)
    p_add.add_argument("--unit", default="EA")
    p_add.add_argument("--name")
    p_add.add_argument("--maker-part-name")

    # parts list
    p_list = sub_parts.add_parser("list")
    p_list.add_argument("--layer")
    p_list.add_argument("--category")
    p_list.add_argument("--status")
    p_list.add_argument("--q")
    p_list.add_argument("--limit", type=int, default=200)

    # parts show
    p_show = sub_parts.add_parser("show")
    p_show.add_argument("asset_code")

    # parts update
    p_upd = sub_parts.add_parser("update")
    p_upd.add_argument("asset_code")
    p_upd.add_argument("--layer")
    p_upd.add_argument("--category")
    p_upd.add_argument("--category-free")
    p_upd.add_argument("--name")
    p_upd.add_argument("--note")
    p_upd.add_argument("--status")
    p_upd.add_argument("--reason")  # 任意（ログに残す）

    # parts archive
    p_arc = sub_parts.add_parser("archive")
    p_arc.add_argument("asset_code")
    p_arc.add_argument("--reason", required=True)

    args = p.parse_args(argv)

    if args.cmd == "parts" and args.sub == "add":
        asset_code = add_part(
            layer_code=args.layer,
            category_code=args.category,
            category_free_text=args.category_free,
            part_no=args.part_no,
            maker=args.maker,
            stock_unit=args.unit,
            display_name=args.name,
            maker_part_name=args.maker_part_name,
        )
        print(f"[parts] added: {asset_code}")
        return

    if args.cmd == "parts" and args.sub == "list":
        rows = list_parts(
            layer_code=args.layer,
            category_code=args.category,
            status=args.status,
            q=args.q,
            limit=args.limit,
        )
        for r in rows:
            # 最小表示：現場で見たい順
            print(f"{r['asset_code']}  {r['layer_code']}  {r.get('category_code')}  {r['status']}  {r['maker']}  {r['part_no']}  {r['display_name']}")
        return

    if args.cmd == "parts" and args.sub == "show":
        r = get_part(args.asset_code)
        print(json.dumps(r, ensure_ascii=False, indent=2))
        return

    if args.cmd == "parts" and args.sub == "update":
        patch = {}
        if args.layer is not None:
            patch["layer_code"] = args.layer
        if args.category is not None:
            patch["category_code"] = args.category
        if args.category_free is not None:
            patch["category_free_text"] = args.category_free
        if args.name is not None:
            patch["display_name"] = args.name
        if args.note is not None:
            patch["note"] = args.note
        if args.status is not None:
            patch["status"] = args.status

        if not patch:
            raise SystemExit("no fields to update")

        update_part(args.asset_code, patch=patch, reason=args.reason)
        print(f"[parts] updated: {args.asset_code}")
        return

    if args.cmd == "parts" and args.sub == "archive":
        archive_part(args.asset_code, reason=args.reason)
        print(f"[parts] archived: {args.asset_code}")
        return


if __name__ == "__main__":
    main()
