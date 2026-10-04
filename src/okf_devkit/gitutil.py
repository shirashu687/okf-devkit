"""Git and repository resources with explicit project roots and caller-owned caches."""
from __future__ import annotations

import datetime as _dt
import glob as _glob
import re
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from functools import partial
from pathlib import Path
from typing import Callable

from .errors import OkfError
from .fsutil import parse_datetime, path_matches

GitRunner = Callable[..., tuple[int, str]]


@dataclass
class CommitTimesCache:
    root: Path | None = None
    mapping: dict[str, str] | None = None


def git(root: Path, *args: str, cwd: Path | None = None) -> tuple[int, str]:
    """git を実行して (returncode, stdout) を返す。失敗しても例外にしない。"""
    try:
        proc = subprocess.run(
            ["git", *args],
            cwd=str(cwd or root),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
    except FileNotFoundError:
        return 127, ""
    return proc.returncode, proc.stdout or ""


def git_available(root: Path, *, runner: GitRunner | None = None) -> bool:
    run = runner if runner is not None else partial(git, root)
    code, _ = run("rev-parse", "--git-dir")
    return code == 0


def has_commits(root: Path, *, runner: GitRunner | None = None) -> bool:
    """1 つ以上のコミットがあるか（初回コミット前は False）。"""
    run = runner if runner is not None else partial(git, root)
    code, _ = run("rev-parse", "--verify", "--quiet", "HEAD")
    return code == 0


def is_shallow(root: Path, *, runner: GitRunner | None = None) -> bool:
    run = runner if runner is not None else partial(git, root)
    code, out = run("rev-parse", "--is-shallow-repository")
    return code == 0 and out.strip() == "true"


def repo_web_url(root: Path, *, runner: GitRunner | None = None) -> str | None:
    """origin の URL から GitHub の https URL を導出する。"""
    run = runner if runner is not None else partial(git, root)
    code, out = run("remote", "get-url", "origin")
    if code != 0 or not out.strip():
        return None
    url = out.strip()
    m = re.match(r"^git@([^:]+):(.+?)(?:\.git)?$", url)
    if m:
        return f"https://{m.group(1)}/{m.group(2)}"
    m = re.match(r"^(https?://[^\s]+?)(?:\.git)?$", url)
    if m:
        return m.group(1)
    return None


def resolve_ref(root: Path, ref: str, *, runner: GitRunner | None = None) -> str | None:
    """ref を解決できれば ref 名を返す（`<ref>` → `origin/<ref>` の順）。"""
    run = runner if runner is not None else partial(git, root)
    for candidate in (ref, f"origin/{ref}"):
        code, _ = run("rev-parse", "--verify", "--quiet", f"{candidate}^{{commit}}")
        if code == 0:
            return candidate
    return None


def resolve_commit(root: Path, ref: str, *, runner: GitRunner | None = None) -> str | None:
    """ref を full SHA に解決する。"""
    run = runner if runner is not None else partial(git, root)
    code, out = run("rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}")
    if code != 0:
        return None
    return out.strip() or None


def _parse_log_z(out: str, field_count: int) -> list[tuple[list[str], list[tuple[str, str]]]]:
    """`-z` + `--name-status` の出力を [(ヘッダ項目, [(status, path), ...])] にする。"""
    tokens = out.split("\0")
    records: list[tuple[list[str], list[tuple[str, str]]]] = []
    current: tuple[list[str], list[tuple[str, str]]] | None = None
    i = 0
    while i < len(tokens):
        tok = tokens[i]
        if tok == "":
            i += 1
            continue
        if tok.startswith("@@@"):
            head, nl, rest = tok.partition("\n")
            fields = head[3:].split("\t", field_count - 1)
            while len(fields) < field_count:
                fields.append("")
            current = (fields, [])
            records.append(current)
            if nl and rest:
                tokens[i] = rest  # 先頭のステータス/パスとして読み直す
                continue
            i += 1
            continue
        if current is None:
            i += 1
            continue
        i = _consume_change(tokens, i, current[1])
    return records


def _consume_change(tokens: list[str], i: int, out: list[tuple[str, str]]) -> int:
    status = tokens[i]
    if status[:1] in ("R", "C"):
        old = tokens[i + 1] if i + 1 < len(tokens) else ""
        new = tokens[i + 2] if i + 2 < len(tokens) else ""
        for p in (old, new):
            if p:
                out.append((status, p.replace("\\", "/")))
        return i + 3
    path = tokens[i + 1] if i + 1 < len(tokens) else ""
    if path:
        out.append((status, path.replace("\\", "/")))
    return i + 2


def parse_porcelain_z(out: str) -> list[str]:
    """`git status --porcelain -z` を解析する（rename は新旧の両方を返す）。"""
    tokens = out.split("\0")
    paths: list[str] = []
    i = 0
    while i < len(tokens):
        rec = tokens[i]
        if not rec:
            i += 1
            continue
        xy = rec[:2]
        path = rec[3:] if len(rec) > 3 else ""
        if path:
            paths.append(path.replace("\\", "/"))
        if "R" in xy or "C" in xy:
            if i + 1 < len(tokens) and tokens[i + 1]:
                paths.append(tokens[i + 1].replace("\\", "/"))
            i += 2
        else:
            i += 1
    return paths


def path_commit_times(root: Path, cache: CommitTimesCache, *, runner: GitRunner | None = None) -> dict[str, str]:
    """全履歴を 1 回だけ走査して path → 最終コミット日時（ISO 8601）を作る。

    `git log -1 -- <paths>` をパス集合ごとに呼ぶ方式だと、パス数が増えるほど
    git プロセスが増え、引数上限で切り捨てる必要も出てくる。ここでは
    1 回の `git log --name-only -z` から全件の対応表を作る。
    """
    run = runner if runner is not None else partial(git, root)
    current_root = root.resolve()
    if cache.mapping is not None and cache.root == current_root:
        return cache.mapping
    mapping: dict[str, str] = {}
    if has_commits(root, runner=run):
        code, out = run("log", "-z", "--pretty=format:@@@%cI", "--name-status")
        if code == 0:
            for fields, changes in _parse_log_z(out, 1):
                when = fields[0].strip()
                if not when:
                    continue
                for _status, path in changes:
                    mapping.setdefault(path, when)  # 新しい順なので最初の 1 件が最新
    cache.mapping = mapping
    cache.root = current_root
    return mapping


def last_commit_time(root: Path, paths: list[str], cache: CommitTimesCache, *, runner: GitRunner | None = None) -> str | None:
    """指定パス群の最終コミット日時（ISO 8601 文字列）。"""
    run = runner if runner is not None else partial(git, root)
    mapping = path_commit_times(root, cache, runner=run)
    return latest_commit_time(paths, mapping)


def latest_commit_time(paths: list[str], mapping: dict[str, str]) -> str | None:
    best: str | None = None
    best_dt: _dt.datetime | None = None
    for path in paths:
        raw = mapping.get(path)
        if not raw:
            continue
        parsed, _ = parse_datetime(raw)
        if parsed is None:
            continue
        if best_dt is None or parsed > best_dt:
            best_dt, best = parsed, raw
    return best


def resolve_resource(root: Path, resource: str) -> list[str]:
    """sources[].resource（パス or glob）を実ファイルのリストに解決する。

    列挙は標準の :mod:`glob` で行い、最終的な採否は ``path_matches()``
    （= `glob_to_regex`）で決める。これにより lint / stale / affected の
    glob 解釈が 1 実装に揃う。
    """
    pattern = resource.replace("\\", "/").lstrip("/")
    if not pattern:
        return []
    if not any(ch in pattern for ch in "*?["):
        p = root / pattern
        return [pattern] if p.is_file() else []
    matched = _glob.glob(pattern, root_dir=str(root), recursive=True)
    out = []
    for rel in matched:
        rel = rel.replace("\\", "/")
        if (root / rel).is_file() and path_matches(rel, pattern):
            out.append(rel)
    return sorted(out)


class Commit:
    def __init__(self, sha: str, short: str, date: str, subject: str, paths: list[str]):
        self.sha = sha          # full SHA（既出判定に使う）
        self.short = short      # 短縮ハッシュ（log.md への出力に使う）
        self.date = date
        self.subject = subject
        self.paths = paths


def collect_commits(root: Path, rev_range: str | None, exclude: str | None = None, *, runner: GitRunner | None = None) -> list[Commit]:
    """git 履歴からコミットを収集する。

    既定では `--first-parent`。これは「マージコミットを 1 件に畳む」という意味で
    あって「PR 単位」を保証するものではない（main への直接コミットもそのまま
    1 件として現れる）。
    """
    run = runner if runner is not None else partial(git, root)
    if not git_available(root, runner=run):
        raise OkfError("git リポジトリが見つかりません。リポジトリ内で実行してください。")
    if not has_commits(root, runner=run):
        return []
    args = [
        "log",
        "--first-parent",
        "-z",
        "--pretty=format:@@@%H\t%h\t%cs\t%s",
        "--name-status",
    ]
    # 除外だけを渡すと git は「positive ref なし」とみなして何も返さないため、
    # 範囲未指定のときは明示的に HEAD を positive ref にする。
    args.append(rev_range if rev_range else "HEAD")
    if exclude:
        args.append(f"^{exclude}")
    code, out = run(*args)
    if code != 0:
        raise OkfError(
            "git log の実行に失敗しました"
            + (f"（範囲: {rev_range}）" if rev_range else "")
            + "。リビジョン指定と git リポジトリの状態を確認してください。"
        )
    commits: list[Commit] = []
    for fields, changes in _parse_log_z(out, 4):
        sha, short, date, subject = fields[0], fields[1], fields[2], fields[3]
        if not sha:
            continue
        paths = [p for _status, p in changes]
        commits.append(Commit(sha, short, date, subject, paths))
    return commits


def changed_paths(root: Path, base: str, *, runner: GitRunner | None = None) -> list[str]:
    """base からの変更パス。未コミットの作業ツリー変更も含める。

    base は `<base>` → `origin/<base>` の順に解決し、HEAD との merge-base で
    比較する（detached HEAD やローカル ref が無い環境でも動くようにする）。
    """
    run = runner if runner is not None else partial(git, root)
    if not git_available(root, runner=run):
        raise OkfError("git リポジトリが見つかりません。リポジトリ内で実行してください。")

    paths: set[str] = set()
    if has_commits(root, runner=run):
        ref = resolve_ref(root, base, runner=run)
        if ref is None:
            raise OkfError(
                f"base ref を解決できませんでした: {base}"
                f"（`{base}` も `origin/{base}` も存在しません。--base か --paths を指定してください）"
            )
        code, out = run("merge-base", ref, "HEAD")
        merge_base = out.strip() if code == 0 else ""
        if merge_base:
            code, out = run("diff", "--name-only", "-z", merge_base, "HEAD")
        else:
            # 履歴が交わらない（shallow / 別ルート）ときは直接比較にフォールバック
            code, out = run("diff", "--name-only", "-z", ref)
        if code != 0:
            raise OkfError(f"git diff に失敗しました（base: {base}）")
        paths.update(p.replace("\\", "/") for p in out.split("\0") if p.strip())
    else:
        print("[okf affected] コミットがまだないため、作業ツリーの変更のみを対象にします。",
              file=sys.stderr)

    code, out = run("status", "--porcelain", "-z", "--untracked-files=all")
    if code == 0:
        paths.update(parse_porcelain_z(out))
    return sorted(paths)


def gate_state_dir(root: Path, *, runner: GitRunner | None = None) -> Path:
    """gate 状態の保存先（git 管理外）。

    作業ツリーに置くと `.gitignore` 漏れで常に dirty になり、
    「変更が無ければ即終了」が機能しなくなるため git ディレクトリ配下に置く。
    """
    run = runner if runner is not None else partial(git, root)
    code, out = run("rev-parse", "--git-path", "okf-gate")
    if code == 0 and out.strip():
        path = Path(out.strip())
        if not path.is_absolute():
            path = root / path
        return path
    return Path(tempfile.gettempdir()) / "okf-gate"


def _has_local_changes(root: Path, *, runner: GitRunner | None = None) -> bool:
    run = runner if runner is not None else partial(git, root)
    code, out = run("status", "--porcelain")
    if code != 0:
        return True  # git が使えないときは判断できないので処理を続ける
    return bool(out.strip())
