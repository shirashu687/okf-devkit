"""index コマンド: golden test / 冪等性 / マーカー破損時の非書き込み。"""

from __future__ import annotations

import contextlib
import io
from pathlib import Path
from urllib.parse import unquote, urlsplit
import unittest

from helpers import OkfTestCase, doc_text, ns
from okf_devkit import cli as okf


GOLDEN_ROOT = """\
---
okf_version: "0.2"
---

# テスト ドキュメント

<!-- okf:auto:start -->
## ディレクトリ
* [client ドキュメント](/client/index.md)

## Reference
* [Alpha](/alpha.md) - アルファの説明。
<!-- okf:auto:end -->
"""

GOLDEN_CLIENT = """\
# client ドキュメント

<!-- okf:auto:start -->
## Architecture
* [Beta](/client/beta.md) - ベータの説明。

## Reference
* [Gamma (draft)](/client/gamma.md) - ガンマの説明。

## 非推奨
* [Delta](/client/delta.md) - デルタの説明。
<!-- okf:auto:end -->
"""


class IndexGoldenTest(OkfTestCase):
    def build(self) -> okf.Bundle:
        self.write("docs/alpha.md", doc_text(title="Alpha", description="アルファの説明。",
                                             layer="shared", code_globs=None))
        self.write("docs/client/beta.md", doc_text(type_="Architecture", title="Beta",
                                                   description="ベータの説明。", code_globs=None))
        self.write("docs/client/gamma.md", doc_text(title="Gamma", description="ガンマの説明。",
                                                     status="draft", code_globs=None))
        self.write("docs/client/delta.md", doc_text(title="Delta", description="デルタの説明。",
                                                     status="deprecated", code_globs=None))
        return self.bundle()

    def test_golden_output(self):
        bundle = self.build()
        self.assertEqual(0, okf.cmd_index(bundle, ns(write=True, check=False, quiet=True)))
        self.assertEqual(GOLDEN_ROOT, self.read("docs/index.md"))
        self.assertEqual(GOLDEN_CLIENT, self.read("docs/client/index.md"))

    def test_idempotent_second_run(self):
        bundle = self.build()
        okf.cmd_index(bundle, ns(write=True, check=False, quiet=True))
        first_root = self.read("docs/index.md")
        first_client = self.read("docs/client/index.md")

        bundle2 = self.bundle()
        self.assertEqual(0, okf.cmd_index(bundle2, ns(write=True, check=False, quiet=True)))
        self.assertEqual(first_root, self.read("docs/index.md"))
        self.assertEqual(first_client, self.read("docs/client/index.md"))
        # --check も差分なしになる
        self.assertEqual(0, okf.cmd_index(self.bundle(), ns(write=False, check=True, quiet=True)))

    def test_preamble_outside_markers_is_kept(self):
        bundle = self.build()
        okf.cmd_index(bundle, ns(write=True, check=False, quiet=True))
        text = self.read("docs/client/index.md")
        self.write("docs/client/index.md", text.replace("# client ドキュメント\n",
                                                        "# client ドキュメント\n\n手書きの前文。\n"))
        okf.cmd_index(self.bundle(), ns(write=True, check=False, quiet=True))
        self.assertIn("手書きの前文。", self.read("docs/client/index.md"))

    def test_markdown_special_chars_are_escaped(self):
        self.write("docs/alpha.md", doc_text(title="A [b] (c)", description="説明。",
                                             layer="shared", code_globs=None))
        okf.cmd_index(self.bundle(), ns(write=True, check=False, quiet=True))
        text = self.read("docs/index.md")
        self.assertIn(r"* [A \[b\] (c)](/alpha.md)", text)

    def test_explicit_bundle_absolute_keeps_the_golden_output(self):
        bundle = self.build()
        config = self.make_config(index_link_style="bundle-absolute")
        bundle = okf.Bundle(config)
        self.assertEqual(0, okf.cmd_index(bundle, ns(write=True, check=False, quiet=True)))
        self.assertEqual(GOLDEN_ROOT, self.read("docs/index.md"))
        self.assertEqual(GOLDEN_CLIENT, self.read("docs/client/index.md"))

    def test_explicit_bundle_absolute_keeps_backlog_links(self):
        self.build()
        self.write(
            "docs/backlog/T-0001-task.md",
            doc_text(
                type_="Backlog Item",
                title="作業",
                description="作業の説明。",
                layer="shared",
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
        config = self.make_config(index_link_style="bundle-absolute")
        self.assertEqual(0, okf.cmd_index(okf.Bundle(config), ns(write=True, check=False, quiet=True)))
        self.assertIn("* [作業](/backlog/T-0001-task.md)", self.read("docs/backlog/index.md"))


class RelativeIndexLinkTests(OkfTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.write(
            "docs/special dir/foo (x) % 日本語.md",
            doc_text(title="特殊文書", description="特殊文字。", layer="shared", code_globs=None),
        )
        self.write(
            "docs/project/overview.md",
            doc_text(type_="Project Overview", title="概要", description="概要。", code_globs=None),
        )
        backlog_fields = {
            "doing": ("high", "T-0001-doing.md"),
            "todo": ("medium", "T-0002-todo.md"),
            "done": ("low", "T-0003 (x) % 日本語.md"),
            "dropped": ("low", "T-0004-dropped.md"),
        }
        for state, (priority, name) in backlog_fields.items():
            done_at = "2026-01-02" if state == "done" else "null"
            self.write(
                f"docs/backlog/{name}",
                doc_text(
                    type_="Backlog Item",
                    title=f"{state} task",
                    description=f"{state} の説明。",
                    layer="shared",
                    code_globs=None,
                    extra=(
                        f"state: {state}\n"
                        f"priority: {priority}\n"
                        "effort: M\n"
                        "created: 2026-01-01\n"
                        f"done_at: {done_at}"
                    ),
                ),
            )

    def bundle(self) -> okf.Bundle:
        return super().bundle(index_link_style="relative")

    def assert_link_resolves(self, index_rel: str, href: str) -> None:
        path = unquote(urlsplit(href).path)
        target = (self.repo / "docs" / Path(index_rel).parent / path).resolve()
        self.assertTrue(target.is_file(), f"{index_rel}: {href} -> {target}")

    def test_relative_links_use_each_index_parent_and_keep_all_states(self):
        bundle = self.bundle()
        self.assertEqual(0, okf.cmd_index(bundle, ns(write=True, check=False, quiet=True)))

        root = self.read("docs/index.md")
        self.assertIn("* [special dir ドキュメント](./special%20dir/index.md)", root)
        self.assertIn("* [project ドキュメント](./project/index.md)", root)

        special = self.read("docs/special dir/index.md")
        special_href = "./foo%20%28x%29%20%25%20日本語.md"
        self.assertIn(f"]({special_href})", special)
        self.assert_link_resolves("special dir/index.md", special_href)

        project = self.read("docs/project/index.md")
        self.assertIn("* [概要](./overview.md)", project)
        self.assert_link_resolves("project/index.md", "./overview.md")

        backlog = self.read("docs/backlog/index.md")
        for state in ("doing", "todo", "done", "dropped"):
            self.assertIn(f"## {state}", backlog)
        self.assertIn("./T-0003%20%28x%29%20%25%20日本語.md", backlog)
        self.assert_link_resolves("backlog/index.md", "./T-0003%20%28x%29%20%25%20日本語.md")

    def test_relative_regeneration_is_idempotent_and_checkable(self):
        bundle = self.bundle()
        self.assertEqual(0, okf.cmd_index(bundle, ns(write=True, check=False, quiet=True)))
        first = {
            path: self.read(path)
            for path in (
                "docs/index.md",
                "docs/special dir/index.md",
                "docs/project/index.md",
                "docs/backlog/index.md",
            )
        }
        self.assertEqual(0, okf.cmd_index(self.bundle(), ns(write=True, check=False, quiet=True)))
        self.assertEqual(0, okf.cmd_index(self.bundle(), ns(write=False, check=True, quiet=True)))
        self.assertEqual(first, {path: self.read(path) for path in first})

    def test_lint_and_sync_use_the_same_relative_link_style(self):
        bundle = self.bundle()
        output = io.StringIO()
        with contextlib.redirect_stdout(output), contextlib.redirect_stderr(output):
            result = okf.cmd_sync(bundle, ns(gate=False))
        self.assertEqual(0, result)
        self.assertIn("./project/index.md", self.read("docs/index.md"))
        self.assertIn("./overview.md", self.read("docs/project/index.md"))
        findings = okf.run_lint(self.bundle())
        self.assertFalse([f for f in findings if f.rule == "L13" and f.level == "error"])


class InvalidIndexConfigTests(OkfTestCase):
    def test_invalid_link_style_fails_without_writing_any_index(self):
        config = self.make_config()
        base_config = config.read_text(encoding="utf-8")
        sentinel = "# keep this file\n"
        self.write("docs/index.md", sentinel)
        for raw in ("unknown", "null", "123", "[relative]"):
            with self.subTest(raw=raw):
                config.write_text(
                    base_config.replace(
                        '  okf_version: "0.2"\n',
                        f'  okf_version: "0.2"\n  link_style: {raw}\n',
                    ),
                    encoding="utf-8",
                    newline="\n",
                )
                stdout = io.StringIO()
                stderr = io.StringIO()
                with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                    result = okf.main(["--config", str(config), "index", "--write"])
                self.assertEqual(1, result)
                self.assertIn("index.link_style", stderr.getvalue())
                self.assertEqual(sentinel, self.read("docs/index.md"))


START = "<!-- okf:auto:start -->"
END = "<!-- okf:auto:end -->"

CORRUPTIONS = {
    "start_only": f"# x\n\n{START}\n## old\n",
    "end_only": f"# x\n\n## old\n{END}\n",
    "reversed": f"# x\n\n{END}\n## old\n{START}\n",
    "duplicate_start": f"# x\n\n{START}\n## a\n{START}\n## b\n{END}\n",
    "duplicate_end": f"# x\n\n{START}\n## a\n{END}\n## b\n{END}\n",
    "nested": f"# x\n\n{START}\n{START}\n## a\n{END}\n{END}\n",
    "two_pairs": f"# x\n\n{START}\n## a\n{END}\n\n{START}\n## b\n{END}\n",
}


class MarkerCorruptionTest(OkfTestCase):
    """壊れたマーカーでは 1 バイトも書き込まないこと（内容増殖の防止）。"""

    def setUp(self):
        super().setUp()
        self.write("docs/alpha.md", doc_text(title="Alpha", description="アルファ。",
                                             layer="shared", code_globs=None))
        self.write("docs/client/beta.md", doc_text(type_="Architecture", title="Beta",
                                                   description="ベータ。", code_globs=None))

    def test_each_corruption_blocks_all_writes(self):
        for name, broken in CORRUPTIONS.items():
            with self.subTest(corruption=name):
                self.write("docs/client/index.md", broken)
                if (self.repo / "docs/index.md").exists():
                    (self.repo / "docs/index.md").unlink()

                rc = okf.cmd_index(self.bundle(), ns(write=True, check=False, quiet=True))
                self.assertEqual(1, rc, "壊れたマーカーでは exit 1 になるべき")
                # 壊れたファイルは書き換えられていない
                self.assertEqual(broken, self.read("docs/client/index.md"))
                # 他のファイルも書かれていない（全体を中止する）
                self.assertFalse((self.repo / "docs/index.md").exists(),
                                 "破損検出時は他の index.md も書いてはいけない")

    def test_no_growth_on_repeated_runs(self):
        """レビューで報告された 95→161→227 byte の増殖が起きないこと。"""
        broken = CORRUPTIONS["reversed"]
        self.write("docs/client/index.md", broken)
        sizes = []
        for _ in range(3):
            okf.cmd_index(self.bundle(), ns(write=True, check=False, quiet=True))
            sizes.append(len(self.read("docs/client/index.md")))
        self.assertEqual([len(broken)] * 3, sizes)

    def test_missing_markers_are_appended(self):
        """マーカーが完全に無い場合だけ新規追加を許す。"""
        self.write("docs/client/index.md", "# client ドキュメント\n\n手書きのみ。\n")
        rc = okf.cmd_index(self.bundle(), ns(write=True, check=False, quiet=True))
        self.assertEqual(0, rc)
        text = self.read("docs/client/index.md")
        self.assertIn("手書きのみ。", text)
        self.assertEqual(1, text.count(START))
        self.assertEqual(1, text.count(END))

    def test_lint_reports_marker_error_instead_of_crashing(self):
        self.write("docs/client/index.md", CORRUPTIONS["reversed"])
        findings = okf.run_lint(self.bundle())
        marker = [f for f in findings if f.rule == "L13" and "マーカー" in f.message]
        self.assertTrue(marker, f"L13 でマーカー破損を報告すべき: {[str(f) for f in findings]}")


class SplitMarkersTest(unittest.TestCase):
    def test_valid_pair(self):
        text = f"pre\n{START}\nauto\n{END}\npost\n"
        self.assertEqual(("pre\n", "\npost\n"), okf.split_markers(text, START, END, "x"))

    def test_absent(self):
        self.assertIsNone(okf.split_markers("nothing", START, END, "x"))

    def test_errors(self):
        for name, broken in CORRUPTIONS.items():
            with self.subTest(corruption=name):
                with self.assertRaises(okf.MarkerError):
                    okf.split_markers(broken, START, END, "x")


if __name__ == "__main__":
    unittest.main()
