"""Package defaults, project configuration and explicit-root bundle discovery."""
from __future__ import annotations

import os
import re
from pathlib import Path
from .doc import Doc
from .errors import OkfError
from .fsutil import read_text, rel_posix, path_matches
from . import yamlio as _yamlio

DEFAULTS_PATH = Path(__file__).resolve().parent / "defaults.yml"
CONFIG_FILENAME = "okf.yml"
RESERVED_DEFAULT = ("index.md", "log.md")
INDEX_LINK_STYLES = ("bundle-absolute", "relative")


def merge_config(base: dict, override: dict) -> dict:
    """``base`` に ``override`` を重ねた新しい dict を返す。

    dict は再帰的にマージし、**リストとスカラーは丸ごと置換**する。
    リストを追記扱いにすると「既定の語彙を減らせない」ため、
    プロジェクト側が ``types`` を書いたらその内容が唯一の正になる。
    """
    out = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(out.get(key), dict):
            out[key] = merge_config(out[key], value)
        else:
            out[key] = value
    return out


def load_merged_config(cfg_path: Path, *, defaults_path: Path = DEFAULTS_PATH) -> dict:
    """同梱の ``defaults.yml`` にプロジェクトの ``okf.yml`` を重ねて返す。"""
    if not defaults_path.exists():  # pragma: no cover - 壊れたインストール向け
        raise OkfError(f"同梱の既定設定が見つかりません: {defaults_path}")
    defaults = _yamlio.parse_yaml(read_text(defaults_path), str(defaults_path))
    if not isinstance(defaults, dict):  # pragma: no cover
        raise OkfError(f"既定設定の形式が不正です: {defaults_path}")

    project = _yamlio.parse_yaml(read_text(cfg_path), str(cfg_path))
    if project is None:
        project = {}
    if not isinstance(project, dict):
        raise OkfError(f"設定ファイルの形式が不正です: {cfg_path}")
    return merge_config(defaults, project)


class Bundle:
    """docs/ バンドル全体と設定を保持する。"""

    def __init__(self, config_path: Path | None = None, *, repo_root: Path, doc_factory=Doc, defaults_path: Path = DEFAULTS_PATH):
        self.repo_root = Path(repo_root).resolve()
        self._doc_factory = doc_factory
        cfg_path = config_path or (self.repo_root / CONFIG_FILENAME)
        if not cfg_path.exists():
            raise OkfError(
                f"設定ファイルが見つかりません: {cfg_path}\n"
                "  `okf init` で生成するか、--config でパスを指定してください。"
            )
        cfg = load_merged_config(cfg_path, defaults_path=defaults_path)
        self.cfg = cfg
        self.code_glob_exclude = cfg.get("code_glob_exclude", [])
        if not isinstance(self.code_glob_exclude, list) or any(
            not isinstance(rule, str) or not rule.strip() for rule in self.code_glob_exclude
        ):
            raise OkfError("code_glob_exclude は空でない glob 文字列のリストで指定してください")
        try:
            for rule in self.code_glob_exclude:
                path_matches("", rule)
        except re.error as exc:
            raise OkfError("code_glob_exclude に不正な glob があります") from exc
        self.config_path = cfg_path
        self.root = (self.repo_root / str(cfg.get("bundle_root", "docs"))).resolve()
        self.exclude = list(cfg.get("exclude") or [])
        self.reserved = tuple(cfg.get("reserved") or RESERVED_DEFAULT)
        self.types = list(cfg.get("types") or [])
        self.statuses = list(cfg.get("statuses") or ["draft", "stable", "deprecated"])
        self.site_name = str(cfg.get("site_name") or self.repo_root.name)
        self.layers = list(cfg.get("layers") or [])
        raw_index_cfg = cfg.get("index", {})
        if not isinstance(raw_index_cfg, dict):
            raise OkfError("設定 `index` はマップで指定してください")
        self.index_cfg = dict(raw_index_cfg)
        self.index_link_style = self._validate_index_link_style()
        self.backlog_cfg = dict(cfg.get("backlog") or {})
        self.log_cfg = dict(cfg.get("log") or {})
        self._docs: list[Doc] | None = None
        self.declared_version = None
        root_index = self.root / "index.md"
        if self.root.is_relative_to(self.repo_root) and not root_index.is_symlink() and root_index.is_file():
            metadata = Doc(root_index, self.root, repo_root=self.repo_root, okf03=True)
            if not metadata.has_fm or metadata.fm_error:
                metadata = Doc(root_index, self.root, repo_root=self.repo_root)
            value = metadata.get("okf_version")
            if isinstance(value, (str, int, float)) and not isinstance(value, bool) and str(value).strip():
                self.declared_version = str(value).strip()
        version = self.declared_version
        if version is None and not root_index.exists():
            version = str(self.index_cfg.get("okf_version", "0.2"))
        parts = re.fullmatch(r"(\d+)\.(\d+)", version or "")
        self.okf03 = version is not None and (parts is None or tuple(map(int, parts.groups())) >= (0, 3))

    def _validate_index_link_style(self) -> str:
        value = self.index_cfg.get("link_style", "bundle-absolute")
        if not isinstance(value, str) or value not in INDEX_LINK_STYLES:
            allowed = " / ".join(f"`{item}`" for item in INDEX_LINK_STYLES)
            raise OkfError(f"設定 `index.link_style` は {allowed} のいずれかの文字列で指定してください")
        return value

    # -- パス判定 ----------------------------------------------------------
    def is_excluded(self, path: Path) -> bool:
        try:
            rel = rel_posix(path, self.root)
        except ValueError:
            return True
        if self.okf03 and rel != "." and any(part.startswith(".") for part in rel.split("/")):
            return True
        return any(path_matches(rel, pat) for pat in self.exclude)

    def dirs(self) -> list[Path]:
        """index 生成対象のディレクトリ（バンドルルート含む）を昇順で返す。"""
        found = [self.root]
        for dirpath, dirnames, _files in os.walk(self.root):
            dirnames[:] = sorted(
                d for d in dirnames
                if self.includes_dir(Path(dirpath) / d)
            )
            for d in dirnames:
                found.append(Path(dirpath) / d)
        return sorted(set(found), key=lambda p: rel_posix(p, self.root) if p != self.root else "")

    def includes_dir(self, path: Path) -> bool:
        if self.okf03:
            return not path.is_symlink() and not self.is_excluded(path)
        return not path.name.startswith(("_", ".")) and not self.is_excluded(path)

    def is_reserved(self, name: str) -> bool:
        return name in self.reserved or (self.okf03 and name in RESERVED_DEFAULT)

    def md_files(self, include_reserved: bool = False, directory: Path | None = None) -> list[Path]:
        folders = self.dirs() if directory is None else [directory]
        return [
            p for folder in folders for p in sorted(folder.iterdir())
            if p.suffix == ".md" and (not self.okf03 or not p.is_symlink())
            and (include_reserved or not self.is_reserved(p.name))
            and not self.is_excluded(p) and p.is_file()
        ]

    def document(self, path: Path) -> Doc:
        if self.okf03:
            return self._doc_factory(path, self.root, repo_root=self.repo_root, okf03=True)
        return self._doc_factory(path, self.root, repo_root=self.repo_root)

    def docs(self, directory: Path | None = None) -> list[Doc]:
        """非予約文書の一覧。OKF 0.3 はコンセプトだけを返す。"""
        if directory is None and self._docs is not None:
            return self._docs
        docs = [self.document(p) for p in self.md_files(directory=directory)]
        if self.okf03:
            docs = [doc for doc in docs if doc.type]
        if directory is None:
            self._docs = docs
        return docs

    def backlog_dir(self) -> Path:
        return self.root / str(self.backlog_cfg.get("dir", "backlog"))

    # -- log の出力先 ------------------------------------------------------
    def log_layers(self) -> list[str]:
        """自動追記の対象になる層。"""
        value = self.log_cfg.get("layers")
        if value is None:
            return list(self.layers)
        return [str(v) for v in value]

    def log_path(self, layer: str) -> Path:
        """層 → log.md のパス（`log.paths` で層ごとに差し替え可能）。"""
        paths = self.log_cfg.get("paths") or {}
        rel = paths.get(layer) if isinstance(paths, dict) else None
        if rel:
            return (self.root / str(rel)).resolve()
        return (self.root / layer / "log.md").resolve()
