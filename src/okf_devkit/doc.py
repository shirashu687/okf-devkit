"""Frontmatter document model with an explicit project root."""
from __future__ import annotations

import re
from pathlib import Path
from .errors import OkfError
from .fsutil import read_text, rel_posix
from . import yamlio as _yamlio

CODE_GLOBS_REQUIRED_TYPES = ("Project Overview", "Architecture", "Reference", "How-To")


class Doc:
    """バンドル内の 1 ファイルを表す。"""

    def __init__(self, path: Path, bundle_root: Path, *, repo_root: Path):
        self.path = path
        self.repo_rel = rel_posix(path, repo_root)
        self.bundle_rel = "/" + rel_posix(path, bundle_root)
        self.name = path.name
        self.text = read_text(path)
        self.fm: dict = {}
        self.fm_error: str | None = None
        self.has_fm = False
        self.fm_opened = False  # 先頭が `---` だったか（終端欠落の判定用）
        self.body = self.text
        self._fm_lines: list[str] = []
        self._parse()

    def _parse(self) -> None:
        lines = self.text.split("\n")
        if not lines or lines[0].strip() != "---":
            return
        self.fm_opened = True
        end = None
        for idx in range(1, len(lines)):
            if lines[idx].strip() in ("---", "..."):
                end = idx
                break
        if end is None:
            self.fm_error = "frontmatter の終端 `---` がありません"
            return
        self.has_fm = True
        self._fm_lines = lines[1:end]
        self.body = "\n".join(lines[end + 1:])
        try:
            data = _yamlio.parse_yaml("\n".join(self._fm_lines), self.repo_rel)
        except OkfError as exc:
            self.fm_error = str(exc)
            return
        if data is None:
            data = {}
        if not isinstance(data, dict):
            self.fm_error = "frontmatter がマップではありません"
            return
        self.fm = data

    # -- 参照系 ------------------------------------------------------------
    def get(self, key, default=None):
        value = self.fm.get(key, default)
        return default if value is None else value

    def key_line(self, key: str) -> int | None:
        """frontmatter 内のトップレベルキーの行番号（1 始まり）。"""
        for idx, line in enumerate(self._fm_lines):
            if re.match(rf"^{re.escape(key)}\s*:", line):
                return idx + 2  # `---` の分
        return None

    @property
    def h1(self) -> str | None:
        for line in self.body.split("\n"):
            m = re.match(r"^#\s+(.+?)\s*$", line)
            if m:
                return m.group(1)
        return None

    @property
    def title(self) -> str:
        title = self.fm.get("title")
        if isinstance(title, str) and title.strip():
            return title.strip()
        if self.h1:
            return self.h1
        return self.path.stem.replace("-", " ").replace("_", " ")

    @property
    def description(self) -> str:
        desc = self.fm.get("description")
        return desc.strip() if isinstance(desc, str) else ""

    @property
    def type(self) -> str:
        value = self.fm.get("type")
        return value.strip() if isinstance(value, str) else ""

    @property
    def status(self) -> str:
        value = self.fm.get("status")
        return value.strip() if isinstance(value, str) else "stable"

    def code_globs(self) -> list[str]:
        """`code_globs` の一覧（正しい形式のものだけ）。更新検知の起点。

        OKF 標準の `sources` は出典（provenance）専用なので、変更監視用の
        glob はこの独自キーに分離している。
        """
        out = []
        raw = self.fm.get("code_globs")
        if isinstance(raw, list):
            for item in raw:
                if isinstance(item, str) and item.strip():
                    out.append(item.strip().replace("\\", "/"))
        return out

    def code_globs_problems(self) -> list[str]:
        """`code_globs` の形式上の問題を返す。

        欠如が問題かどうかは type / status に依存するため、ここでは
        「書かれている場合の形式」だけを検査する。
        """
        problems: list[str] = []
        raw = self.fm.get("code_globs")
        if raw is None:
            return problems
        if not isinstance(raw, list):
            return [f"`code_globs` はリストである必要があります（現在: {type(raw).__name__}）"]
        for pos, item in enumerate(raw, start=1):
            if not isinstance(item, str) or not item.strip():
                problems.append(f"`code_globs[{pos}]` が空、または文字列ではありません")
        return problems

    def requires_code_globs(self) -> bool:
        """このドキュメントが `code_globs` を必須とするか。

        コードから導出される type のみ必須。`status: deprecated` は除外する。
        """
        if self.status == "deprecated":
            return False
        return self.type in CODE_GLOBS_REQUIRED_TYPES

    def source_problems(self) -> list[str]:
        """`sources`（OKF 標準の provenance）の形式上の問題を返す。欠如は問題としない。"""
        problems: list[str] = []
        raw = self.fm.get("sources")
        if raw is None:
            return problems
        if not isinstance(raw, list):
            return [f"`sources` はリストである必要があります（現在: {type(raw).__name__}）"]
        for pos, item in enumerate(raw, start=1):
            if not isinstance(item, dict):
                problems.append(f"`sources[{pos}]` はマップ（`- resource: ...`）である必要があります")
                continue
            resource = item.get("resource")
            if not isinstance(resource, str) or not resource.strip():
                problems.append(f"`sources[{pos}].resource` が空、または文字列ではありません")
        return problems
