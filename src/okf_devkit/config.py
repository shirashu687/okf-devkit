"""Package defaults, project configuration and explicit-root bundle discovery."""
from __future__ import annotations

import os
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
        return any(path_matches(rel, pat) for pat in self.exclude)

    def dirs(self) -> list[Path]:
        """index 生成対象のディレクトリ（バンドルルート含む）を昇順で返す。"""
        found = [self.root]
        for dirpath, dirnames, _files in os.walk(self.root):
            dirnames[:] = sorted(
                d for d in dirnames
                if not d.startswith(("_", "."))
                and not self.is_excluded(Path(dirpath) / d)
            )
            for d in dirnames:
                found.append(Path(dirpath) / d)
        return sorted(set(found), key=lambda p: rel_posix(p, self.root) if p != self.root else "")

    def md_files(self, include_reserved: bool = False) -> list[Path]:
        out = []
        for d in self.dirs():
            for p in sorted(d.iterdir()):
                if p.is_file() and p.suffix == ".md" and not self.is_excluded(p):
                    if not include_reserved and p.name in self.reserved:
                        continue
                    out.append(p)
        return out

    def docs(self) -> list[Doc]:
        """非予約ファイルの Doc 一覧（キャッシュ付き）。"""
        if self._docs is None:
            self._docs = [self._doc_factory(p, self.root, repo_root=self.repo_root) for p in self.md_files()]
        return self._docs

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
