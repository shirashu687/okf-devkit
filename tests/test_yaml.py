"""YAML: PyYAML と内蔵パーサの同値性、および曖昧な構文の明示的な拒否。"""

from __future__ import annotations

import unittest
from unittest.mock import patch

from helpers import OkfTestCase, doc_text
from okf_devkit import cli as okf, yamlio


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
        original = yamlio._pyyaml
        try:
            yamlio._pyyaml = original
            with_pyyaml = yamlio.parse_yaml(text, "<test>")
            yamlio._pyyaml = None
            without = yamlio.parse_yaml(text, "<test>")
        finally:
            yamlio._pyyaml = original
        return with_pyyaml, without

    @unittest.skipIf(yamlio._pyyaml is None, "PyYAML が無い環境では比較できない")
    def test_equivalent_snippets(self):
        for snippet in EQUIVALENT_SNIPPETS:
            with self.subTest(snippet=snippet):
                a, b = self.parse_both(snippet)
                self.assertEqual(a, b)

    def test_mini_rejects_ambiguous_syntax(self):
        original = yamlio._pyyaml
        yamlio._pyyaml = None
        try:
            for label, snippet in REJECTED_BY_MINI:
                with self.subTest(case=label):
                    with self.assertRaises(okf.OkfError, msg=f"{label} は拒否されるべき"):
                        yamlio.parse_yaml(snippet, "<test>")
        finally:
            yamlio._pyyaml = original

    def test_mini_timestamp_normalization(self):
        original = yamlio._pyyaml
        yamlio._pyyaml = None
        try:
            data = yamlio.parse_yaml("at: 2026-08-16T10:00:00+09:00\nd: 2026-08-16\n", "<test>")
        finally:
            yamlio._pyyaml = original
        self.assertEqual("2026-08-16T01:00:00Z", data["at"])
        self.assertEqual("2026-08-16", data["d"])

    def test_mini_yaml_11_booleans(self):
        original = yamlio._pyyaml
        yamlio._pyyaml = None
        try:
            data = yamlio.parse_yaml("a: yes\nb: off\nc: TRUE\n", "<test>")
        finally:
            yamlio._pyyaml = original
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
        yamlio._pyyaml = self._orig_pyyaml if pyyaml_enabled else None
        self.reset_caches()
        return [str(f) for f in okf.run_lint(self.bundle())]

    @unittest.skipIf(yamlio._pyyaml is None, "PyYAML が無い環境では比較できない")
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
                self.assertEqual({"title": value}, yamlio.parse_yaml(text, "<test>"))

    def test_plain_values_stay_plain(self):
        self.assertEqual("サーバー API リファレンス", okf.yaml_scalar("サーバー API リファレンス"))

    def test_newline_is_rejected(self):
        with self.assertRaises(okf.OkfError):
            okf.yaml_scalar("a\nb")


class YamlBackendOwnerTest(unittest.TestCase):
    def test_default_backend_reads_current_owner_and_explicit_none_forces_mini(self):
        backend = yamlio._pyyaml
        if backend is None:
            self.skipTest("PyYAML unavailable for the enabled-backend comparison")
        with patch.object(backend, "safe_load", wraps=backend.safe_load) as loaded:
            self.assertEqual({"key": "value"}, yamlio.parse_yaml("key: value"))
        loaded.assert_called_once_with("key: value")
        mini = yamlio._MiniYaml
        with patch.object(yamlio, "_MiniYaml", wraps=mini) as observed, patch.object(backend, "safe_load", side_effect=AssertionError("explicit None must not use PyYAML")):
            self.assertEqual({"key": "value"}, yamlio.parse_yaml("key: value", "explicit-source", backend=None))
        observed.assert_called_once_with("key: value", "explicit-source")

    def test_forced_owner_none_uses_actual_mini_constructor(self):
        mini = yamlio._MiniYaml
        with patch.object(yamlio, "_pyyaml", None), patch.object(yamlio, "_MiniYaml", wraps=mini) as observed:
            self.assertEqual({"flag": True}, yamlio.parse_yaml("flag: yes", "owner-source"))
            with self.assertRaises(okf.YamlSubsetError):
                yamlio.parse_yaml("key: &anchor value", "rejected-source")
        self.assertEqual(["owner-source", "rejected-source"], [call.args[1] for call in observed.call_args_list])

    def test_legacy_cli_adapter_preserves_explicit_backend_override_and_exception_identity(self):
        self.assertIs(okf.YamlSubsetError, yamlio.YamlSubsetError)
        self.assertIs(okf.OkfError, yamlio.OkfError)
        self.assertIs(okf._MiniYaml, yamlio._MiniYaml)
        self.assertIs(okf.yaml_scalar, yamlio.yaml_scalar)
        mini = yamlio._MiniYaml
        with patch.object(okf, "_pyyaml", None), patch.object(yamlio, "_MiniYaml", wraps=mini) as observed:
            with self.assertRaises(okf.YamlSubsetError):
                okf.parse_yaml("key: &anchor value", "legacy-source")
        observed.assert_called_once_with("key: &anchor value", "legacy-source")

    def test_explicit_backend_is_used_even_when_owner_is_none(self):
        backend = yamlio._pyyaml
        if backend is None:
            self.skipTest("PyYAML unavailable for explicit-backend test")
        with patch.object(yamlio, "_pyyaml", None), patch.object(backend, "safe_load", wraps=backend.safe_load) as loaded:
            self.assertEqual({"key": "value"}, yamlio.parse_yaml("key: value", backend=backend))
        loaded.assert_called_once_with("key: value")


if __name__ == "__main__":
    unittest.main()
