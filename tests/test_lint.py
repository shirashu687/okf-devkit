"""lint: L4 / L7 / L8 / L10 / L11 / L12 の見逃し防止。"""

from __future__ import annotations

import unittest

from helpers import OkfTestCase, doc_text
from okf_devkit import cli as okf


class LintTestCase(OkfTestCase):
    def findings(self) -> list[okf.Finding]:
        self.reset_caches()
        return okf.run_lint(self.bundle())

    def rules(self) -> set[str]:
        return {f.rule for f in self.findings()}

    def assertRule(self, rule: str, level: str | None = None, contains: str | None = None):
        hits = [f for f in self.findings() if f.rule == rule]
        self.assertTrue(hits, f"{rule} が検出されていません: {[str(f) for f in self.findings()]}")
        if level:
            self.assertTrue(any(f.level == level for f in hits),
                            f"{rule} が {level} になっていません: {[str(f) for f in hits]}")
        if contains:
            self.assertTrue(any(contains in f.message for f in hits),
                            f"{rule} のメッセージに {contains!r} が含まれません: {[str(f) for f in hits]}")

    def assertNoRule(self, rule: str):
        hits = [f for f in self.findings() if f.rule == rule]
        self.assertFalse(hits, f"{rule} が誤検出されています: {[str(f) for f in hits]}")


class L4StatusTest(LintTestCase):
    def test_non_string_status_is_error(self):
        for value in ("true", "[]", "123", "{}"):
            with self.subTest(status=value):
                self.write("docs/a.md", doc_text(title="A", layer="shared", status=value,
                                                 code_globs=None))
                self.assertRule("L4", level="error")

    def test_valid_status_passes(self):
        self.write("docs/a.md", doc_text(title="A", layer="shared", status="draft", code_globs=None))
        self.assertNoRule("L4")


class L5LayerTest(LintTestCase):
    def test_non_string_layer_is_error(self):
        self.write("docs/a.md", doc_text(title="A", layer="123", code_globs=None))
        self.assertRule("L5", level="error")


class L7ReservedTest(LintTestCase):
    def setUp(self):
        super().setUp()
        self.write("docs/a.md", doc_text(title="A", layer="shared", code_globs=None))

    def test_malformed_index_frontmatter_is_error(self):
        """終端 `---` の無い index.md を素通りさせない。"""
        self.write("docs/client/index.md", "---\ntitle: x\n\n# client ドキュメント\n")
        self.assertRule("L7", level="error", contains="frontmatter")

    def test_index_with_frontmatter_is_error(self):
        self.write("docs/client/index.md", "---\ntitle: x\n---\n\n# client ドキュメント\n")
        self.assertRule("L7", level="error")

    def test_root_index_okf_version_is_allowed(self):
        okf.cmd_index(self.bundle(), okf.argparse.Namespace(write=True, check=False, quiet=True))
        self.assertNoRule("L7")

    def test_log_with_frontmatter_is_error(self):
        self.write("docs/client/log.md", "---\ntitle: x\n---\n\n# 変更履歴\n")
        self.assertRule("L7", level="error", contains="log.md")


class L8LogHeadingTest(LintTestCase):
    def setUp(self):
        super().setUp()
        self.write("docs/a.md", doc_text(title="A", layer="shared", code_globs=None))

    def test_impossible_date_is_rejected(self):
        self.write("docs/client/log.md", "# 変更履歴\n\n## 2026-99-99\n- **Update** x。\n")
        self.assertRule("L8", level="warn", contains="実在する日付")

    def test_duplicate_heading_is_reported(self):
        self.write("docs/client/log.md",
                   "# 変更履歴\n\n## 2026-08-16\n- a\n\n## 2026-08-16\n- b\n")
        self.assertRule("L8", contains="重複")

    def test_out_of_order_is_reported(self):
        self.write("docs/client/log.md",
                   "# 変更履歴\n\n## 2026-01-01\n- a\n\n## 2026-08-16\n- b\n")
        self.assertRule("L8", contains="新しい順")

    def test_valid_log_passes(self):
        self.write("docs/client/log.md",
                   "# 変更履歴\n\n## 2026-08-16\n- a\n\n## 2026-01-01\n- b\n")
        self.assertNoRule("L8")


class L10CodeGlobsTest(LintTestCase):
    def test_missing_code_globs_is_warned_for_code_derived_type(self):
        # Reference はコード由来の type なので code_globs が必須
        self.write("docs/a.md", doc_text(title="A", layer="shared", code_globs=None))
        self.assertRule("L10", level="warn", contains="`code_globs` がありません")

    def test_missing_code_globs_is_ok_for_convention(self):
        # Convention は code_globs 任意
        self.write("docs/a.md", doc_text(type_="Convention", title="A", layer="shared",
                                         code_globs=None))
        self.assertNoRule("L10")

    def test_missing_code_globs_is_ok_when_deprecated(self):
        # status: deprecated は必須要件から除外される
        self.write("docs/a.md", doc_text(title="A", layer="shared", status="deprecated",
                                         code_globs=None))
        self.assertNoRule("L10")

    def test_non_list_is_error(self):
        self.write("docs/a.md", doc_text(title="A", layer="shared", code_globs=None,
                                         extra="code_globs: not-a-list"))
        self.assertRule("L10", level="error", contains="リスト")

    def test_non_string_element_is_error(self):
        self.write("docs/a.md", doc_text(title="A", layer="shared",
                                         code_globs="  - id: only-id"))
        self.assertRule("L10", level="error", contains="文字列ではありません")

    def test_unmatched_glob_is_warned(self):
        self.write("docs/a.md", doc_text(title="A", layer="shared",
                                         code_globs="  - missing/*.ts"))
        self.assertRule("L10", level="warn", contains="マッチするファイルがありません")

    def test_valid_code_globs_pass(self):
        self.write("code/thing.ts", "x")
        self.write("docs/a.md", doc_text(title="A", layer="shared",
                                         code_globs="  - code/*.ts"))
        self.assertNoRule("L10")


class L14SourcesTest(LintTestCase):
    """`sources` は OKF 標準の provenance。欠如は問題としない。"""

    def test_missing_sources_is_not_warned(self):
        self.write("docs/a.md", doc_text(title="A", layer="shared"))
        self.assertNoRule("L14")

    def test_non_map_element_is_warned(self):
        self.write("docs/a.md", doc_text(title="A", layer="shared",
                                         sources="  - https://example.invalid/spec"))
        self.assertRule("L14", level="warn", contains="マップ")

    def test_missing_resource_is_warned(self):
        self.write("docs/a.md", doc_text(title="A", layer="shared", sources="  - id: only-id"))
        self.assertRule("L14", level="warn", contains="resource")

    def test_valid_sources_pass(self):
        self.write("docs/a.md", doc_text(title="A", layer="shared",
                                         sources="  - id: okf\n    resource: https://example.invalid/spec"))
        self.assertNoRule("L14")


class L11RelatedTest(LintTestCase):
    def test_outside_bundle_is_warned(self):
        self.write("README.md", "x")
        self.write("docs/a.md", doc_text(title="A", layer="shared", code_globs=None,
                                         extra="related:\n  - /../README.md"))
        self.assertRule("L11", contains="バンドル")

    def test_missing_target_is_warned(self):
        self.write("docs/a.md", doc_text(title="A", layer="shared", code_globs=None,
                                         extra="related:\n  - /nope.md"))
        self.assertRule("L11", contains="存在しません")

    def test_valid_related_passes(self):
        self.write("docs/b.md", doc_text(title="B", layer="shared", code_globs=None))
        self.write("docs/a.md", doc_text(title="A", layer="shared", code_globs=None,
                                         extra="related:\n  - /b.md"))
        self.assertNoRule("L11")


class L12BacklogTest(LintTestCase):
    def test_invalid_done_at_is_error(self):
        self.write("docs/backlog/B-0001-x.md",
                   doc_text(type_="Backlog Item", title="X", layer="shared", code_globs=None,
                            extra="state: done\ndone_at: invalid-2026-99-99-text"))
        self.assertRule("L12", level="error", contains="done_at")

    def test_impossible_done_at_is_error(self):
        self.write("docs/backlog/B-0001-x.md",
                   doc_text(type_="Backlog Item", title="X", layer="shared", code_globs=None,
                            extra='state: done\ndone_at: "2026-02-31"'))
        self.assertRule("L12", level="error")

    def test_valid_done_at_passes(self):
        self.write("docs/backlog/B-0001-x.md",
                   doc_text(type_="Backlog Item", title="X", layer="shared", code_globs=None,
                            extra="state: done\ndone_at: 2026-08-16"))
        self.assertNoRule("L12")


class L6ActorTest(LintTestCase):
    def test_bad_verified_actor_is_warned(self):
        self.write("docs/a.md", doc_text(title="A", layer="shared", code_globs=None,
                                         extra="verified:\n  - by: rintaro\n    at: 2026-08-16T00:00:00Z"))
        self.assertRule("L6", level="warn", contains="verified[1].by")

    def test_verified_non_list_is_warned(self):
        self.write("docs/a.md", doc_text(title="A", layer="shared", code_globs=None,
                                         extra="verified: true"))
        self.assertRule("L6", contains="リスト")

    def test_trust_level(self):
        self.write("docs/a.md", doc_text(title="A", layer="shared", code_globs=None,
                                         extra="verified:\n  - by: human:rintaro\n    at: 2026-08-16T00:00:00Z"))
        doc = self.bundle().docs()[0]
        self.assertEqual("human-reviewed", okf.trust_level(doc))

    def test_trust_level_machine(self):
        self.write("docs/a.md", doc_text(title="A", layer="shared", code_globs=None,
                                         extra="verified:\n  - by: process:ci\n    at: 2026-08-16T00:00:00Z"))
        doc = self.bundle().docs()[0]
        self.assertEqual("machine-confirmed", okf.trust_level(doc))


class L9DescriptionTest(LintTestCase):
    def test_multiple_sentences_english(self):
        self.write("docs/a.md", doc_text(title="A", layer="shared", code_globs=None,
                                         description="First one. Second one."))
        self.assertRule("L9", contains="一文")

    def test_version_number_is_not_a_sentence_break(self):
        self.write("docs/a.md", doc_text(title="A", layer="shared", code_globs=None,
                                         description="React 19.1 と Vite 7.0 の構成。"))
        self.assertNoRule("L9")


class GlobTest(unittest.TestCase):
    def test_character_class(self):
        self.assertTrue(okf.path_matches("a/b1.php", "a/b[0-9].php"))
        self.assertFalse(okf.path_matches("a/bx.php", "a/b[0-9].php"))
        self.assertTrue(okf.path_matches("a/bx.php", "a/b[!0-9].php"))

    def test_doublestar(self):
        self.assertTrue(okf.path_matches("a/b/c/d.ts", "a/**/*.ts"))
        self.assertTrue(okf.path_matches("a/d.ts", "a/**/*.ts"))
        self.assertFalse(okf.path_matches("z/d.ts", "a/**/*.ts"))


class ResolveResourceGlobTest(OkfTestCase):
    def test_resolve_uses_same_glob_semantics(self):
        self.write("code/a1.ts", "x")
        self.write("code/ab.ts", "x")
        self.assertEqual(["code/a1.ts"], okf.resolve_resource("code/a[0-9].ts"))
        self.assertEqual(["code/ab.ts"], okf.resolve_resource("code/a[!0-9].ts"))


if __name__ == "__main__":
    unittest.main()
