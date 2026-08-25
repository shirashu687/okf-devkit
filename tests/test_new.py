"""new コマンド: YAML の安全性 / パス検証 / 連番採番。"""

from __future__ import annotations

import contextlib
import io
import unittest

from helpers import OkfTestCase, ns
from okf_devkit import cli as okf


def quiet(fn, *args):
    with contextlib.redirect_stdout(io.StringIO()):
        return fn(*args)


class NewDocTest(OkfTestCase):
    def setUp(self):
        super().setUp()
        self.make_templates()

    def doc_args(self, **kw):
        base = dict(kind="doc", layer="server", type="Reference", title="T", dir=None, slug=None)
        base.update(kw)
        return ns(**base)

    def test_title_with_colon_stays_valid_yaml(self):
        quiet(okf.cmd_new, self.bundle(), self.doc_args(title="API: 一覧", slug="api-list"))
        doc = okf.Doc(self.repo / "docs/server/api-list.md", self.docs)
        self.assertIsNone(doc.fm_error)
        self.assertEqual("API: 一覧", doc.fm["title"])

    def test_title_with_hash_and_quotes(self):
        for title, slug in (("#1 の対応", "hash-title"), ('He said "hi"', "quote-title"),
                            ("yes", "bool-title"), ("2026-08-16", "date-title")):
            with self.subTest(title=title):
                quiet(okf.cmd_new, self.bundle(), self.doc_args(title=title, slug=slug))
                doc = okf.Doc(self.repo / f"docs/server/{slug}.md", self.docs)
                self.assertIsNone(doc.fm_error, f"{title!r} で frontmatter が壊れた")
                self.assertEqual(title, doc.fm["title"])

    def test_newline_in_title_is_rejected(self):
        with self.assertRaises(okf.OkfError):
            okf.cmd_new(self.bundle(), self.doc_args(title="a\nb", slug="x"))

    def test_slug_traversal_is_rejected(self):
        for bad in ("../evil", "/abs", "..", "Upper", "with space", "a/b"):
            with self.subTest(slug=bad):
                with self.assertRaises(okf.OkfError):
                    okf.cmd_new(self.bundle(), self.doc_args(slug=bad))

    def test_dir_traversal_is_rejected(self):
        for bad in ("../../outside", "/etc", "a/../../b", "C:/tmp"):
            with self.subTest(dir=bad):
                with self.assertRaises(okf.OkfError):
                    okf.cmd_new(self.bundle(), self.doc_args(dir=bad, slug="ok"))
        self.assertFalse((self.repo / "outside").exists())

    def test_unknown_layer_and_type_are_rejected(self):
        with self.assertRaises(okf.OkfError):
            okf.cmd_new(self.bundle(), self.doc_args(layer="nope", slug="x"))
        with self.assertRaises(okf.OkfError):
            okf.cmd_new(self.bundle(), self.doc_args(type="Nope", slug="x"))

    def test_valid_subdir(self):
        quiet(okf.cmd_new, self.bundle(), self.doc_args(dir="guides", slug="how", type="How-To"))
        self.assertTrue((self.repo / "docs/server/guides/how.md").exists())

    def test_adr_gets_sequential_number(self):
        args = dict(kind="doc", layer="shared", type="Decision Record", dir="decisions")
        quiet(okf.cmd_new, self.bundle(), ns(**args, title="最初の判断", slug="first"))
        quiet(okf.cmd_new, self.bundle(), ns(**args, title="次の判断", slug="second"))
        names = sorted(p.name for p in (self.repo / "docs/project/decisions").iterdir())
        self.assertEqual(["0001-first.md", "0002-second.md"], names)


class NewBacklogTest(OkfTestCase):
    def setUp(self):
        super().setUp()
        self.make_templates()

    def backlog_args(self, **kw):
        base = dict(kind="backlog", layer="shared", title="やること", priority="medium",
                    effort="M", slug=None)
        base.update(kw)
        return ns(**base)

    def test_sequential_ids(self):
        quiet(okf.cmd_new, self.bundle(), self.backlog_args(slug="one"))
        quiet(okf.cmd_new, self.bundle(), self.backlog_args(slug="two"))
        names = sorted(p.name for p in (self.repo / "docs/backlog").iterdir())
        self.assertEqual(["B-0001-one.md", "B-0002-two.md"], names)

    def test_japanese_title_without_slug(self):
        quiet(okf.cmd_new, self.bundle(), self.backlog_args())
        self.assertTrue((self.repo / "docs/backlog/B-0001.md").exists())
        doc = okf.Doc(self.repo / "docs/backlog/B-0001.md", self.docs)
        self.assertEqual("やること", doc.fm["title"])
        self.assertEqual(["shared"], doc.fm["tags"])

    def test_invalid_priority_and_effort(self):
        with self.assertRaises(okf.OkfError):
            okf.cmd_new(self.bundle(), self.backlog_args(priority="urgent"))
        with self.assertRaises(okf.OkfError):
            okf.cmd_new(self.bundle(), self.backlog_args(effort="XXL"))

    def test_generated_output_passes_lint(self):
        self.write("code/a.ts", "x")
        quiet(okf.cmd_new, self.bundle(), self.backlog_args(slug="one"))
        # sources のプレースホルダを実在パスに直せば lint error にならない
        path = self.repo / "docs/backlog/B-0001-one.md"
        path.write_text(path.read_text(encoding="utf-8"), encoding="utf-8", newline="\n")
        self.reset_caches()
        errors = [f for f in okf.run_lint(self.bundle())
                  if f.level == "error" and f.rule != "L13"]
        self.assertEqual([], [str(f) for f in errors])


if __name__ == "__main__":
    unittest.main()
