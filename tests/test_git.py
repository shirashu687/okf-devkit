"""git 連携: rename / 非 ASCII パス / shallow / detached / コミット 0 件。"""

from __future__ import annotations

import unittest

from helpers import OkfTestCase, doc_text, ns
from okf_devkit import cli as okf


JP_PATH = "app/client/src/app/日本語ファイル.tsx"


class GitPathParsingTest(OkfTestCase):
    def setUp(self):
        super().setUp()
        self.git_init()
        self.write("docs/.keep", "")

    def test_non_ascii_path_is_parsed(self):
        self.commit("日本語ファイルを追加", {JP_PATH: "x\n"})
        commits = okf.collect_commits(None)
        self.assertIn(JP_PATH, commits[0].paths)
        self.assertEqual("client", okf.layer_of(self.bundle(), commits[0].paths[0]))

    def test_rename_keeps_both_paths(self):
        old = "app/client/src/app/old.tsx"
        new = "app/client/src/app/new.tsx"
        self.commit("初期", {old: "content\n" * 20})
        self.git("mv", old, new)
        self.git("commit", "-m", "ファイル名を変更")
        self.reset_caches()
        commits = okf.collect_commits(None)
        self.assertIn(new, commits[0].paths)
        self.assertIn(old, commits[0].paths, "rename の旧パスも保持すること")

    def test_worktree_rename_is_reported_by_affected(self):
        old = "app/client/src/app/old.tsx"
        new = "app/client/src/app/new.tsx"
        self.commit("初期", {old: "content\n" * 20})
        self.git("mv", old, new)
        self.reset_caches()
        paths = okf.changed_paths("main")
        self.assertIn(new, paths)
        self.assertIn(old, paths)

    def test_untracked_non_ascii_is_reported(self):
        self.commit("初期", {"a.txt": "x\n"})
        self.write(JP_PATH, "x\n")
        self.reset_caches()
        self.assertIn(JP_PATH, okf.changed_paths("main"))


class ShallowTest(OkfTestCase):
    def test_shallow_detection_and_warning(self):
        self.git_init()
        self.write("docs/.keep", "")
        sha = self.commit("初期", {"app/client/a.tsx": "x\n"})
        self.assertFalse(okf.is_shallow())

        (self.repo / ".git" / "shallow").write_text(sha + "\n", encoding="utf-8")
        self.reset_caches()
        self.assertTrue(okf.is_shallow())

        import io
        import contextlib
        err = io.StringIO()
        with contextlib.redirect_stderr(err), contextlib.redirect_stdout(io.StringIO()):
            okf.cmd_log(self.bundle(baseline=sha),
                        ns(write=False, range=None, layer=None, dry_run=True))
        self.assertIn("shallow", err.getvalue())


class BaseResolutionTest(OkfTestCase):
    def setUp(self):
        super().setUp()
        self.git_init()
        self.write("docs/.keep", "")
        self.sha = self.commit("初期", {"app/client/a.tsx": "x\n"})

    def test_detached_head_with_branch_present(self):
        self.git("checkout", "--detach", self.sha)
        self.reset_caches()
        self.assertEqual("main", okf.resolve_ref("main"))
        self.assertIsInstance(okf.changed_paths("main"), list)

    def test_missing_base_raises_clear_error(self):
        self.reset_caches()
        with self.assertRaises(okf.OkfError) as cm:
            okf.changed_paths("no-such-branch")
        self.assertIn("no-such-branch", str(cm.exception))

    def test_origin_fallback(self):
        self.git("update-ref", "refs/remotes/origin/develop", self.sha)
        self.reset_caches()
        self.assertEqual("origin/develop", okf.resolve_ref("develop"))

    def test_detached_head_without_local_branch(self):
        self.git("update-ref", "refs/remotes/origin/main", self.sha)
        self.git("checkout", "--detach", self.sha)
        self.git("branch", "-D", "main")
        self.reset_caches()
        self.assertEqual("origin/main", okf.resolve_ref("main"))
        self.assertIsInstance(okf.changed_paths("main"), list)


class NoCommitsTest(OkfTestCase):
    def setUp(self):
        super().setUp()
        self.git_init()
        self.write("docs/.keep", "")

    def test_has_commits_false(self):
        self.assertFalse(okf.has_commits())

    def test_changed_paths_uses_worktree_only(self):
        self.write("app/client/a.tsx", "x\n")
        self.reset_caches()
        paths = okf.changed_paths("main")
        self.assertIn("app/client/a.tsx", paths)


class PathCommitTimeTest(OkfTestCase):
    def test_map_covers_more_than_200_paths(self):
        """201 件以上でも取りこぼさない（旧実装は先頭 200 件で打ち切っていた）。"""
        self.git_init()
        self.write("docs/.keep", "")
        files = {f"code/f{i:03d}.ts": "x\n" for i in range(210)}
        self.commit("大量追加", files)
        mapping = okf.path_commit_times()
        for name in files:
            self.assertIn(name, mapping)
        self.assertIsNotNone(okf.last_commit_time(sorted(files)))


class StaleSameDayTest(OkfTestCase):
    def test_same_day_update_is_detected(self):
        """generated.at が時刻付きなら、同日の後続コミットも outdated になる。"""
        self.git_init()
        self.write("docs/.keep", "")
        self.commit("コード追加", {"code/a.ts": "x\n"})
        stamp = okf.path_commit_times()["code/a.ts"]
        dt, _ = okf.parse_datetime(stamp)
        dt = dt.astimezone(okf._dt.timezone.utc)
        earlier = (dt - okf._dt.timedelta(minutes=5)).strftime("%Y-%m-%dT%H:%M:%SZ")

        self.write("docs/a.md",
                   doc_text(title="A", layer="shared", code_globs="  - code/a.ts")
                   .replace("at: 2026-01-01T00:00:00Z", f"at: {earlier}"))
        self.reset_caches()
        kinds = {r["kind"] for r in okf.run_stale(self.bundle())}
        self.assertIn("outdated", kinds)

    def test_date_only_generated_at_does_not_false_positive(self):
        self.git_init()
        self.write("docs/.keep", "")
        self.commit("コード追加", {"code/a.ts": "x\n"})
        stamp = okf.path_commit_times()["code/a.ts"]
        same_day = stamp[:10]
        self.write("docs/a.md",
                   doc_text(title="A", layer="shared", code_globs="  - code/a.ts")
                   .replace("at: 2026-01-01T00:00:00Z", f"at: {same_day}"))
        self.reset_caches()
        kinds = {r["kind"] for r in okf.run_stale(self.bundle())}
        self.assertNotIn("outdated", kinds)


class PorcelainParseTest(unittest.TestCase):
    def test_rename_record(self):
        raw = "R  new.txt\0old.txt\0 M other.txt\0?? 日本語.txt\0"
        self.assertEqual(["new.txt", "old.txt", "other.txt", "日本語.txt"],
                         okf.parse_porcelain_z(raw))


if __name__ == "__main__":
    unittest.main()
