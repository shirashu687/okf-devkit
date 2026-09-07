#!/usr/bin/env python3
"""Check protected and upstream-managed changes for a fixed comparison point.

This is intentionally a repository-local check rather than a public CLI feature.
It reports paths and declaration state, but never prints changed file contents or
modifies the repository.
"""

from __future__ import annotations

import argparse
import fnmatch
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


EXIT_OK = 0
EXIT_INVALID = 1
EXIT_UNAVAILABLE = 2

FULL_SHA = re.compile(r"^[0-9a-fA-F]{40}$")
ZERO_SHA = re.compile(r"^0+$")
DECLARATION_DIRECTORY = "harness/state/journal"
DECLARATION_SCOPES = ("task", "pull-request")

PROTECTED_PATTERNS = (
    "AGENTS.md",
    "CLAUDE.md",
    "harness/core/policy/**",
    "harness/core/procedures/verify-report.md",
    "harness/project/config.md",
    "harness/project/check_changes.py",
    ".github/workflows/**",
    "tests/**",
    "pyproject.toml",
    "okf.yml",
    ".claude/settings*.json",
    ".codex/**",
)

UPSTREAM_PATTERNS = (
    ".agents/skills/**",
    ".claude/skills/**",
    "skills-lock.json",
    "THIRD_PARTY_NOTICES.md",
    "harness/project/skill-profile.md",
)


class ComparisonUnavailable(Exception):
    """Raised when the requested comparison cannot be established safely."""


@dataclass(frozen=True)
class ChangedPath:
    path: str
    status: str
    rename_peer: str | None = None


def run_git(repo: Path, args: list[str]) -> subprocess.CompletedProcess[bytes]:
    """Run git without a shell and return bytes so NUL paths stay intact."""

    try:
        return subprocess.run(
            ["git", *args],
            cwd=repo,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
    except OSError as exc:
        raise ComparisonUnavailable("Git executable is unavailable") from exc


def git_error(args: Iterable[str], proc: subprocess.CompletedProcess[bytes]) -> str:
    detail = proc.stderr.decode("utf-8", errors="replace").strip()
    command = "git " + " ".join(args)
    if detail:
        return f"{command} failed: {detail}"
    return f"{command} failed"


def find_repo_root() -> Path:
    try:
        proc = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
    except OSError as exc:
        raise ComparisonUnavailable("Git executable is unavailable") from exc
    if proc.returncode != 0:
        raise ComparisonUnavailable("current directory is not a Git repository")
    raw_root = proc.stdout.decode("utf-8", errors="surrogateescape").strip()
    if not raw_root:
        raise ComparisonUnavailable("Git did not return a repository root")
    return Path(raw_root).resolve()


def ensure_repository_is_comparable(repo: Path) -> None:
    shallow = run_git(repo, ["rev-parse", "--is-shallow-repository"])
    if shallow.returncode != 0:
        raise ComparisonUnavailable(git_error(["rev-parse", "--is-shallow-repository"], shallow))
    if shallow.stdout.strip().lower() == b"true":
        raise ComparisonUnavailable("repository history is shallow; fetch the full history first")


def resolve_commit(repo: Path, value: str, label: str) -> str:
    if not value or ZERO_SHA.fullmatch(value):
        raise ComparisonUnavailable(f"{label} is empty or all-zero")
    args = ["rev-parse", "--verify", f"{value}^{{commit}}"]
    proc = run_git(repo, args)
    if proc.returncode != 0:
        raise ComparisonUnavailable(f"{label} cannot be resolved")
    resolved = proc.stdout.decode("ascii", errors="replace").strip()
    if not FULL_SHA.fullmatch(resolved):
        raise ComparisonUnavailable(f"{label} did not resolve to a complete commit SHA")
    return resolved.lower()


def decode_git_field(value: bytes) -> str:
    return value.decode("utf-8", errors="surrogateescape").replace("\\", "/")


def parse_name_status(raw: bytes) -> list[ChangedPath]:
    fields = raw.split(b"\0")
    if fields and fields[-1] == b"":
        fields.pop()

    result: list[ChangedPath] = []
    index = 0
    while index < len(fields):
        status = decode_git_field(fields[index])
        index += 1
        if not status:
            raise ComparisonUnavailable("Git returned an empty change status")
        if status[0] in {"R", "C"}:
            if index + 1 >= len(fields):
                raise ComparisonUnavailable("Git returned an incomplete rename/copy record")
            old_path = decode_git_field(fields[index])
            new_path = decode_git_field(fields[index + 1])
            index += 2
            result.append(ChangedPath(old_path, f"{status}:old", new_path))
            result.append(ChangedPath(new_path, f"{status}:new", old_path))
        else:
            if index >= len(fields):
                raise ComparisonUnavailable("Git returned an incomplete change record")
            path = decode_git_field(fields[index])
            index += 1
            result.append(ChangedPath(path, status))
    return result


def changed_paths(repo: Path, base: str, head: str | None) -> list[ChangedPath]:
    if head is None:
        conflict = run_git(repo, ["ls-files", "--unmerged", "-z"])
        if conflict.returncode != 0:
            raise ComparisonUnavailable(git_error(["ls-files", "--unmerged", "-z"], conflict))
        if conflict.stdout:
            raise ComparisonUnavailable("working tree contains unmerged paths")

    diff_args = ["diff", "--name-status", "--find-renames=50%", "-z", base]
    if head is not None:
        diff_args.append(head)
    diff_args.append("--")
    diff = run_git(repo, diff_args)
    if diff.returncode != 0:
        raise ComparisonUnavailable(git_error(diff_args, diff))

    paths = parse_name_status(diff.stdout)
    if head is None:
        untracked_args = ["ls-files", "--others", "--exclude-standard", "-z", "--"]
        untracked = run_git(repo, untracked_args)
        if untracked.returncode != 0:
            raise ComparisonUnavailable(git_error(untracked_args, untracked))
        for raw_path in untracked.stdout.split(b"\0"):
            if raw_path:
                paths.append(ChangedPath(decode_git_field(raw_path), "A:untracked"))

    unique: dict[str, ChangedPath] = {}
    for item in paths:
        existing = unique.get(item.path)
        if existing is None:
            unique[item.path] = item
        else:
            unique[item.path] = ChangedPath(
                item.path,
                f"{existing.status},{item.status}",
                existing.rename_peer or item.rename_peer,
            )
    return list(unique.values())


def matches(path: str, pattern: str) -> bool:
    if pattern.endswith("/**"):
        prefix = pattern[:-3]
        return path == prefix or path.startswith(prefix + "/")
    return fnmatch.fnmatchcase(path, pattern)


def classify(path: str) -> str:
    if any(matches(path, pattern) for pattern in PROTECTED_PATTERNS):
        return "protected"
    if any(matches(path, pattern) for pattern in UPSTREAM_PATTERNS):
        return "upstream"
    return "ordinary"


def change_category(path: str, changed_by_path: dict[str, ChangedPath]) -> str:
    category = classify(path)
    item = changed_by_path.get(path)
    if category == "ordinary" and item is not None and item.rename_peer:
        peer_category = classify(item.rename_peer)
        if peer_category != "ordinary":
            return peer_category
    return category


def is_declaration_path(path: str) -> bool:
    prefix = DECLARATION_DIRECTORY + "/"
    if not path.startswith(prefix) or not path.endswith(".changes.json"):
        return False
    return "/" not in path[len(prefix) : -len(".changes.json")]


def valid_relative_path(value: object) -> bool:
    if not isinstance(value, str) or not value:
        return False
    if value.startswith(("/", "\\")) or "\\" in value or re.match(r"^[A-Za-z]:", value):
        return False
    if any(part in {"", ".", ".."} for part in value.split("/")):
        return False
    if any(char in value for char in "*?[]"):
        return False
    return "\0" not in value


def worktree_file(repo: Path, relative_path: str) -> Path:
    if not valid_relative_path(relative_path):
        raise ValueError("path must be a repository-relative path")
    candidate = (repo / Path(*relative_path.split("/"))).resolve()
    try:
        candidate.relative_to(repo)
    except ValueError as exc:
        raise ValueError("path escapes the repository") from exc
    return candidate


def declaration_bytes(repo: Path, path: str, head: str | None) -> bytes:
    if head is None:
        candidate = worktree_file(repo, path)
        try:
            return candidate.read_bytes()
        except OSError as exc:
            raise ValueError("declaration file is not readable in the working tree") from exc

    args = ["show", f"{head}:{path}"]
    proc = run_git(repo, args)
    if proc.returncode != 0:
        raise ValueError("declaration file is not present in the head commit")
    return proc.stdout


def worklog_exists(repo: Path, path: str, head: str | None) -> bool:
    if not valid_relative_path(path) or not path.endswith(".md"):
        return False
    if head is None:
        try:
            return worktree_file(repo, path).is_file()
        except ValueError:
            return False
    proc = run_git(repo, ["cat-file", "-t", f"{head}:{path}"])
    return proc.returncode == 0 and proc.stdout.strip() == b"blob"


def load_declarations(
    repo: Path,
    paths: list[ChangedPath],
    changed_by_path: dict[str, ChangedPath],
    base: str,
    head: str | None,
    scope: str = "task",
) -> tuple[dict[str, str], list[str]]:
    declarations = sorted({item.path for item in paths if is_declaration_path(item.path)})
    declared: dict[str, str] = {}
    diagnostics: list[str] = []

    for declaration_path in declarations:
        try:
            raw = declaration_bytes(repo, declaration_path, head)
            document = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError, OSError, ValueError) as exc:
            diagnostics.append(f"invalid declaration {declaration_path}: {exc}")
            continue

        if not isinstance(document, dict):
            diagnostics.append(f"invalid declaration {declaration_path}: top level must be an object")
            continue
        if type(document.get("version")) is not int or document["version"] != 1:
            diagnostics.append(f"invalid declaration {declaration_path}: version must be 1")
        declaration_scope = document.get("scope", "task")
        if declaration_scope not in DECLARATION_SCOPES:
            diagnostics.append(f"invalid declaration {declaration_path}: scope must be task or pull-request")
            continue
        selected = declaration_scope == scope
        declared_base = document.get("base")
        if (
            not isinstance(declared_base, str)
            or not FULL_SHA.fullmatch(declared_base)
            or ZERO_SHA.fullmatch(declared_base)
        ):
            diagnostics.append(f"invalid declaration {declaration_path}: base must be a complete nonzero SHA")
        elif selected and declared_base.lower() != base:
            diagnostics.append(f"invalid declaration {declaration_path}: base does not match comparison base")
        worklog = document.get("worklog")
        if not valid_relative_path(worklog) or not worklog.endswith(".md"):
            diagnostics.append(f"invalid declaration {declaration_path}: worklog must be a repository Markdown path")
        elif not worklog_exists(repo, worklog, head):
            diagnostics.append(f"invalid declaration {declaration_path}: worklog does not exist")

        entries = document.get("changes")
        if not isinstance(entries, list) or not entries:
            diagnostics.append(f"invalid declaration {declaration_path}: changes must be a non-empty list")
            continue
        entry_paths: set[str] = set()
        for entry in entries:
            if not isinstance(entry, dict):
                diagnostics.append(f"invalid declaration {declaration_path}: each change must be an object")
                continue
            path = entry.get("path")
            reason = entry.get("reason")
            if not valid_relative_path(path):
                diagnostics.append(f"invalid declaration {declaration_path}: path is not repository-relative")
                continue
            if not isinstance(reason, str) or not reason.strip():
                diagnostics.append(f"invalid declaration {declaration_path}: reason is empty for {path}")
            if path in entry_paths:
                diagnostics.append(f"invalid declaration {declaration_path}: duplicate path: {path}")
                continue
            entry_paths.add(path)
            # Preserve evidence from other comparisons without treating it as
            # permission for any path in the selected comparison.
            if not selected:
                continue
            changed = changed_by_path.get(path)
            if changed is None:
                diagnostics.append(f"invalid declaration {declaration_path}: path is not in this comparison: {path}")
            elif change_category(path, changed_by_path) == "ordinary":
                diagnostics.append(f"invalid declaration {declaration_path}: path is not protected or upstream: {path}")
            elif path in declared:
                diagnostics.append(f"invalid declaration {declaration_path}: duplicate path: {path}")
            else:
                declared[path] = declaration_path
    return declared, diagnostics


def report_paths(
    paths: list[ChangedPath], declared: dict[str, str], changed_by_path: dict[str, ChangedPath]
) -> None:
    for item in sorted(paths, key=lambda value: value.path):
        category = change_category(item.path, changed_by_path)
        if category == "ordinary":
            state = "not-applicable"
        elif item.path in declared:
            state = "declared"
        else:
            state = "undeclared"
        print(f"path={item.path} category={category} status={item.status} declaration={state}")


def parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", required=True, help="comparison base commit or ref")
    parser.add_argument("--head", help="comparison head commit or ref; omit for the working tree")
    parser.add_argument(
        "--scope", choices=DECLARATION_SCOPES, default="task",
        help="declaration scope; pull-request requires a declaration of the entire PR diff",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        repo = find_repo_root()
        ensure_repository_is_comparable(repo)
        base = resolve_commit(repo, args.base, "base")
        head = resolve_commit(repo, args.head, "head") if args.head is not None else None
        paths = changed_paths(repo, base, head)
        changed_by_path = {item.path: item for item in paths}
        declared, diagnostics = load_declarations(repo, paths, changed_by_path, base, head, args.scope)
    except ComparisonUnavailable as exc:
        print(f"diagnostic: comparison unavailable: {exc}")
        return EXIT_UNAVAILABLE

    print(f"scope={args.scope}")
    print(f"base={base}")
    print(f"head={head if head is not None else 'working-tree'}")
    report_paths(paths, declared, changed_by_path)

    protected_paths = [item.path for item in paths if change_category(item.path, changed_by_path) != "ordinary"]
    for path in protected_paths:
        if path not in declared:
            diagnostics.append(f"undeclared protected or upstream change: {path}")
    for diagnostic in diagnostics:
        print(f"diagnostic: {diagnostic}")

    if diagnostics:
        print("result=invalid")
        return EXIT_INVALID
    print("result=ok (declaration presence is not human approval or semantic review)")
    return EXIT_OK


if __name__ == "__main__":
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except Exception:
            pass
    sys.exit(main())
