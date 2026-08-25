"""log コマンド: 冪等性 / baseline / ハッシュ無し既存エントリの保護。"""

from __future__ import annotations

import io
import contextlib
import unittest

from helpers import OkfTestCase, ns
from okf_devkit import cli as okf


CLIENT_FILE = "app/client/src/app/x.tsx"
SERVER_FILE = "app/server/api.php"


def run(fn, *args) -> str:
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        fn(*args)
    return buf.getvalue()


class LogTest(OkfTestCase):
    def setUp(self):
        super().setUp()
        self.git_init()
        self.write("docs/.keep", "")
        self.first = self.commit("初期化", {CLIENT_FILE: "a\n"})
        self.second = self.commit("マイページ機能の追加", {CLIENT_FILE: "b\n"})
        self.third = self.commit("API のバグを修正", {SERVER_FILE: "<?php\n"})

    def write_args(self, **kw):
        base = dict(write=True, range=None, layer=None, dry_run=False)
        base.update(kw)
        return ns(**base)

    def test_writes_and_is_idempotent(self):
        bundle = self.bundle()
        run(okf.cmd_log, bundle, self.write_args())
        first = self.read("docs/client/log.md")
        self.assertIn("**Creation** マイページ機能の追加。", first)
        self.assertIn(self.second[:7], first)

        run(okf.cmd_log, self.bundle(), self.write_args())
        self.assertEqual(first, self.read("docs/client/log.md"), "2 回目で内容が変わってはいけない")

    def test_layer_routing(self):
        run(okf.cmd_log, self.bundle(), self.write_args())
        self.assertIn("API のバグを修正。", self.read("docs/server/log.md"))
        self.assertNotIn("API のバグを修正", self.read("docs/client/log.md"))

    def test_baseline_excludes_older_commits(self):
        bundle = self.bundle(baseline=self.second)
        run(okf.cmd_log, bundle, self.write_args())
        # second 以前（= 初期化 / マイページ）は対象外
        self.assertFalse((self.repo / "docs/client/log.md").exists())
        self.assertIn("API のバグを修正。", self.read("docs/server/log.md"))

    def test_baseline_head_means_nothing_to_add(self):
        bundle = self.bundle(baseline=self.third)
        out = run(okf.cmd_log, bundle, self.write_args())
        self.assertIn("追記すべき変更はありません", out)
        self.assertFalse((self.repo / "docs/client/log.md").exists())

    def test_unknown_baseline_is_an_error(self):
        bundle = self.bundle(baseline="0" * 40)
        with self.assertRaises(okf.OkfError):
            okf.cmd_log(bundle, self.write_args())

    def test_refuses_write_when_hashless_entries_and_no_baseline(self):
        """移行済み（ハッシュ無し）エントリがある状態で baseline 未設定なら書かない。"""
        legacy = (
            "# 変更履歴 — client\n\n"
            "## 2026-06-11\n"
            "- **Creation** マイページを追加した。\n"
        )
        self.write("docs/client/log.md", legacy)
        with self.assertRaises(okf.OkfError) as cm:
            okf.cmd_log(self.bundle(), self.write_args())
        self.assertIn("log.baseline", str(cm.exception))
        self.assertEqual(legacy, self.read("docs/client/log.md"), "拒否時は書き換えない")

    def test_dry_run_is_allowed_even_with_hashless_entries(self):
        self.write("docs/client/log.md",
                   "# 変更履歴 — client\n\n## 2026-06-11\n- **Creation** マイページを追加した。\n")
        out = run(okf.cmd_log, self.bundle(), self.write_args(write=False, dry_run=True))
        self.assertIn("dry-run", out)

    def test_baseline_allows_write_with_hashless_entries(self):
        self.write("docs/client/log.md",
                   "# 変更履歴 — client\n\n## 2026-06-11\n- **Creation** マイページを追加した。\n")
        run(okf.cmd_log, self.bundle(baseline=self.second), self.write_args())
        text = self.read("docs/client/log.md")
        self.assertEqual(1, text.count("マイページを追加した。"), "移行済みエントリを重複させない")

    def test_shared_layer_is_not_automatic(self):
        self.commit("ルート直下の変更", {"README.md": "x\n"})
        run(okf.cmd_log, self.bundle(), self.write_args())
        self.assertFalse((self.repo / "docs/log.md").exists(),
                         "shared は既定では自動追記しない（CONVENTIONS.md §7）")

    def test_shared_layer_writes_to_root_log_when_explicit(self):
        self.commit("ルート直下の変更", {"README.md": "x\n"})
        run(okf.cmd_log, self.bundle(), self.write_args(layer="shared"))
        self.assertTrue((self.repo / "docs/log.md").exists())
        self.assertFalse((self.repo / "docs/shared/log.md").exists())

    def test_full_sha_prefix_matching(self):
        """記録済み判定は full SHA を正とする。"""
        self.write("docs/client/log.md",
                   f"# 変更履歴 — client\n\n## 2026-01-01\n- **Update** x。(`{self.second}`)\n")
        run(okf.cmd_log, self.bundle(baseline=self.first), self.write_args())
        text = self.read("docs/client/log.md")
        self.assertEqual(1, text.count(self.second[:7]), "full SHA で記録済みなら再追記しない")

    def test_range_option_still_works(self):
        run(okf.cmd_log, self.bundle(), self.write_args(range=f"{self.first}..HEAD"))
        text = self.read("docs/client/log.md")
        self.assertIn("マイページ機能の追加。", text)
        self.assertNotIn("初期化", text)


class NoCommitTest(OkfTestCase):
    def test_log_on_empty_repo(self):
        self.git_init()
        self.write("docs/.keep", "")
        out = run(okf.cmd_log, self.bundle(), ns(write=True, range=None, layer=None, dry_run=False))
        self.assertIn("コミットがまだありません", out)


class KindRuleTest(OkfTestCase):
    def test_add_needs_word_boundary(self):
        bundle = self.bundle()
        self.assertEqual("**Update**", okf.kind_of(bundle, "fix padding on the header"))
        self.assertEqual("**Creation**", okf.kind_of(bundle, "add song master screen"))


if __name__ == "__main__":
    unittest.main()
