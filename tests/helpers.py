"""okf-devkit のテスト用共通ヘルパー（標準ライブラリのみ）。

CLI は `REPO_ROOT`（= プロジェクトルート）を基準にファイルと git を触るため、
テストでは一時ディレクトリを `okf.REPO_ROOT` に差し替えて隔離する。
本物のリポジトリには一切触れない。
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from okf_devkit import cli as okf  # noqa: E402


CONFIG_TEMPLATE = """\
bundle_root: docs

exclude:
  - "_*"
  - "_*/**"
  - ".*"
  - ".*/**"

reserved:
  - index.md
  - log.md

types:
  - Project Overview
  - Architecture
  - Reference
  - How-To
  - Decision Record
  - Glossary
  - Backlog Item
  - Convention

statuses:
  - draft
  - stable
  - deprecated

layers:
  - client
  - server
  - batch
  - shared

layer_dirs:
  client: client
  server: server
  batch: batch
  shared: project

layer_map:
  - {{ glob: "app/client/**", layer: client }}
  - {{ glob: "app/server/**", layer: server }}
  - {{ glob: "app/batch/**", layer: batch }}
  - {{ glob: "docs/**", layer: skip }}
  - {{ glob: "**", layer: shared }}

kind_rules:
  - {{ pattern: '(追加|実装|新規|作成|\\badd(s|ed)?\\b|\\bfeat(ure)?\\b)', kind: "**Creation**" }}
  - {{ pattern: '(削除|廃止|\\bremove[ds]?\\b)', kind: "**Deprecation**" }}
  - {{ pattern: '.*', kind: "**Update**" }}

backlog:
  dir: backlog
  prefix: B
  states: [todo, doing, done, dropped]
  state_order: [doing, todo, done, dropped]
  priorities: [high, medium, low]
  efforts: [S, M, L, XL]
  feasibilities: [A, B, C, D]
  ai: [full, assisted, manual]

templates:
  Architecture: _templates/architecture.md
  Reference: _templates/reference.md
  How-To: _templates/how-to.md
  Decision Record: _templates/decision-record.md
  Glossary: _templates/glossary.md
  Backlog Item: _templates/backlog-item.md

index:
  start_marker: "<!-- okf:auto:start -->"
  end_marker: "<!-- okf:auto:end -->"
  root_heading: "テスト ドキュメント"
  heading_suffix: " ドキュメント"
  subdir_section: "ディレクトリ"
  other_section: "その他"
  deprecated_section: "非推奨"
  okf_version: "0.2"
{index_link_style_line}

log:
  heading_prefix: "変更履歴 — "
  layers: [client, server, batch]
  paths:
    client: client/log.md
    server: server/log.md
    batch: batch/log.md
    shared: log.md
{baseline_line}
stale:
  draft_days: 30
"""


def ns(**kwargs) -> argparse.Namespace:
    """argparse.Namespace の簡易生成。"""
    return argparse.Namespace(**kwargs)


class OkfTestCase(unittest.TestCase):
    """一時 REPO_ROOT を持つテストの基底クラス。"""

    def setUp(self) -> None:
        super().setUp()
        self.repo = Path(tempfile.mkdtemp(prefix="okf-test-")).resolve()
        self.addCleanup(shutil.rmtree, str(self.repo), True)
        self._orig_root = okf.REPO_ROOT
        self._orig_pyyaml = okf._pyyaml
        okf.REPO_ROOT = self.repo
        self.addCleanup(self._restore)
        self.reset_caches()
        self.docs = self.repo / "docs"
        self.docs.mkdir(parents=True, exist_ok=True)

    def _restore(self) -> None:
        okf.REPO_ROOT = self._orig_root
        okf._pyyaml = self._orig_pyyaml
        self.reset_caches()

    @staticmethod
    def reset_caches() -> None:
        okf._GLOB_CACHE.clear()
        okf._PATH_TIME_MAP = None

    # -- ファイル操作 ------------------------------------------------------
    def write(self, rel: str, text: str) -> Path:
        path = self.repo / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8", newline="\n")
        return path

    def read(self, rel: str) -> str:
        return (self.repo / rel).read_text(encoding="utf-8").replace("\r\n", "\n")

    def make_config(
        self,
        baseline: str | None = None,
        name: str = "okf-config.yml",
        index_link_style: str | None = None,
    ) -> Path:
        line = f"  baseline: {baseline}\n" if baseline else ""
        index_link_style_line = (
            f"  link_style: {index_link_style}\n" if index_link_style is not None else ""
        )
        path = self.repo / name
        path.write_text(
            CONFIG_TEMPLATE.format(
                baseline_line=line,
                index_link_style_line=index_link_style_line,
            ),
            encoding="utf-8",
            newline="\n",
        )
        return path

    def bundle(
        self,
        baseline: str | None = None,
        index_link_style: str | None = None,
    ) -> okf.Bundle:
        return okf.Bundle(self.make_config(baseline, index_link_style=index_link_style))

    def make_templates(self) -> None:
        """new コマンド用の最小テンプレート一式。"""
        common = (
            "---\n"
            "type: <TYPE>\n"
            "title: <TITLE>\n"
            "description: <一文>\n"
            "tags: []\n"
            "status: draft\n"
            "layer: <LAYER>\n"
            "generated:\n"
            "  by: <ACTOR>\n"
            "  at: <ISO>\n"
            "code_globs:\n"
            "  - TODO\n"
            "---\n"
            "\n"
            "# <TITLE>\n"
        )
        for name in ("architecture", "reference", "how-to", "decision-record", "glossary"):
            self.write(f"docs/_templates/{name}.md", common)
        self.write(
            "docs/_templates/backlog-item.md",
            "---\n"
            "type: Backlog Item\n"
            "title: <TITLE>\n"
            "description: <一文>\n"
            "tags: []\n"
            "status: draft\n"
            "layer: <LAYER>\n"
            "state: todo\n"
            "priority: medium\n"
            "effort: M\n"
            "created: 2000-01-01\n"
            "done_at: null\n"
            "generated:\n"
            "  by: <ACTOR>\n"
            "  at: <ISO>\n"
            "---\n"
            "\n"
            "# <TITLE>\n",
        )

    # -- git ---------------------------------------------------------------
    def git(self, *args: str, check: bool = True) -> str:
        proc = subprocess.run(
            ["git", *args],
            cwd=str(self.repo),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        if check and proc.returncode != 0:
            raise AssertionError(f"git {' '.join(args)} failed: {proc.stderr}")
        return proc.stdout

    def git_init(self) -> None:
        self.git("init", "--initial-branch=main")
        self.git("config", "user.email", "test@example.com")
        self.git("config", "user.name", "okf test")
        self.git("config", "commit.gpgsign", "false")

    def commit(self, message: str, files: dict[str, str] | None = None) -> str:
        for rel, text in (files or {}).items():
            self.write(rel, text)
        self.git("add", "-A")
        self.git("commit", "-m", message, "--allow-empty")
        self.reset_caches()
        return self.git("rev-parse", "HEAD").strip()


def doc_text(
    *,
    type_: str = "Reference",
    title: str = "Doc",
    description: str = "説明。",
    layer: str = "client",
    status: str | None = None,
    code_globs: str | None = "  - src/a.ts",
    sources: str | None = None,
    extra: str = "",
    body: str = "# Doc\n",
) -> str:
    """テスト用の frontmatter 付きドキュメントを組み立てる。"""
    lines = ["---", f"type: {type_}", f"title: {title}", f"description: {description}"]
    if status is not None:
        lines.append(f"status: {status}")
    lines.append(f"layer: {layer}")
    lines.append("generated:")
    lines.append("  by: claude-code/opus-5")
    lines.append("  at: 2026-01-01T00:00:00Z")
    if code_globs is not None:
        lines.append("code_globs:")
        lines.append(code_globs)
    if sources is not None:
        lines.append("sources:")
        lines.append(sources)
    if extra:
        lines.append(extra.rstrip("\n"))
    lines.append("---")
    lines.append("")
    return "\n".join(lines) + body
