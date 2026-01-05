# apps/main.py

"""
アプリケーションのエントリポイント。
CLI / GUI / Web いずれの場合も、このファイルは"薄く"保つ。
"""
from __future__ import annotations
from tool_asset_system.core import main

if __name__ == "__main__":
    main()
