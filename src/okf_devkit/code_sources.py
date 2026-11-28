"""Resolve named code sources independently of the documentation repository."""
from __future__ import annotations

import os
import re
from pathlib import Path

from . import gitutil
from .errors import OkfError
from .fsutil import path_matches

_NAME = re.compile(r"[A-Za-z][A-Za-z0-9_-]*")
_DRIVE = re.compile(r"[A-Za-z]:")


def split_code_glob(reference: str) -> tuple[str | None, str | None]:
    """Return the source and pattern. A missing named pattern is invalid."""
    name, separator, pattern = reference.partition(":")
    if not separator or not _NAME.fullmatch(name) or re.match(r"[A-Za-z]:[/\\]", reference):
        return None, reference
    pattern = pattern.replace("\\", "/")
    while pattern.startswith("./"):
        pattern = pattern[2:]
    if not pattern.strip() or "\0" in pattern or pattern.startswith("/") or _DRIVE.match(pattern) or ".." in pattern.split("/"):
        return name, None
    try:
        path_matches("", pattern)
    except re.error:
        return name, None
    return name, pattern


class CodeSources:
    def __init__(self, project_root: Path, declarations: object):
        self.project_root = project_root
        self.declarations = declarations
        self._roots: dict[str, Path] = {}

    def root(self, name: str) -> Path:
        if name in self._roots:
            return self._roots[name]
        if not _NAME.fullmatch(name):
            raise OkfError(f"ソース名 `{name}` が不正です")
        if not isinstance(self.declarations, list):
            raise OkfError("`code_sources` はリストで指定してください")
        entries = [entry for entry in self.declarations if isinstance(entry, dict) and entry.get("name") == name]
        if not entries:
            raise OkfError(f"ソース `{name}` が code_sources に登録されていません")
        if len(entries) > 1:
            raise OkfError(f"ソース `{name}` の宣言が重複しています")
        entry = entries[0]
        location = entry.get("path")
        if not isinstance(location, str) or not location.strip():
            raise OkfError(f"ソース `{name}` の path を指定してください")
        env_name = entry.get("path_env")
        if "path_env" in entry:
            if not isinstance(env_name, str) or not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", env_name):
                raise OkfError(f"ソース `{name}` の path_env は環境変数名で指定してください")
            location = os.environ.get(env_name) or location
        try:
            root = (self.project_root / location).resolve()
            if not root.is_dir():
                raise OkfError(f"ソース `{name}` のチェックアウトが見つかりません")
            rc, git_root = gitutil.source_git(root, "rev-parse", "--show-toplevel")
            top = git_root.rstrip("\r\n")
            if rc != 0 or not top or not root.samefile(top):
                raise OkfError(f"ソース `{name}` の配置先は Git の作業ツリールートではありません")
        except (OSError, RuntimeError, ValueError) as exc:
            raise OkfError(f"ソース `{name}` の配置先を確認できません") from exc
        self._roots[name] = root
        return root
