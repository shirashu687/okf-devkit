"""Explicit-root frontmatter ownership and legacy Doc constructor contracts."""
from pathlib import Path
from unittest.mock import patch

from helpers import OkfTestCase, doc_text
from okf_devkit import cli, doc, yamlio


class DocTests(OkfTestCase):
    def test_explicit_root_paths_and_frontmatter_do_not_follow_cli_root(self):
        path = self.write("nested/knowledge/item.md", doc_text(title="Item", layer="shared", body="# Item\n"))
        with patch.object(cli, "REPO_ROOT", self.repo / "unrelated"):
            item = doc.Doc(path, path.parent, repo_root=self.repo)
        self.assertEqual(item.repo_rel, "nested/knowledge/item.md")
        self.assertEqual(item.bundle_rel, "/item.md")
        self.assertEqual(item.title, "Item")
        self.assertEqual(item.code_globs(), ["src/a.ts"])
        self.assertTrue(item.requires_code_globs())
        self.assertIsNone(item.fm_error)
        self.assertEqual(item.h1, "Item")

    def test_canonical_constructor_requires_explicit_root(self):
        path = self.write("docs/item.md", "# Item\n")
        with self.assertRaises(TypeError):
            doc.Doc(path, self.docs)
        item = cli.Doc(path, self.docs)
        self.assertIsInstance(item, doc.Doc)
        self.assertEqual(item.repo_rel, "docs/item.md")

    def test_unclosed_and_nonmapping_frontmatter_remain_distinct(self):
        open_path = self.write("docs/open.md", "---\ntitle: Open\n")
        opened = doc.Doc(open_path, self.docs, repo_root=self.repo)
        self.assertTrue(opened.fm_opened)
        self.assertFalse(opened.has_fm)
        self.assertIsNotNone(opened.fm_error)
        array_path = self.write("docs/array.md", "---\n- one\n---\n# Array\n")
        array = doc.Doc(array_path, self.docs, repo_root=self.repo)
        self.assertTrue(array.has_fm)
        self.assertEqual(array.fm, {})
        self.assertIsNotNone(array.fm_error)

    def test_actual_yaml_owner_handles_document_fallback(self):
        path = self.write("docs/item.md", doc_text(title="Fallback", layer="shared"))
        with patch.object(yamlio, "_pyyaml", None), patch.object(yamlio, "_MiniYaml", wraps=yamlio._MiniYaml) as parser:
            item = doc.Doc(path, self.docs, repo_root=self.repo)
        self.assertEqual(item.title, "Fallback")
        parser.assert_called_once()
        self.assertEqual(parser.call_args.args[1], "docs/item.md")

    def test_deprecated_required_type_and_provenance_validation(self):
        path = self.write("docs/item.md", doc_text(status="deprecated", code_globs=None, sources="  - resource: src/a.ts"))
        item = doc.Doc(path, self.docs, repo_root=self.repo)
        self.assertFalse(item.requires_code_globs())
        self.assertEqual(item.source_problems(), [])
        item.fm["sources"] = ["src/a.ts"]
        self.assertTrue(item.source_problems())
        item.fm["code_globs"] = [False, ""]
        self.assertEqual(len(item.code_globs_problems()), 2)

