"""render: HTML 生成、リンク変換、hook の非ブロッキング動作。"""

from __future__ import annotations

import argparse
import contextlib
import io
import json
import unittest
from pathlib import Path
from urllib.parse import quote

from okf_devkit import cli as okf
from okf_devkit import renderer
from helpers import OkfTestCase, doc_text, ns


class LinkRewriteTests(unittest.TestCase):
    def test_bundle_link_is_rewritten_relative_to_output(self) -> None:
        actual, target, warning = renderer.rewrite_href(
            "project/overview.md",
            "project/overview.html",
            "/client/architecture.md#state",
            {"project/overview.md", "client/architecture.md"},
        )
        self.assertEqual("../client/architecture.html#state", actual)
        self.assertEqual("client/architecture.md", target)
        self.assertIsNone(warning)

    def test_external_and_fragment_links_are_unchanged(self) -> None:
        pages = {"index.md"}
        for href in ("https://example.com/readme.md", "mailto:test@example.com", "#section"):
            self.assertEqual(href, renderer.rewrite_href("index.md", "index.html", href, pages)[0])

    def test_missing_target_is_warn_only(self) -> None:
        actual, target, warning = renderer.rewrite_href(
            "index.md", "index.html", "/missing.md", {"index.md"}
        )
        self.assertEqual("/missing.md", actual)
        self.assertIsNone(target)
        self.assertIn("HTML 化できない", warning or "")

    def test_encoded_special_path_is_resolved_once_and_reencoded_for_html(self) -> None:
        actual, target, warning = renderer.rewrite_href(
            "index.md",
            "index.html",
            "/foo%20%28x%29%20%25%20日本語.md",
            {"index.md", "foo (x) % 日本語.md"},
        )
        expected = quote("foo (x) % 日本語.html", safe="/:@-._~!$&'()*+,;=")
        self.assertEqual(expected, actual)
        self.assertEqual("foo (x) % 日本語.md", target)
        self.assertIsNone(warning)


@unittest.skipUnless(renderer.MarkdownIt is not None, "markdown-it-py が必要")
class RenderBundleTests(OkfTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.write("src/a.ts", "export const a = 1;\n")
        self.write("docs/index.md", "---\nokf_version: \"0.2\"\n---\n\n# Docs\n\n[文書A](/client/a.md)\n")
        self.write(
            "docs/client/a.md",
            doc_text(
                title="文書A",
                extra="related:\n  - /client/b.md",
                body=(
                    "# 文書A\n\n"
                    "[文書B](/client/b.md#詳細) [外部](https://example.com/readme.md)\n\n"
                    "<script>alert('x')</script>\n\n"
                    "テンプレート例: `{{RELATED}}` / `{{FOO_BAR}}`\n\n"
                    "```text\n/client/b.md\n```\n\n"
                    "```mermaid\ngraph TD\n  A --> B\n```\n"
                ),
            ),
        )
        self.write(
            "docs/client/b.md",
            doc_text(title="文書B", body="# 文書B\n\n## 詳細\n\n本文。\n"),
        )
        self.write("docs/_templates/skip.md", "# 生成しない\n")

    def test_render_all_pages_with_html_navigation_and_safe_content(self) -> None:
        bundle = self.bundle()
        report = renderer.render_bundle(bundle, okf.Doc)
        self.assertEqual(3, report.pages)
        self.assertTrue((self.docs / "index.html").exists())
        self.assertTrue((self.docs / "client/a.html").exists())
        self.assertFalse((self.docs / "_templates/skip.html").exists())
        self.assertTrue((self.docs / "_assets/docs.css").exists())

        page = self.read("docs/client/a.html")
        self.assertIn('href="b.html#%E8%A9%B3%E7%B4%B0"', page)
        self.assertIn('href="https://example.com/readme.md"', page)
        self.assertIn("/client/b.md", page)  # code block / related の表示文字列は保持
        self.assertIn("&lt;script&gt;alert('x')&lt;/script&gt;", page)
        self.assertIn("{{RELATED}}", page)
        self.assertIn("{{FOO_BAR}}", page)
        self.assertIn('class="mermaid"', page)
        self.assertIn("このページへのリンク", self.read("docs/client/b.html"))

        second = renderer.render_bundle(self.bundle(), okf.Doc)
        self.assertEqual(0, second.written)

    def test_removed_source_cleans_only_generated_html(self) -> None:
        renderer.render_bundle(self.bundle(), okf.Doc)
        authored = self.write(
            "docs/handwritten.html",
            "<!doctype html><title>SampleApp OKF renderer</title><!-- Generated from example -->\n",
        )
        (self.docs / "client/b.md").unlink()

        report = renderer.render_bundle(self.bundle(), okf.Doc)

        self.assertEqual(1, report.removed)
        self.assertFalse((self.docs / "client/b.html").exists())
        self.assertTrue(authored.exists())

    def test_separate_site_keeps_markdown_source_link(self) -> None:
        output = self.repo / "_site"
        renderer.render_bundle(self.bundle(), okf.Doc, output)
        page = self.read("_site/client/a.html")
        self.assertIn('href="../../docs/client/a.md"', page)
        self.assertIn('href="../index.html"', page)

    def test_check_mode_does_not_write(self) -> None:
        report = renderer.render_bundle(self.bundle(), okf.Doc, write=False)
        self.assertEqual(3, report.pages)
        self.assertEqual(0, report.written)
        self.assertFalse((self.docs / "index.html").exists())

    def test_hook_mode_outputs_empty_json_and_never_returns_two(self) -> None:
        args = argparse.Namespace(output=None, check=False, hook=True)
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            result = okf.cmd_render(self.bundle(), args)
        self.assertEqual(0, result)
        self.assertEqual({}, json.loads(stdout.getvalue()))

    def test_hook_failure_is_non_blocking_exit_one_not_two(self) -> None:
        stdout = io.StringIO()
        stderr = io.StringIO()
        missing = self.repo / "missing.yml"
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            result = okf.main(["--config", str(missing), "render", "--hook"])
        self.assertEqual(1, result)
        self.assertNotEqual(2, result)
        self.assertNotIn("decision", stdout.getvalue())


@unittest.skipUnless(renderer.MarkdownIt is not None, "markdown-it-py が必要")
class RelativeIndexRenderTests(OkfTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.write(
            "docs/special dir/foo (x) % 日本語.md",
            doc_text(title="特殊文書", description="特殊文字。", code_globs=None),
        )
        self.write(
            "docs/project/overview.md",
            doc_text(type_="Project Overview", title="概要", description="概要。", code_globs=None),
        )
        self.write(
            "docs/backlog/T-0001-task.md",
            doc_text(
                type_="Backlog Item",
                title="作業",
                description="作業の説明。",
                code_globs=None,
                extra=(
                    "state: done\n"
                    "priority: medium\n"
                    "effort: M\n"
                    "created: 2026-01-01\n"
                    "done_at: 2026-01-02"
                ),
            ),
        )

    def bundle(self) -> okf.Bundle:
        return super().bundle(index_link_style="relative")

    def test_adjacent_and_separate_html_rewrite_relative_indexes(self) -> None:
        bundle = self.bundle()
        self.assertEqual(0, okf.cmd_index(bundle, ns(write=True, check=False, quiet=True)))
        sources = {
            path: self.read(path)
            for path in (
                "docs/index.md",
                "docs/special dir/index.md",
                "docs/project/index.md",
                "docs/backlog/index.md",
            )
        }

        report = renderer.render_bundle(bundle, okf.Doc)
        self.assertFalse(report.warnings)
        root = self.read("docs/index.html")
        self.assertIn('href="special%20dir/index.html"', root)
        self.assertIn('href="project/index.html"', root)
        special = self.read("docs/special dir/index.html")
        special_href = quote("foo (x) % 日本語.html", safe="/:@-._~!$&'()*+,;=")
        self.assertIn(f'href="{special_href}"', special)
        self.assertIn('href="overview.html"', self.read("docs/project/index.html"))
        self.assertIn('href="T-0001-task.html"', self.read("docs/backlog/index.html"))
        self.assertEqual(sources, {path: self.read(path) for path in sources})

        output = self.repo / "_site"
        separate = renderer.render_bundle(self.bundle(), okf.Doc, output)
        self.assertGreater(separate.written, 0)
        self.assertIn('href="special%20dir/index.html"', self.read("_site/index.html"))
        self.assertIn(f'href="{special_href}"', self.read("_site/special dir/index.html"))
        self.assertIn('href="overview.html"', self.read("_site/project/index.html"))
        self.assertIn('href="T-0001-task.html"', self.read("_site/backlog/index.html"))


class HookConfigurationTests(unittest.TestCase):
    """同梱の hook ラッパーが「モデルを継続させない」契約を守っているか検証する。"""

    def wrappers(self) -> list[Path]:
        found = sorted((okf.SCAFFOLD_DIR / "hooks").iterdir())
        self.assertTrue(found, "scaffold の hook スクリプトが同梱されていない")
        return found

    def test_wrappers_invoke_render_hook(self) -> None:
        for wrapper in self.wrappers():
            text = wrapper.read_text(encoding="utf-8")
            self.assertIn("render --hook", text, wrapper.name)

    def test_wrappers_never_request_model_continuation(self) -> None:
        # 終了コード 2 と `decision: block` は「LLM に差し戻す」合図であり、
        # HTML 生成の hook からは決して返してはいけない。
        # 契約を説明するコメント行は対象外にし、実行される部分だけを見る。
        for wrapper in self.wrappers():
            text = "\n".join(
                line for line in wrapper.read_text(encoding="utf-8").splitlines()
                if not line.lstrip().startswith("#")
            )
            self.assertNotIn("exit 2", text, wrapper.name)
            self.assertNotIn("decision", text, wrapper.name)
            self.assertNotIn("sync --gate", text, wrapper.name)
