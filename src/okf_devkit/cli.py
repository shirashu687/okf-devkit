#!/usr/bin/env python3
"""CLI entry: resolve projects, dispatch commands, preserve legacy exports.

Canonical parsing, models, Git helpers and commands have separate owners.
Mutable legacy injection state and public constructor classes remain here.
"""
from __future__ import annotations

import sys
from pathlib import Path
from . import compat, parser, config as _config, yamlio as _yamlio
from .doc import Doc as _Doc

PACKAGE_DIR = Path(__file__).resolve().parent
SCAFFOLD_DIR = PACKAGE_DIR / "scaffold"
REPO_ROOT = Path.cwd()
_pyyaml = _yamlio._pyyaml
_PATH_TIME_MAP: dict[str, str] | None = None
_PATH_TIME_ROOT: Path | None = None


class Doc(_Doc):
    """Legacy Doc constructor using the current injected project root."""
    def __init__(self, path: Path, bundle_root: Path, *, repo_root: Path | None = None):
        super().__init__(path, bundle_root, repo_root=REPO_ROOT if repo_root is None else repo_root)


class Bundle(_config.Bundle):
    """Legacy Bundle constructor using the current injected project root."""
    def __init__(self, config_path: Path | None = None):
        super().__init__(config_path, repo_root=REPO_ROOT, doc_factory=Doc, defaults_path=DEFAULTS_PATH)


compat.install_legacy_exports(globals())


def build_parser() -> argparse.ArgumentParser:
    return parser.build_parser()


def resolve_root(args) -> Path:
    """プロジェクトルートを決める。``--root`` > ``--config`` の親 > 自動探索。"""
    if getattr(args, "root", None):
        root = Path(args.root).expanduser().resolve()
        if not root.is_dir():
            raise OkfError(f"--root がディレクトリではありません: {root}")
        return root
    if getattr(args, "config", None):
        return Path(args.config).expanduser().resolve().parent
    return find_project_root()


def main(argv: list[str] | None = None) -> int:
    global REPO_ROOT, _PATH_TIME_MAP
    args = build_parser().parse_args(argv)
    gate = args.command == "sync" and getattr(args, "gate", False)
    try:
        REPO_ROOT = resolve_root(args)
        # A repeated CLI invocation must observe new commits even in the same root.
        _PATH_TIME_MAP = None
        if args.command == "init":
            return cmd_init(args)
        bundle = Bundle(Path(args.config) if args.config else None)
        if not bundle.root.exists():
            raise OkfError(f"バンドルルートがありません: {bundle.root}")
        handlers = {
            "index": cmd_index,
            "log": cmd_log,
            "lint": cmd_lint,
            "stale": cmd_stale,
            "affected": cmd_affected,
            "new": cmd_new,
            "status": cmd_status,
            "render": cmd_render,
            "sync": cmd_sync,
        }
        return handlers[args.command](bundle, args)
    except OkfError as exc:
        print(f"エラー: {exc}", file=sys.stderr)
        if gate:
            # gate 中の運用エラーは fail-open にせず、安全側（差し戻し）に倒す
            print("[okf gate] 上記エラーのため検証を完了できませんでした。", file=sys.stderr)
            return 2
        return 1


def run() -> int:
    """コンソールスクリプト（`okf`）のエントリーポイント。"""
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # Windows のコンソール対策
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:  # pragma: no cover
        pass
    return main()


if __name__ == "__main__":
    sys.exit(run())
