"""index コマンド: golden test / 冪等性 / マーカー破損時の非書き込み。"""

from __future__ import annotations

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
