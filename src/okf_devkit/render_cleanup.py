"""Explicit, recoverable migration of verified renderer artifacts."""
from __future__ import annotations

import hashlib
import json
import os
import re
import stat
import uuid
from pathlib import Path

from .renderer import OWNERSHIP_MARKER, RenderError, _write_atomic

MANIFEST = ".okf-render-manifest.json"
BACKUPS = ".okf/render-backups"


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def artifact_bytes(content: str) -> bytes:
    return content.replace("\r\n", "\n").encode("utf-8")


def safe_path(repo: Path, path: Path) -> Path:
    """Check lexical bounds before resolution and every existing component."""
    repo = repo.resolve()
    if ".." in path.parts:
        raise RenderError("cleanup refuses parent traversal")
    # GetFullPathName can erase Windows trailing dot/space aliases.
    # Inspect the user's lexical spelling before normalization.
    if os.name == "nt" and any(part.endswith((".", " ")) for part in path.parts):
        raise RenderError("cleanup refuses ambiguous Windows path spelling")
    path = Path(os.path.abspath(path))
    try:
        rel = path.relative_to(repo)
    except ValueError as exc:
        raise RenderError("cleanup path must stay inside repository") from exc
    current = repo
    for part in rel.parts:
        if ":" in part or any(ord(char) < 32 for char in part) or (os.name == "nt" and part.endswith((".", " "))):
            raise RenderError("cleanup refuses unsafe path characters")
        current /= part
        try:
            info = current.lstat()
        except FileNotFoundError:
            continue
        if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & 0x400:
            raise RenderError(f"cleanup refuses symlink/reparse path: {current}")
    return path


def regular(repo: Path, path: Path) -> bool:
    safe_path(repo, path)
    if not path.exists():
        return False
    if not stat.S_ISREG(path.lstat().st_mode):
        raise RenderError(f"cleanup requires regular file: {path}")
    return True


def validate_roots(repo: Path, old: Path, new: Path) -> tuple[Path, Path]:
    old, new = safe_path(repo, old), safe_path(repo, new)
    backup = repo.resolve() / BACKUPS
    for root in (old, new):
        if root == repo.resolve() or root == backup or root in backup.parents or backup in root.parents:
            raise RenderError("cleanup root cannot be repository root or overlap backups")
        if root.exists() and not root.is_dir():
            raise RenderError("cleanup root must be a directory")
    if old == new or old in new.parents or new in old.parents:
        raise RenderError("cleanup roots must be distinct and non-nested")
    if old.exists() and new.exists() and os.path.samefile(old, new):
        raise RenderError("cleanup roots refer to the same directory")
    for root, other in ((old, new), (new, old)):
        if root.exists():
            for ancestor in other.parents:
                if ancestor.exists() and os.path.samefile(root, ancestor):
                    raise RenderError("cleanup roots overlap through a directory alias")
    return old, new


def valid_name(name: object) -> bool:
    return isinstance(name, str) and bool(name) and "\\" not in name and ":" not in name and not any(ord(char) < 32 for char in name) and not name.startswith("/") and all(p not in ("", ".", "..") for p in name.split("/")) and (name.endswith(".html") or name in ("_assets/docs.css", "_assets/docs.js"))


def read_manifest(repo: Path, root: Path) -> dict[str, str] | None:
    path = root / MANIFEST
    if not regular(repo, path):
        return None
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(value, dict) or set(value) != {"version", "generator", "output_root", "files"} or type(value["version"]) is not int or value["version"] != 1 or value["generator"] != "okf-devkit" or value["output_root"] != root.relative_to(repo.resolve()).as_posix() or not isinstance(value["files"], list):
            raise ValueError("schema")
        entries = {}
        seen_names = set()
        for entry in value["files"]:
            if not isinstance(entry, dict) or set(entry) != {"path", "sha256"} or not valid_name(entry["path"]) or not isinstance(entry["sha256"], str) or not re.fullmatch(r"[0-9a-f]{64}", entry["sha256"]) or entry["path"] in entries:
                raise ValueError("entry")
            key = entry["path"].casefold() if os.name == "nt" else entry["path"]
            if key in seen_names:
                raise ValueError("aliased duplicate entry")
            seen_names.add(key)
            entries[entry["path"]] = entry["sha256"]
        return entries
    except (ValueError, TypeError, KeyError) as exc:
        raise RenderError(f"invalid render manifest: {path}") from exc


def owned(name: str, data: bytes) -> bool:
    return not name.endswith(".html") or OWNERSHIP_MARKER.encode() in data[:256]


def write_manifest(repo: Path, root: Path, artifacts: dict[str, str]) -> None:
    safe_path(repo, root / MANIFEST)
    regular(repo, root / MANIFEST)
    value = {"version": 1, "generator": "okf-devkit", "output_root": root.relative_to(repo.resolve()).as_posix(), "files": [{"path": name, "sha256": digest(artifact_bytes(artifacts[name]))} for name in sorted(artifacts, key=lambda s: s.encode("utf-8"))]}
    _write_atomic(root / MANIFEST, json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def plan_cleanup(repo: Path, old: Path, new: Path, old_artifacts: dict[str, str], new_artifacts: dict[str, str]) -> tuple[list[tuple[Path, str, tuple]], list[str]]:
    old, new = validate_roots(repo, old, new)
    backup_anchor = safe_path(repo, repo.resolve() / BACKUPS)
    if backup_anchor.exists() and not backup_anchor.is_dir():
        raise RenderError("cleanup backup anchor must be a directory")
    old_entries = read_manifest(repo, old)
    new_entries = read_manifest(repo, new)
    # Manifest destination itself must also be safe before any render write.
    regular(repo, new / MANIFEST)
    for name, content in new_artifacts.items():
        target = new / name
        if regular(repo, target):
            data = target.read_bytes()
            if data != artifact_bytes(content) and not (new_entries and new_entries.get(name) == digest(data) and owned(name, data)):
                raise RenderError(f"cleanup refuses output overwrite: {target}")
    entries = old_entries if old_entries is not None else {name: digest(artifact_bytes(content)) for name, content in old_artifacts.items()}
    moves, lines = [], []
    for name in sorted(entries, key=lambda s: s.encode("utf-8")):
        path = old / name
        rel = path.relative_to(repo.resolve()).as_posix()
        if not regular(repo, path):
            lines.append(f"cleanup keep: {rel} (missing)")
            continue
        data = path.read_bytes()
        if digest(data) != entries[name] or not owned(name, data):
            lines.append(f"cleanup keep: {rel} (modified)")
            continue
        info = path.stat()
        moves.append((path, entries[name], (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns)))
        lines.append(f"cleanup move: {rel}")
    # Report untracked files, but never traverse linked directories.
    if old.exists():
        for directory, dirs, files in os.walk(old, followlinks=False):
            for child in list(dirs):
                safe_path(repo, Path(directory) / child)
            for child in files:
                path = Path(directory) / child
                safe_path(repo, path)
                name = path.relative_to(old).as_posix()
                if name not in entries and name != MANIFEST:
                    lines.append(f"cleanup keep: {path.relative_to(repo.resolve()).as_posix()} (untracked)")
    return moves, sorted(lines, key=lambda s: s.encode("utf-8"))


def same_file(repo: Path, path: Path, expected: str, identity: tuple) -> bool:
    if not regular(repo, path):
        return False
    info = path.stat()
    return (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns) == identity and digest(path.read_bytes()) == expected


def execute_cleanup(repo: Path, old: Path, new: Path, moves: list[tuple[Path, str, tuple]]) -> Path | None:
    if not moves:
        return None
    for source, expected, identity in moves:
        if not same_file(repo, source, expected, identity):
            raise RenderError(f"cleanup source changed: {source}")
    base = safe_path(repo, repo.resolve() / BACKUPS)
    base.mkdir(parents=True, exist_ok=True)
    backup = base / str(uuid.uuid4())
    backup.mkdir(exist_ok=False)
    receipt = {"version": 1, "old_root": old.relative_to(repo.resolve()).as_posix(), "new_root": new.relative_to(repo.resolve()).as_posix(), "status": "in-progress", "moves": [], "copies": []}
    receipt["planned"] = [
        {"path": source.relative_to(repo.resolve()).as_posix(),
         "backup": (backup / source.relative_to(repo.resolve())).relative_to(repo.resolve()).as_posix(),
         "sha256": expected}
        for source, expected, _identity in moves
    ]
    completed = []
    def save():
        _write_atomic(backup / "receipt.json", json.dumps(receipt, ensure_ascii=False, indent=2) + "\n")
    try:
        save()
        for source, expected, identity in moves:
            if not same_file(repo, source, expected, identity):
                raise RenderError(f"cleanup source changed: {source}")
            rel = source.relative_to(repo.resolve()).as_posix()
            target = backup / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open("xb") as stream:
                stream.write(source.read_bytes())
                stream.flush()
                os.fsync(stream.fileno())
            if digest(target.read_bytes()) != expected or not same_file(repo, source, expected, identity):
                raise RenderError(f"cleanup verification failed: {source}")
            receipt["copies"].append({"path": rel, "sha256": expected})
            save()
            source.unlink()
            completed.append((source, target, expected))
            receipt["moves"].append({"path": rel, "sha256": expected})
            save()
        receipt["status"] = "complete"
        save()
        return backup
    except Exception as exc:
        recovery = []
        for source, target, expected in reversed(completed):
            try:
                safe_path(repo, source)
                if not regular(repo, target) or digest(target.read_bytes()) != expected:
                    raise OSError("backup verification failed before restore")
                with source.open("xb") as stream:
                    stream.write(target.read_bytes())
                    stream.flush()
                    os.fsync(stream.fileno())
                if digest(source.read_bytes()) != expected:
                    raise OSError("restore verification failed")
            except Exception:
                recovery.append(target.relative_to(repo.resolve()).as_posix())
        receipt["status"] = "recovery-required" if recovery else "rolled-back"
        receipt["recovery_paths"] = recovery
        try:
            save()
        except Exception:
            pass
        raise RenderError(f"cleanup failed; {receipt['status']}; backups preserved: {backup}: {exc}") from exc
