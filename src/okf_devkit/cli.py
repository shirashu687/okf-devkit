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

STDIN_LIMIT = 1 << 20  # hook 入力の読み取り上限（1 MiB）
STDIN_TIMEOUT = 2.0    # 秒。EOF が来なくてもここで諦める（ハング防止）
GATE_TTL = 600         # session_id が無いときに同一セッションとみなす秒数


def gate_state_dir() -> Path:
    return gitutil.gate_state_dir(REPO_ROOT, runner=git)


def _gate_state_file(session_id: str | None) -> Path:
    key = re.sub(r"[^A-Za-z0-9_.-]", "_", session_id or "")[:80] or "_nosession"
    return gate_state_dir() / f"{key}.json"


def _read_stdin_json(timeout: float = STDIN_TIMEOUT, limit: int = STDIN_LIMIT) -> dict | None:
    """hook が stdin で渡す JSON を、ハングしない形で読む。

    `sys.stdin.read()` は EOF が来るまで無期限に待つため、別スレッドで
    サイズ上限付きに読み、タイムアウトしたら諦める（デーモンスレッドなので
    プロセス終了を妨げない）。
    """
    stream = getattr(sys.stdin, "buffer", sys.stdin)
    if stream is None:
        return None
    try:
        if sys.stdin.isatty():
            return None
    except Exception:
        return None

    box: dict = {}

    def worker() -> None:
        try:
            box["raw"] = stream.read(limit)
        except Exception:
            pass

    thread = threading.Thread(target=worker, daemon=True)
    thread.start()
    thread.join(timeout)
    raw = box.get("raw")
    if raw is None:
        return None
    if isinstance(raw, bytes):
        try:
            raw = raw.decode("utf-8", errors="replace")
        except Exception:
            return None
    if not raw.strip():
        return None
    try:
        data = json.loads(raw)
    except Exception:
        return None
    return data if isinstance(data, dict) else None


def resolve_session_id(args) -> str | None:
    """`--session-id` → 環境変数 → stdin JSON の順にセッション ID を決める。"""
    explicit = getattr(args, "session_id", None)
    if explicit:
        return str(explicit)
    for name in ("CLAUDE_SESSION_ID", "OKF_SESSION_ID"):
        value = os.environ.get(name)
        if value:
            return value
    payload = _read_stdin_json()
    if payload:
        value = payload.get("session_id")
        if value:
            return str(value)
    return None


def findings_fingerprint(findings: list[Finding]) -> str:
    """lint error 集合の指紋。内容が変われば別物として扱う。"""
    joined = "\n".join(sorted(str(f) for f in findings))
    return hashlib.sha256(joined.encode("utf-8")).hexdigest()[:32]


def gate_bump(session_id: str | None, fingerprint: str | None) -> int:
    """同じ error 集合に対して exit 2 を返した回数を数える。

    fingerprint が None（= error 無し）のときは状態をリセットして 0 を返す。
    """
    state_file = _gate_state_file(session_id)
    if fingerprint is None:
        try:
            state_file.unlink()
        except OSError:
            pass
        return 0

    prev: dict = {}
    same = False
    if state_file.exists():
        try:
            prev = json.loads(state_file.read_text(encoding="utf-8"))
        except Exception:
            prev = {}
        if isinstance(prev, dict) and prev.get("fingerprint") == fingerprint:
            if session_id:
                same = True
            else:
                try:
                    age = time.time() - state_file.stat().st_mtime
                except OSError:
                    age = GATE_TTL + 1
                same = age <= GATE_TTL
    count = int(prev.get("count", 0)) + 1 if same else 1
    payload = json.dumps(
        {"session_id": session_id, "fingerprint": fingerprint, "count": count, "at": now_iso()},
        ensure_ascii=False,
    )
    atomic_write_bytes(state_file, payload.encode("utf-8"))
    return count


def _has_local_changes() -> bool:
    return gitutil._has_local_changes(REPO_ROOT, runner=git)


def cmd_sync(bundle: Bundle, args) -> int:
    session_id = resolve_session_id(args) if args.gate else None

    if args.gate and not _has_local_changes():
        return 0  # docs もコードも変更が無ければ何もしない

    print("== index ==")
    index_args = argparse.Namespace(write=True, check=False, quiet=False)
    index_rc = cmd_index(bundle, index_args)

    print("\n== log ==")
    log_args = argparse.Namespace(write=True, range=None, layer=None, dry_run=False)
    try:
        cmd_log(bundle, log_args)
    except OkfError as exc:
        # log の失敗（baseline 未設定など）で sync 全体を落とさない。
        print(f"[okf log] スキップしました: {exc}", file=sys.stderr)
    if _has_local_changes():
        # log の入力はコミット履歴だけなので、未コミットの作業は反映されない。
        print(
            "[okf log] 未コミットの変更があります。今回の作業分の log.md エントリは"
            "コミット後に `okf log --write` を実行して生成してください。",
            file=sys.stderr,
        )

    print("\n== lint ==")
    bundle._docs = None  # index / log の書き込み結果を反映させる
    findings = run_lint(bundle)
    for finding in findings:
        print(finding)
    errors = [f for f in findings if f.level == "error"]
    warns = [f for f in findings if f.level == "warn"]
    print(f"lint: error {len(errors)} 件 / warn {len(warns)} 件")

    print("\n== stale ==")
    results = run_stale(bundle)
    if not results:
        print("陳腐化の兆候はありません。")
    for item in results:
        print(f"{item['path']} {item['level']} {item['kind']} {item['message']}")

    if not args.gate:
        return 1 if (errors or index_rc != 0) else 0

    count = gate_bump(session_id, findings_fingerprint(errors) if errors else None)
    if not errors:
        return 0
    if count >= 2:
        print(
            f"[okf gate] lint error が {len(errors)} 件残っていますが、"
            "同じ内容で 2 回目の差し戻しになるため警告のみとします。",
            file=sys.stderr,
        )
        return 0
    lines = [
        "[okf gate] ドキュメントの規約違反があります。次を修正してから終了してください。",
        "",
    ]
    lines += [f"  {f}" for f in errors]
    lines += [
        "",
        "修正の手順:",
        "  1. 上記ファイルの frontmatter / 本文を修正する",
        "  2. okf lint で解消を確認する",
    ]
    print("\n".join(lines), file=sys.stderr)
    return 2


# =============================================================================
# init
# =============================================================================


def _scaffold_text(rel: str) -> str:
    path = SCAFFOLD_DIR / rel
    if not path.is_file():  # pragma: no cover - 壊れたインストール向け
        raise OkfError(f"scaffold が見つかりません: {path}")
    return path.read_text(encoding="utf-8").replace("\r\n", "\n")


def _parse_layer_specs(specs: list[str] | None) -> list[tuple[str, str, str]]:
    """``--layer name=glob[:dir]`` を (name, glob, dir) に分解する。

    ``glob`` は「その層に属するコードのパス」で、log の振り分けと affected の
    起点になる。``dir`` 省略時は層名をそのままバンドル内のディレクトリ名に使う。
    """
    parsed: list[tuple[str, str, str]] = []
    seen: set[str] = set()
    for spec in specs or []:
        name, sep, rest = spec.partition("=")
        name = name.strip()
        if not sep or not name or not rest.strip():
            raise OkfError(f"--layer の書式が不正です（name=glob[:dir]）: {spec}")
        glob_part, _, dir_part = rest.partition(":")
        glob_part = glob_part.strip()
        dir_part = dir_part.strip() or name
        if not re.fullmatch(r"[a-z0-9][a-z0-9_-]*", name):
            raise OkfError(f"層名は英小文字・数字・- _ のみ使えます: {name}")
        if name in seen:
            raise OkfError(f"層名が重複しています: {name}")
        if name == "shared":
            raise OkfError("`shared` は層をまたぐ知識用に予約されています")
        if dir_part.startswith((".", "/")) or ".." in dir_part.split("/"):
            raise OkfError(f"層のディレクトリが不正です: {dir_part}")
        seen.add(name)
        parsed.append((name, glob_part, dir_part))
    return parsed


def _render_okf_yml(
    bundle_root: str, site_name: str, layers: list[tuple[str, str, str]]
) -> str:
    """``okf.yml`` を組み立てる。値はすべて ``yaml_scalar`` で安全に引用する。"""
    names = [name for name, _glob, _dir in layers]

    layer_lines = [f"  - {yaml_scalar(n)}" for n in names] + ["  - shared"]
    dir_lines = [f"  {n}: {yaml_scalar(d)}" for n, _g, d in layers]
    dir_lines.append("  shared: project")
    map_lines = [
        f"  - {{ glob: {yaml_scalar(g)}, layer: {yaml_scalar(n)} }}"
        for n, g, _d in layers
    ]
    map_lines.append(f"  - {{ glob: {yaml_scalar(bundle_root + chr(47) + chr(42) * 2)}, layer: skip }}")
    map_lines.append('  - { glob: "**", layer: shared }')
    # log.paths は log: > paths: の下なのでインデントは4スペース
    log_path_lines = [f"    {n}: {yaml_scalar(d + '/log.md')}" for n, _g, d in layers]
    log_path_lines.append("    shared: log.md")

    return _scaffold_text("okf.yml.tmpl").format(
        bundle_root=yaml_scalar(bundle_root),
        site_name=yaml_scalar(site_name),
        root_heading=yaml_scalar(f"{site_name} ドキュメント"),
        layers="\n".join(layer_lines),
        layer_dirs="\n".join(dir_lines),
        layer_map="\n".join(map_lines),
        log_layers=("[" + ", ".join(names) + "]") if names else "[]",
        log_paths="\n".join(log_path_lines),
    )


def cmd_init(args) -> int:
    """リポジトリに OKF バンドルと設定一式を生成する。"""
    layers = _parse_layer_specs(args.layer)
    raw = args.bundle_root if args.bundle_root is not None else "docs"
    bundle_root = raw.strip().replace("\\", "/")
    # 末尾スラッシュを落とす前に判定する（"/abs" が "abs" に化けるのを防ぐ）。
    if bundle_root.startswith(("/", ".")) or ":" in bundle_root:
        raise OkfError(f"bundle_root はプロジェクト内の相対パスで指定してください: {raw!r}")
    bundle_root = bundle_root.rstrip("/")
    if not bundle_root or ".." in bundle_root.split("/"):
        raise OkfError(f"bundle_root が不正です: {raw!r}")
    site_name = (args.site_name or REPO_ROOT.name).strip() or "Project"

    created: list[str] = []
    skipped: list[str] = []

    def emit(rel: str, text: str) -> None:
        path = REPO_ROOT / rel
        if path.exists() and not args.force:
            skipped.append(rel)
            return
        path.parent.mkdir(parents=True, exist_ok=True)
        write_if_changed(path, text)
        created.append(rel)

    layer_table = "\n".join(
        f"| `{bundle_root}/{d}/log.md` | `{g}` の変更 |" for _n, g, d in layers
    ) or "| （層を定義していません） | — |"
    tokens = {
        "GENERATED_AT": now_iso(),
        "BUNDLE_ROOT": bundle_root,
        "SITE_NAME": site_name,
        "LAYER_LIST": "、".join(n for n, _g, _d in layers) or "（層なし）",
        "LAYER_DIRS": " ".join(f"`{d}/`" for _n, _g, d in layers) or "—",
        "LAYER_TABLE": layer_table,
    }

    def expand(text: str) -> str:
        for key, value in tokens.items():
            text = text.replace("{{" + key + "}}", value)
        return text

    emit(CONFIG_FILENAME, _render_okf_yml(bundle_root, site_name, layers))
    emit(f"{bundle_root}/AGENTS.md", expand(_scaffold_text("AGENTS.md.tmpl")))
    emit(f"{bundle_root}/CONVENTIONS.md", expand(_scaffold_text("CONVENTIONS.md.tmpl")))

    for tmpl in sorted((SCAFFOLD_DIR / "templates").glob("*.md")):
        emit(f"{bundle_root}/_templates/{tmpl.name}", _scaffold_text(f"templates/{tmpl.name}"))
    for hook in sorted((SCAFFOLD_DIR / "hooks").iterdir()):
        emit(f".okf/hooks/{hook.name}", _scaffold_text(f"hooks/{hook.name}"))

    def empty_log(layer_name: str) -> str:
        return (
            f"# 変更履歴 — {layer_name}\n"
            "\n"
            "<!-- `okf log --write` が git 履歴からここに追記する。"
            "書式は /CONVENTIONS.md §7 を参照。 -->\n"
        )

    for name, _glob, directory in layers:
        emit(f"{bundle_root}/{directory}/log.md", empty_log(name))
    emit(f"{bundle_root}/log.md", empty_log("shared"))

    for rel in created:
        print(f"作成: {rel}")
    if skipped:
        print(f"既存のためスキップ（--force で上書き）: {len(skipped)} 件")
        for rel in skipped:
            print(f"  {rel}")
    print()
    print("次の手順:")
    print(f"  1. {bundle_root}/CONVENTIONS.md の語彙を確認・調整する")
    print(f"  2. {CONFIG_FILENAME} の layer_map が実際のコード配置と合っているか確認する")
    print("  3. okf index --write で目次を生成する")
    print("  4. okf lint で規約違反が無いか確認する")
    print("  5. .gitignore に _site/ を追加する（HTML生成物）")
    return 0


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
