"""Sync orchestration and gate session state with explicit root and callback seams."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
import re
import sys
import threading
import time
from pathlib import Path
from ..config import Bundle
from ..errors import OkfError
from .. import gitutil
from ..fsutil import atomic_write_bytes, now_iso
from .index import cmd_index
from .log import cmd_log
from .lint import Finding, run_lint
from .stale import run_stale

STDIN_LIMIT = 1 << 20  # hook 入力の読み取り上限（1 MiB）
STDIN_TIMEOUT = 2.0    # 秒。EOF が来なくてもここで諦める（ハング防止）
GATE_TTL = 600         # session_id が無いときに同一セッションとみなす秒数


def gate_state_dir(repo_root: Path, *, runner=None) -> Path:
    return gitutil.gate_state_dir(repo_root, runner=runner)


def _gate_state_file(repo_root: Path, session_id: str | None, *, runner=None, state_dir=None) -> Path:
    key = re.sub(r"[^A-Za-z0-9_.-]", "_", session_id or "")[:80] or "_nosession"
    return (gate_state_dir(repo_root, runner=runner) if state_dir is None else state_dir()) / f"{key}.json"


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


def resolve_session_id(args, *, payload_reader=None) -> str | None:
    """`--session-id` → 環境変数 → stdin JSON の順にセッション ID を決める。"""
    explicit = getattr(args, "session_id", None)
    if explicit:
        return str(explicit)
    for name in ("CLAUDE_SESSION_ID", "OKF_SESSION_ID"):
        value = os.environ.get(name)
        if value:
            return value
    payload = (_read_stdin_json if payload_reader is None else payload_reader)()
    if payload:
        value = payload.get("session_id")
        if value:
            return str(value)
    return None


def findings_fingerprint(findings: list[Finding]) -> str:
    """lint error 集合の指紋。内容が変われば別物として扱う。"""
    joined = "\n".join(sorted(str(f) for f in findings))
    return hashlib.sha256(joined.encode("utf-8")).hexdigest()[:32]


def gate_bump(repo_root: Path, session_id: str | None, fingerprint: str | None, *, runner=None, state_file_provider=None, ttl: float | None = None) -> int:
    """同じ error 集合に対して exit 2 を返した回数を数える。

    fingerprint が None（= error 無し）のときは状態をリセットして 0 を返す。
    """
    ttl = GATE_TTL if ttl is None else ttl
    state_file = (_gate_state_file(repo_root, session_id, runner=runner) if state_file_provider is None else state_file_provider(session_id))
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
                    age = ttl + 1
                same = age <= ttl
    count = int(prev.get("count", 0)) + 1 if same else 1
    payload = json.dumps(
        {"session_id": session_id, "fingerprint": fingerprint, "count": count, "at": now_iso()},
        ensure_ascii=False,
    )
    atomic_write_bytes(state_file, payload.encode("utf-8"))
    return count


def _has_local_changes(repo_root: Path, *, runner=None) -> bool:
    return gitutil._has_local_changes(repo_root, runner=runner)


def cmd_sync(bundle: Bundle, args, *, runner=None, indexer=None, logger=None, linter=None, stale_reporter=None, dirty_checker=None, session_resolver=None, gate_counter=None) -> int:
    session_id = (resolve_session_id if session_resolver is None else session_resolver)(args) if args.gate else None

    if args.gate and not ( _has_local_changes(bundle.repo_root, runner=runner) if dirty_checker is None else dirty_checker()):
        return 0  # docs もコードも変更が無ければ何もしない

    print("== index ==")
    index_args = argparse.Namespace(write=True, check=False, quiet=False)
    index_rc = (cmd_index if indexer is None else indexer)(bundle, index_args)

    print("\n== log ==")
    log_args = argparse.Namespace(write=True, range=None, layer=None, dry_run=False)
    try:
        (cmd_log if logger is None else logger)(bundle, log_args)
    except OkfError as exc:
        # log の失敗（baseline 未設定など）で sync 全体を落とさない。
        print(f"[okf log] スキップしました: {exc}", file=sys.stderr)
    if ( _has_local_changes(bundle.repo_root, runner=runner) if dirty_checker is None else dirty_checker()):
        # log の入力はコミット履歴だけなので、未コミットの作業は反映されない。
        print(
            "[okf log] 未コミットの変更があります。今回の作業分の log.md エントリは"
            "コミット後に `okf log --write` を実行して生成してください。",
            file=sys.stderr,
        )

    print("\n== lint ==")
    bundle._docs = None  # index / log の書き込み結果を反映させる
    findings = (run_lint if linter is None else linter)(bundle)
    for finding in findings:
        print(finding)
    errors = [f for f in findings if f.level == "error"]
    warns = [f for f in findings if f.level == "warn"]
    print(f"lint: error {len(errors)} 件 / warn {len(warns)} 件")

    print("\n== stale ==")
    results = (run_stale if stale_reporter is None else stale_reporter)(bundle)
    if not results:
        print("陳腐化の兆候はありません。")
    for item in results:
        print(f"{item['path']} {item['level']} {item['kind']} {item['message']}")

    if not args.gate:
        return 1 if (errors or index_rc != 0) else 0

    fingerprint = findings_fingerprint(errors) if errors else None
    count = (gate_bump(bundle.repo_root, session_id, fingerprint, runner=runner) if gate_counter is None else gate_counter(session_id, fingerprint))
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
