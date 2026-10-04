"""Commit-based change logs with explicit project-root Git operations."""
from __future__ import annotations
import re
import sys
from pathlib import Path
from .. import gitutil
from ..gitutil import Commit
from ..config import Bundle
from ..errors import OkfError
from ..fsutil import path_matches, read_text, rel_posix, write_if_changed

def layer_of(bundle: Bundle, path: str) -> str | None:
    """変更パスから層を判定する。skip / 未マッチは None。"""
    for rule in bundle.cfg.get("layer_map") or []:
        if not isinstance(rule, dict):
            continue
        if path_matches(path, str(rule.get("glob", ""))):
            layer = str(rule.get("layer", ""))
            return None if layer == "skip" else layer
    return None


def kind_of(bundle: Bundle, subject: str) -> str:
    """コミット subject から log.md のプレフィックスを推定する。"""
    for rule in bundle.cfg.get("kind_rules") or []:
        if not isinstance(rule, dict):
            continue
        if re.search(str(rule.get("pattern", "")), subject, re.IGNORECASE):
            return str(rule.get("kind", "**Update**"))
    return "**Update**"


def format_log_line(bundle: Bundle, commit: Commit, web_url: str | None) -> str:
    """OKF v0.2 §9 準拠の 1 エントリを組み立てる。"""
    subject = commit.subject.strip()
    pr = None
    m = re.search(r"\s*\(#(\d+)\)\s*$", subject)
    if m:
        pr = m.group(1)
        subject = subject[: m.start()].strip()
    if subject and subject[-1] not in "。．.!?！？":
        subject += "。"
    refs = []
    if pr and web_url:
        refs.append(f"[#{pr}]({web_url}/pull/{pr})")
    elif pr:
        refs.append(f"#{pr}")
    refs.append(f"`{commit.short or commit.sha[:7]}`")
    return f"- {kind_of(bundle, subject)} {subject} ({', '.join(refs)})"


ENTRY_RE = re.compile(r"^\s*-\s+\S")
HASH_RE = re.compile(r"`([0-9a-f]{7,40})`")


def recorded_hashes(text: str) -> set[str]:
    return set(HASH_RE.findall(text))


def hashless_entries(text: str) -> list[str]:
    """コミットハッシュを持たない既存エントリ行を返す（移行済みの手書き分）。"""
    out = []
    for line in text.split("\n"):
        if ENTRY_RE.match(line) and not HASH_RE.search(line):
            out.append(line.strip())
    return out


def insert_log_entries(text: str, entries_by_date: dict[str, list[str]]) -> str:
    """日付見出し（新しい順）を保ちながらエントリを差し込む。"""
    lines = text.split("\n")
    heading_re = re.compile(r"^##\s+(\d{4}-\d{2}-\d{2})\s*$")
    for date in sorted(entries_by_date, reverse=True):
        block = entries_by_date[date]
        pos = None
        for i, line in enumerate(lines):
            m = heading_re.match(line)
            if m and m.group(1) == date:
                pos = i + 1
                break
        if pos is not None:
            lines[pos:pos] = block  # 同一日付の先頭に追記
            continue
        insert_at = None
        for i, line in enumerate(lines):
            m = heading_re.match(line)
            if m and m.group(1) < date:
                insert_at = i
                break
        new_block = [f"## {date}", *block, ""]
        if insert_at is None:
            while lines and lines[-1].strip() == "":
                lines.pop()
            lines.extend(["", *new_block[:-1]])
        else:
            lines[insert_at:insert_at] = new_block
    out = "\n".join(lines).rstrip("\n") + "\n"
    return out


def log_baseline_sha(bundle: Bundle, *, repo_root: Path | None = None, runner=None) -> str | None:
    """`log.baseline` を full SHA に解決する。未設定なら None。"""
    raw = bundle.log_cfg.get("baseline")
    if raw is None:
        return None
    ref = str(raw).strip()
    if not ref:
        return None
    sha = gitutil.resolve_commit((bundle.repo_root if repo_root is None else repo_root), ref, runner=runner)
    if sha is None:
        raise OkfError(
            f"config.yml の log.baseline を解決できません: {ref}"
            "（既存のコミットを指定するか、値を空にしてください）"
        )
    return sha


def cmd_log(bundle: Bundle, args, *, repo_root: Path | None = None, runner=None, writer=None) -> int:
    if not gitutil.git_available((bundle.repo_root if repo_root is None else repo_root), runner=runner):
        raise OkfError("git リポジトリが見つかりません。リポジトリ内で実行してください。")
    if not gitutil.has_commits((bundle.repo_root if repo_root is None else repo_root), runner=runner):
        print("コミットがまだありません（log.md には何も追記しません）。")
        return 0
    if gitutil.is_shallow((bundle.repo_root if repo_root is None else repo_root), runner=runner):
        print(
            "[okf log] 警告: shallow clone です。取得済みの範囲しか走査できないため、"
            "古いコミットが log.md に反映されない可能性があります"
            "（`git fetch --unshallow` を検討してください）。",
            file=sys.stderr,
        )

    baseline = log_baseline_sha(bundle, repo_root=repo_root, runner=runner)
    web_url = gitutil.repo_web_url((bundle.repo_root if repo_root is None else repo_root), runner=runner)
    commits = gitutil.collect_commits((bundle.repo_root if repo_root is None else repo_root), args.range, exclude=baseline, runner=runner)
    target_layers = [args.layer] if args.layer else bundle.log_layers()
    if args.layer and args.layer not in bundle.layers:
        raise OkfError(f"`--layer {args.layer}` は語彙表にありません（{', '.join(bundle.layers)}）")

    # baseline 未設定でハッシュ無しの既存エントリがあると、移行済みの内容を
    # 二重に追記してしまう。--write は拒否し、まず --dry-run を促す。
    if args.write and baseline is None:
        blockers: list[str] = []
        for layer in target_layers:
            log_path = bundle.log_path(layer)
            if not log_path.exists():
                continue
            leftovers = hashless_entries(read_text(log_path))
            if leftovers:
                blockers.append(f"{rel_posix(log_path, (bundle.repo_root if repo_root is None else repo_root))}（{len(leftovers)} 件）")
        if blockers:
            raise OkfError(
                "config.yml の log.baseline が未設定で、コミットハッシュを持たない既存エントリがあります: "
                + " / ".join(blockers)
                + "。同じ変更を二重に追記する恐れがあるため書き込みを中止しました。"
                " `okf log --dry-run` で内容を確認し、"
                " config.yml の log.baseline に移行済みのコミットを設定してください。"
            )

    results: list[str] = []
    changed = 0
    for layer in target_layers:
        log_path = bundle.log_path(layer)
        existing = read_text(log_path) if log_path.exists() else ""
        recorded = recorded_hashes(existing)

        entries_by_date: dict[str, list[str]] = {}
        added = 0
        for commit in commits:
            # 記録済み判定は full SHA を正として prefix 照合する
            # （短縮ハッシュ同士の prefix 比較だと別コミットを既出扱いしうる）
            if any(commit.sha.startswith(h) for h in recorded):
                continue
            layers = {layer_of(bundle, p) for p in commit.paths}
            layers.discard(None)
            if layer not in layers:
                continue
            entries_by_date.setdefault(commit.date, []).append(
                format_log_line(bundle, commit, web_url)
            )
            added += 1

        if not added:
            continue

        if not existing:
            heading = str(bundle.log_cfg.get("heading_prefix", "変更履歴 — "))
            existing = f"# {heading}{layer}\n"
        content = insert_log_entries(existing, entries_by_date)

        rel = rel_posix(log_path, (bundle.repo_root if repo_root is None else repo_root))
        results.append(f"{rel}: {added} 件")
        if args.dry_run:
            print(f"--- {rel} (dry-run) ---")
            for date in sorted(entries_by_date, reverse=True):
                print(f"## {date}")
                for line in entries_by_date[date]:
                    print(line)
            print()
        elif args.write:
            if (write_if_changed if writer is None else writer)(log_path, content):
                changed += 1

    if not results:
        print("log.md に追記すべき変更はありません。")
        return 0
    if args.write:
        print(f"log.md を更新しました（{changed} ファイル）:")
    elif not args.dry_run:
        print("追記対象（--write で書き込み / --dry-run で内容確認）:")
    for line in results:
        print(f"  {line}")
    return 0
