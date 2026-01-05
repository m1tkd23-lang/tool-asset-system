# src/tool_asset_system/core.py
"""
プロジェクトの中核ロジック（エントリ集約）。
CLI / GUI / Web の入口をここに集約していく。

- apps/main.py は薄く core.main() を呼ぶだけ
- core.main() は当面 CLI を起動する
"""

from __future__ import annotations

import sys
from typing import Sequence

from tool_asset_system.cli import main as cli_main


def main(argv: Sequence[str] | None = None) -> None:
    """
    Entry point.
    Default: delegate to CLI.
    """
    if argv is None:
        argv = sys.argv[1:]
    cli_main(list(argv))
