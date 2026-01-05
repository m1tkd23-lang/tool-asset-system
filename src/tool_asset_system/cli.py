#src/tool_asset_system/cli.py
from __future__ import annotations
import argparse

from tool_asset_system.services.parts import add_part

def main(argv=None):
    p = argparse.ArgumentParser("tool-asset")
    sub = p.add_subparsers(dest="cmd", required=True)

    p_parts = sub.add_parser("parts")
    sub_parts = p_parts.add_subparsers(dest="sub", required=True)

    p_add = sub_parts.add_parser("add")
    p_add.add_argument("--layer", required=True)
    p_add.add_argument("--category")
    p_add.add_argument("--category-free")
    p_add.add_argument("--part-no", required=True)
    p_add.add_argument("--maker", required=True)
    p_add.add_argument("--unit", default="EA")

    args = p.parse_args(argv)

    if args.cmd == "parts" and args.sub == "add":
        asset_code = add_part(
            layer_code=args.layer,
            category_code=args.category,
            category_free_text=args.category_free,
            part_no=args.part_no,
            maker=args.maker,
            stock_unit=args.unit,
        )
        print(f"[parts] added: {asset_code}")

if __name__ == "__main__":
    main()
