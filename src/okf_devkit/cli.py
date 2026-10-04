#!/usr/bin/env python3
"""OKF v0.2 バンドルを開発リポジトリで運用するための CLI（okf-devkit）。

決定的に処理できることはすべてこのスクリプトに寄せ、LLM のクレジットは
「文章の中身を書く」非決定的な作業にだけ使う、という方針で作られている。

    okf <command> [options]

    init      リポジトリに OKF バンドルと設定一式を生成する
    index     各ディレクトリの index.md を frontmatter から再生成する
    log       git 履歴から各層の log.md に追記する（冪等）
    lint      OKF 適合 + 独自語彙の検証（CONVENTIONS.md §10 の L1〜L13）
    stale     陳腐化レポート（expired / orphan / outdated / unverified / draft-stale）
    affected  変更パスから更新すべきドキュメントを列挙する
    new       backlog / doc の雛形を生成する（ID 採番込み）
    status    backlog の集計を表示する
    render    バンドルの Markdown を閲覧用 HTML に変換する
    sync      index → log → lint → stale を一括実行する

設定は「パッケージ同梱の defaults.yml」＋「プロジェクトルートの okf.yml」を
マージして決まる。普遍的な語彙は defaults.yml 側にあるので、各リポジトリの
okf.yml には固有の設定（bundle_root / layer / log 出力先）だけを書けばよい。

依存は markdown-it-py（render のみ）と PyYAML。PyYAML が無い環境では内蔵の
厳格な簡易 YAML パーサにフォールバックする（frontmatter のサブセットのみ
対応。曖昧な構文は黙って誤読せず、明確なエラーにする）。

安全性に関する設計方針:

* すべてのファイル書き込みは同一ディレクトリの一時ファイル + fsync +
  ``os.replace()`` による**原子的置換**で行う（中断・容量不足・Windows の
  共有違反で壊れたファイルを残さない）。
* ``index`` は自動生成マーカーの個数・順序を書き込み**前**に検証し、
  1 箇所でも壊れていればどのファイルも書かずに停止する。
* ``log`` は ``config.yml`` の ``log.baseline`` より後のコミットだけを対象にする。
  baseline 未設定でハッシュ無しの既存エントリがある場合は書き込みを拒否する。
* ``sync --gate`` は「同じ lint error 集合に対して exit 2 を返した回数」を
  数える（正常終了や別のエラーではリセットされる）。
"""

from __future__ import annotations

from . import gitutil
from .gitutil import Commit, _parse_log_z, _consume_change, parse_porcelain_z

import argparse
import datetime as _dt
import glob as _glob
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import threading
import time
import webbrowser
from pathlib import Path, PurePosixPath

from . import yamlio as _yamlio
from . import config as _config
from .doc import Doc as _Doc, CODE_GLOBS_REQUIRED_TYPES
from .config import CONFIG_FILENAME, DEFAULTS_PATH, RESERVED_DEFAULT, INDEX_LINK_STYLES, merge_config

# Legacy direct-call injection seam; normal parsing belongs to yamlio.
_pyyaml = _yamlio._pyyaml


# =============================================================================
# 基本ユーティリティ
# =============================================================================

PACKAGE_DIR = Path(__file__).resolve().parent
SCAFFOLD_DIR = PACKAGE_DIR / "scaffold"

#: プロジェクト設定のファイル名。この存在がプロジェクトルートの定義になる。

#: プロジェクトルート。``main()`` が起動時に確定させる。
#: モジュール読み込み時のパスに依存させないため、既定は CWD にしておく
#: （インストール済みパッケージは自分の位置からリポジトリを推測できない）。
REPO_ROOT = Path.cwd()


def find_project_root(start: Path | None = None) -> Path:
    """``okf.yml`` を持つ最も近い祖先ディレクトリを返す。

    見つからない場合は git のトップレベルへフォールバックし、それも無ければ
    起点をそのまま返す（``init`` は設定が無い状態から動く必要があるため、
    ここでは例外にしない）。
    """
    here = (start or Path.cwd()).resolve()
    for candidate in (here, *here.parents):
        if (candidate / CONFIG_FILENAME).is_file():
            return candidate
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=str(here), capture_output=True, text=True, check=True,
        ).stdout.strip()
        if out:
            return Path(out).resolve()
    except Exception:
        pass
    return here


# ``index.link_style`` は index.md の出力形式だけを切り替える。
# frontmatter の ``related`` や ``Doc.bundle_rel`` の意味は変えない。

# `code_globs`（更新検知の起点）を必須とする type。
# コードから導出されるドキュメントのみ対象で、Convention / Glossary /
# Decision Record / Backlog Item は対象外。`status: deprecated` も除外される。


from .errors import OkfError, MarkerError
from .fsutil import (
    rel_posix, read_text, atomic_write_bytes, write_if_changed, today, now_iso,
    ISO_DATE_RE, is_iso_date, extract_date, parse_datetime, glob_to_regex,
    path_matches, _GLOB_CACHE,
)


# =============================================================================
# YAML（PyYAML があれば PyYAML、無ければ内蔵の厳格な簡易パーサ）
# =============================================================================


from .yamlio import (
    YamlSubsetError, _normalize, _MINI_BOOL_TRUE, _MINI_BOOL_FALSE,
    _MINI_NULL, _MINI_INT_RE, _MINI_FLOAT_RE, _MINI_TS_RE,
    _mini_timestamp, _mini_scalar, _strip_inline_comment, _MiniYaml,
    _parse_flow, _flow_skip, _flow_value, _flow_scalar,
    _YAML_PLAIN_SAFE_RE, yaml_scalar, yaml_flow_list,
)


def parse_yaml(text: str, source: str = "<yaml>"):
    """Compatibility adapter for callers overriding cli._pyyaml directly."""
    return _yamlio.parse_yaml(text, source, backend=_pyyaml)


# =============================================================================
# frontmatter
# =============================================================================


class Doc(_Doc):
    """Temporary legacy constructor; canonical doc.Doc requires repo_root."""
    def __init__(self, path: Path, bundle_root: Path, *, repo_root: Path | None = None):
        super().__init__(path, bundle_root, repo_root=REPO_ROOT if repo_root is None else repo_root)


def load_merged_config(cfg_path: Path) -> dict:
    return _config.load_merged_config(cfg_path, defaults_path=DEFAULTS_PATH)


class Bundle(_config.Bundle):
    """Temporary legacy constructor capturing the currently injected CLI root."""
    def __init__(self, config_path: Path | None = None):
        super().__init__(config_path, repo_root=REPO_ROOT, doc_factory=Doc, defaults_path=DEFAULTS_PATH)


# =============================================================================
# git ヘルパー
# =============================================================================


def git(*args: str, cwd: Path | None = None) -> tuple[int, str]:
    return gitutil.git(REPO_ROOT, *args, cwd=cwd)


def git_available() -> bool:
    return gitutil.git_available(REPO_ROOT, runner=git)


def has_commits() -> bool:
    return gitutil.has_commits(REPO_ROOT, runner=git)


def is_shallow() -> bool:
    return gitutil.is_shallow(REPO_ROOT, runner=git)


def repo_web_url() -> str | None:
    return gitutil.repo_web_url(REPO_ROOT, runner=git)


def resolve_ref(ref: str) -> str | None:
    return gitutil.resolve_ref(REPO_ROOT, ref, runner=git)


def resolve_commit(ref: str) -> str | None:
    return gitutil.resolve_commit(REPO_ROOT, ref, runner=git)


# --- git log / status の -z 解析 -------------------------------------------


_PATH_TIME_MAP: dict[str, str] | None = None
_PATH_TIME_ROOT: Path | None = None


def path_commit_times() -> dict[str, str]:
    global _PATH_TIME_MAP, _PATH_TIME_ROOT
    cache = gitutil.CommitTimesCache(_PATH_TIME_ROOT, _PATH_TIME_MAP)
    result = gitutil.path_commit_times(REPO_ROOT, cache, runner=git)
    _PATH_TIME_MAP, _PATH_TIME_ROOT = cache.mapping, cache.root
    return result


def last_commit_time(paths: list[str]) -> str | None:
    return gitutil.latest_commit_time(paths, path_commit_times())


def resolve_resource(resource: str) -> list[str]:
    return gitutil.resolve_resource(REPO_ROOT, resource)


# =============================================================================
# index コマンド
# =============================================================================


from .commands import index as _index
from .commands.index import (
    md_escape_label, md_escape_link, md_escape_text, _entry_line, _index_link, _display_title, build_index_block, build_backlog_block, split_markers, _plan_index,
)

def render_index(bundle: Bundle, directory: Path, block: str) -> str:
    return _index.render_index(bundle, directory, block, repo_root=REPO_ROOT)

def cmd_index(bundle: Bundle, args) -> int:
    return _index.cmd_index(bundle, args, repo_root=REPO_ROOT, writer=write_if_changed)


# =============================================================================
# log コマンド
# =============================================================================


def collect_commits(rev_range: str | None, exclude: str | None=None) -> list[Commit]:
    return gitutil.collect_commits(REPO_ROOT, rev_range, exclude, runner=git)


from .commands import log as _log
from .commands.log import (
    layer_of, kind_of, format_log_line, recorded_hashes, hashless_entries, insert_log_entries, ENTRY_RE, HASH_RE,
)

def log_baseline_sha(bundle: Bundle) -> str | None:
    return _log.log_baseline_sha(bundle, repo_root=REPO_ROOT, runner=git)

def cmd_log(bundle: Bundle, args) -> int:
    return _log.cmd_log(bundle, args, repo_root=REPO_ROOT, runner=git, writer=write_if_changed)


# =============================================================================
# lint コマンド
# =============================================================================

from .commands import lint as _lint
from .commands.lint import (
    Finding, _check_actor_entry, trust_level, ACTOR_RE, SENTENCE_END_RE,
)

def run_lint(bundle: Bundle) -> list[Finding]:
    return _lint.run_lint(bundle, repo_root=REPO_ROOT, resource_resolver=resolve_resource, index_renderer=render_index)

def cmd_lint(bundle: Bundle, args) -> int:
    return _lint.cmd_lint(bundle, args, linter=run_lint)


# =============================================================================
# stale コマンド
# =============================================================================


from .commands import stale as _stale

def run_stale(bundle: Bundle) -> list[dict]:
    return _stale.run_stale(bundle, resource_resolver=resolve_resource, commit_time=last_commit_time)

def cmd_stale(bundle: Bundle, args) -> int:
    return _stale.cmd_stale(bundle, args, runner=git, reporter=run_stale)


# =============================================================================
# affected コマンド
# =============================================================================


def changed_paths(base: str) -> list[str]:
    return gitutil.changed_paths(REPO_ROOT, base, runner=git)


from .commands import affected as _affected
from .commands.affected import compute_affected

def cmd_affected(bundle: Bundle, args) -> int:
    return _affected.cmd_affected(bundle, args, path_provider=changed_paths)


# =============================================================================
# new コマンド
# =============================================================================

from .commands import new as _new
from .commands.new import (
    slugify, validate_slug, validate_subdir, set_fm_field, next_numbered_id, next_backlog_id, _validate_vocab, SLUG_RE,
)

def ensure_inside_bundle(bundle: Bundle, path: Path) -> Path:
    return _new.ensure_inside_bundle(bundle, path, repo_root=REPO_ROOT)

def load_template(bundle: Bundle, type_name: str) -> str:
    return _new.load_template(bundle, type_name, repo_root=REPO_ROOT)

def cmd_new(bundle: Bundle, args) -> int:
    return _new.cmd_new(bundle, args, repo_root=REPO_ROOT, writer=write_if_changed, template_loader=load_template, path_validator=ensure_inside_bundle)


# =============================================================================
# status コマンド
# =============================================================================


from .commands import status as _status

def backlog_docs(bundle: Bundle) -> list[Doc]:
    return _status.backlog_docs(bundle, repo_root=REPO_ROOT, doc_factory=Doc)

def cmd_status(bundle: Bundle, args) -> int:
    return _status.cmd_status(bundle, args, reader=backlog_docs)


# =============================================================================
# HTML レンダリング
# =============================================================================


from .commands import render as _render

def cmd_render(bundle: Bundle, args) -> int:
    return _render.cmd_render(bundle, args, repo_root=REPO_ROOT, doc_factory=Doc)


# =============================================================================
# sync コマンド
# =============================================================================

from .commands import sync as _sync
from .commands.sync import STDIN_LIMIT, STDIN_TIMEOUT, GATE_TTL, _read_stdin_json, findings_fingerprint

def gate_state_dir() -> Path:
    return _sync.gate_state_dir(REPO_ROOT, runner=git)

def _gate_state_file(session_id: str | None) -> Path:
    return _sync._gate_state_file(REPO_ROOT, session_id, state_dir=gate_state_dir)

def resolve_session_id(args) -> str | None:
    return _sync.resolve_session_id(args, payload_reader=_read_stdin_json)

def gate_bump(session_id: str | None, fingerprint: str | None) -> int:
    return _sync.gate_bump(REPO_ROOT, session_id, fingerprint, state_file_provider=_gate_state_file, ttl=GATE_TTL)

def _has_local_changes() -> bool:
    return _sync._has_local_changes(REPO_ROOT, runner=git)

def cmd_sync(bundle: Bundle, args) -> int:
    return _sync.cmd_sync(
        bundle, args, indexer=cmd_index, logger=cmd_log, linter=run_lint,
        stale_reporter=run_stale, dirty_checker=_has_local_changes,
        session_resolver=resolve_session_id, gate_counter=gate_bump,
    )


# =============================================================================
# init
# =============================================================================


from .commands import init as _init
from .commands.init import _parse_layer_specs

def _scaffold_text(rel: str) -> str:
    return _init._scaffold_text(rel, scaffold_dir=SCAFFOLD_DIR)

def _render_okf_yml(bundle_root: str, site_name: str, layers: list[tuple[str, str, str]]) -> str:
    return _init._render_okf_yml(bundle_root, site_name, layers, scaffold_reader=_scaffold_text)

def cmd_init(args) -> int:
    return _init.cmd_init(
        REPO_ROOT, args, scaffold_dir=SCAFFOLD_DIR, scaffold_reader=_scaffold_text,
        writer=write_if_changed, config_renderer=_render_okf_yml,
    )


# =============================================================================
# エントリーポイント
# =============================================================================


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="okf", description="OKF v0.2 バンドルを開発リポジトリで運用する CLI"
    )
    parser.add_argument(
        "--config", help=f"設定ファイルのパス（既定: プロジェクトルートの {CONFIG_FILENAME}）"
    )
    parser.add_argument(
        "--root", help="プロジェクトルート（既定: okf.yml を持つ最も近い祖先 / git トップ）"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_init = sub.add_parser("init", help="OKF バンドルと設定一式を生成する")
    p_init.add_argument("--bundle-root", default="docs", help="バンドルのルート（既定: docs）")
    p_init.add_argument("--site-name", help="ドキュメントの表示名（既定: ルートのディレクトリ名）")
    p_init.add_argument(
        "--layer", action="append", metavar="NAME=GLOB[:DIR]",
        help="層とコード配置の対応（例: client=src/client/**）。複数指定可",
    )
    p_init.add_argument("--force", action="store_true", help="既存ファイルを上書きする")

    p_index = sub.add_parser("index", help="index.md を再生成する")
    p_index.add_argument("--write", action="store_true", help="実際に書き込む")
    p_index.add_argument("--check", action="store_true", help="差分があれば exit 1（CI 用）")
    p_index.add_argument("--quiet", action="store_true", help="変更が無いときは何も出力しない")

    p_log = sub.add_parser("log", help="git 履歴から log.md に追記する")
    p_log.add_argument("--write", action="store_true", help="実際に書き込む")
    p_log.add_argument("--range", help="git のリビジョン範囲（例: A..B）")
    p_log.add_argument("--layer", help="対象の層を限定する")
    p_log.add_argument("--dry-run", action="store_true", help="書き込まずに内容を表示する")

    p_lint = sub.add_parser("lint", help="OKF 適合 + 語彙の検証")
    p_lint.add_argument("--strict", action="store_true", help="warn も exit 1 の対象にする")

    p_stale = sub.add_parser("stale", help="陳腐化レポート")
    p_stale.add_argument("--format", choices=["text", "json"], default="text")

    p_affected = sub.add_parser("affected", help="更新すべきドキュメントを列挙する")
    p_affected.add_argument("--base", default="main", help="比較対象のブランチ（既定: main）")
    p_affected.add_argument("--paths", nargs="+", help="変更パスを直接指定する")

    p_new = sub.add_parser("new", help="雛形を生成する")
    new_sub = p_new.add_subparsers(dest="kind", required=True)

    p_new_backlog = new_sub.add_parser("backlog", help="backlog アイテムを作る")
    p_new_backlog.add_argument("--title", required=True)
    p_new_backlog.add_argument("--layer", default="shared")
    p_new_backlog.add_argument("--priority", default="medium")
    p_new_backlog.add_argument("--effort", default="M")
    p_new_backlog.add_argument("--slug", help="ファイル名の slug（日本語タイトル時に指定する）")

    p_new_doc = new_sub.add_parser("doc", help="通常ドキュメントを作る")
    p_new_doc.add_argument("--layer", required=True)
    p_new_doc.add_argument("--type", required=True)
    p_new_doc.add_argument("--title", required=True)
    p_new_doc.add_argument("--dir", help="層ディレクトリ配下のサブディレクトリ")
    p_new_doc.add_argument("--code-globs", nargs="+", help="根拠コードのパス/glob（複数可、コード由来の型では必須）")
    p_new_doc.add_argument("--slug", help="ファイル名の slug")

    p_status = sub.add_parser("status", help="backlog の集計")
    p_status.add_argument("--format", choices=["text", "json"], default="text")

    p_render = sub.add_parser("render", help="Bundle の Markdown を閲覧用 HTML に変換する")
    p_render.add_argument("--output", help="出力先（既定: _site。旧配置は bundle_root を指定（例: docs））")
    p_render.add_argument("--open", action="store_true", help="生成後にトップページをブラウザで開く（check / hook 時は無効）")
    p_render.add_argument("--check", action="store_true", help="書き込まず、全ページを生成できるか検証する")
    p_render.add_argument("--hook", action="store_true", help="Stop hook 用。成功時は空の JSON だけを返す")

    p_render.add_argument("--cleanup-from", metavar="OLD", help="Move verified old renderer artifacts to backups; --check prints the plan")
    p_sync = sub.add_parser("sync", help="index → log → lint → stale を一括実行する")
    p_sync.add_argument("--gate", action="store_true", help="hook 用。error があれば exit 2")
    p_sync.add_argument("--session-id", help="gate のセッション識別子（既定: 環境変数 / stdin JSON）")

    return parser


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
