#!/usr/bin/env python3
"""okf-devkit のテストを一括実行する。

    python tests/run_all.py [-v]

標準ライブラリの unittest のみを使う（追加依存なし）。本物のリポジトリには
触れず、すべて一時ディレクトリ上のバンドル / git リポジトリで検証する。
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
# `pip install -e .` 前でも動くよう src/ をパスに載せる。
for path in (str(HERE.parent / "src"), str(HERE)):
    if path not in sys.path:
        sys.path.insert(0, path)


def main(argv: list[str] | None = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    verbosity = 2 if ("-v" in argv or "--verbose" in argv) else 1

    loader = unittest.TestLoader()
    suite = loader.discover(start_dir=str(HERE), pattern="test_*.py", top_level_dir=str(HERE))

    print("=" * 60)
    print("okf-devkit テスト")
    print("=" * 60)
    result = unittest.TextTestRunner(verbosity=verbosity, stream=sys.stderr).run(suite)

    print("=" * 60)
    print(f"実行 {result.testsRun} 件 / 失敗 {len(result.failures)} 件 / エラー {len(result.errors)} 件"
          f" / スキップ {len(result.skipped)} 件")
    print("すべて成功しました。" if result.wasSuccessful() else "失敗があります。")
    print("=" * 60)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")  # Windows のコンソール対策
        except Exception:
            pass
    sys.exit(main())
