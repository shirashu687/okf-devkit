"""YAML: PyYAML と内蔵パーサの同値性、および曖昧な構文の明示的な拒否。"""

from __future__ import annotations

import unittest

from helpers import OkfTestCase, doc_text
from okf_devkit import cli as okf


EQUIVALENT_SNIPPETS = [
    "type: Reference\ntitle: サーバー API\n",
    "status: stable\nlayer: server\n",
    "tags: [server, api, php]\n",
    "generated:\n  by: claude-code/opus-5\n  at: 2026-08-16T10:00:00Z\n",
    "generated:\n  by: human:rintaro\n  at: 2026-08-16T10:00:00+09:00\n",
    "verified:\n  - by: human:rintaro\n    at: 2026-08-16T12:00:00Z\n",
    "sources:\n  - id: server-php\n    resource: app/server/*.php\n",
    "related:\n  - /server/database.md\n  - ./other.md\n",
    "created: 2026-08-16\ndone_at: null\n",
    "cost: false\nn: 12\nf: 1.5\n",
    "resource: https://example.com/a/b?c=1\n",
    "note: value  # trailing comment\n",
    'quoted: "plain text"\nsingle: \'text\'\n',
    "empty:\nlist: []\nmap: {}\n",
    "rules:\n  - { glob: \"a/**\", layer: client }\n  - { glob: \"b/**\", layer: server }\n",
    "flag: yes\nother: no\n",
    "deep:\n  a:\n    b: 1\n  c: [x, y]\n",
]

REJECTED_BY_MINI = [
    ("plain scalar 内の `: `", "title: foo: bar\n"),
    ("末尾のコロン", "title: foo:\n"),
    ("引用符内のエスケープ", 'title: "a\\nb"\n'),
    ("単一引用符のエスケープ", "title: 'it''s'\n"),
    ("アンカー", "title: &anchor value\n"),
    ("エイリアス", "title: *anchor\n"),
    ("タグ", "title: !!str value\n"),
    ("ブロックスカラー", "title: |\n  multi\n  line\n"),
    ("フロー内のアンカー", "m: {k: &a v}\n"),
    ("キーの重複", "title: a\ntitle: b\n"),
]


class YamlEquivalenceTest(unittest.TestCase):
    """PyYAML があるときと無いときで結果が同じであること。"""

    def parse_both(self, text: str):
        original = okf._pyyaml
        try:
            okf._pyyaml = original
            with_pyyaml = okf.parse_yaml(text, "<test>")
            okf._pyyaml = None
            without = okf.parse_yaml(text, "<test>")
        finally:
            okf._pyyaml = original
        return with_pyyaml, without

    @unittest.skipIf(okf._pyyaml is None, "PyYAML が無い環境では比較できない")
    def test_equivalent_snippets(self):
        for snippet in EQUIVALENT_SNIPPETS:
            with self.subTest(snippet=snippet):
                a, b = self.parse_both(snippet)
                self.assertEqual(a, b)

    def test_mini_rejects_ambiguous_syntax(self):
        original = okf._pyyaml
        okf._pyyaml = None
        try:
            for label, snippet in REJECTED_BY_MINI:
                with self.subTest(case=label):
                    with self.assertRaises(okf.OkfError, msg=f"{label} は拒否されるべき"):
                        okf.parse_yaml(snippet, "<test>")
        finally:
            okf._pyyaml = original

    def test_mini_timestamp_normalization(self):
        original = okf._pyyaml
        okf._pyyaml = None
        try:
            data = okf.parse_yaml("at: 2026-08-16T10:00:00+09:00\nd: 2026-08-16\n", "<test>")
        finally:
            okf._pyyaml = original
        self.assertEqual("2026-08-16T01:00:00Z", data["at"])
        self.assertEqual("2026-08-16", data["d"])

    def test_mini_yaml_11_booleans(self):
        original = okf._pyyaml
        okf._pyyaml = None
        try:
            data = okf.parse_yaml("a: yes\nb: off\nc: TRUE\n", "<test>")
        finally:
            okf._pyyaml = original
        self.assertEqual({"a": True, "b": False, "c": True}, data)


class LintParserEquivalenceTest(OkfTestCase):
    """PyYAML の有無で lint の結果（findings）が一致すること。"""

    def build_docs(self) -> None:
        self.write("docs/ok.md", doc_text(title="OK", layer="shared", code_globs=None))
        self.write("docs/bad-type.md", doc_text(type_="Unknown", title="Bad", layer="shared",
                                                code_globs=None))
        self.write("docs/bad-layer.md", doc_text(title="Bad2", layer="nope", code_globs=None))
        self.write("docs/backlog/B-0001-x.md",
                   doc_text(type_="Backlog Item", title="B", layer="shared", code_globs=None,
                            extra="state: done\ndone_at: invalid-2026-99-99-text"))
        self.write("docs/client/c.md",
                   doc_text(title="C", sources="  - id: s\n    resource: missing/**/*.ts"))

    def findings_with(self, pyyaml_enabled: bool) -> list[str]:
        okf._pyyaml = self._orig_pyyaml if pyyaml_enabled else None
        self.reset_caches()
        return [str(f) for f in okf.run_lint(self.bundle())]

    @unittest.skipIf(okf._pyyaml is None, "PyYAML が無い環境では比較できない")
    def test_same_findings(self):
        self.build_docs()
        with_pyyaml = self.findings_with(True)
        without = self.findings_with(False)
        self.assertEqual(with_pyyaml, without)
        self.assertTrue(with_pyyaml, "検出すべき違反があるはず")


class YamlScalarTest(unittest.TestCase):
    """new コマンドが埋め込む値のシリアライズ。"""

    def test_quotes_ambiguous_values(self):
        for value in ["foo: bar", "#hash", "yes", "true", "123", "2026-08-16", " padded ",
                      '"quoted"', "a # b", "*star", "&amp", "[bracket]"]:
            with self.subTest(value=value):
                text = f"title: {okf.yaml_scalar(value)}\n"
                self.assertEqual({"title": value}, okf.parse_yaml(text, "<test>"))

    def test_plain_values_stay_plain(self):
        self.assertEqual("サーバー API リファレンス", okf.yaml_scalar("サーバー API リファレンス"))

    def test_newline_is_rejected(self):
        with self.assertRaises(okf.OkfError):
            okf.yaml_scalar("a\nb")


if __name__ == "__main__":
    unittest.main()
