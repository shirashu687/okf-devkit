"""Explicit-root Git ownership and legacy adapter regression contracts."""
from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path
from unittest.mock import patch

from helpers import OkfTestCase
from okf_devkit import cli, gitutil


class GitUtilTest(OkfTestCase):
    def test_canonical_cache_switches_actual_repositories_without_cli_root(self):
        self.git_init()
        self.commit("first", {"first.txt": "first"})
        other = Path(tempfile.mkdtemp(prefix="okf-git-owner-")).resolve()
        self.addCleanup(shutil.rmtree, other, True)
        (other / "second.txt").write_text("second", encoding="utf8")
        for args in [("init", "--initial-branch=main"), ("config", "user.email", "test@example.invalid"), ("config", "user.name", "Test"), ("config", "commit.gpgsign", "false"), ("add", "-A"), ("commit", "-m", "second")]:
            subprocess.run(["git", *args], cwd=other, capture_output=True, check=True)
        cache = gitutil.CommitTimesCache()
        with patch.object(cli, "git", side_effect=AssertionError("canonical owner must not call CLI")):
            first = gitutil.path_commit_times(self.repo, cache)
            self.assertIs(first, gitutil.path_commit_times(self.repo, cache))
            second = gitutil.path_commit_times(other, cache)
            self.assertNotIn("first.txt", second)
            self.assertIn("second.txt", second)
            self.assertEqual(other, cache.root)
            self.assertEqual("second", gitutil.collect_commits(other, None)[0].subject)
            self.assertEqual(cli.REPO_ROOT, self.repo)
            self.assertIn("first.txt", gitutil.path_commit_times(self.repo, cache))
            self.assertIsNot(first, cache.mapping)

    def test_legacy_cache_reset_and_runner_patch_reach_owner(self):
        cli._PATH_TIME_MAP = None
        with patch.object(cli, "git", return_value=(0, "@@@2026-01-01T00:00:00Z\nM\0first.txt\0")) as runner:
            first = cli.path_commit_times()
            self.assertIn("first.txt", first)
            runner.reset_mock()
            self.assertIs(first, cli.path_commit_times())
            runner.assert_not_called()
            cli._PATH_TIME_MAP = None
            self.assertIsNot(first, cli.path_commit_times())
            self.assertEqual(2, runner.call_count)

    def test_legacy_git_uses_current_root_and_explicit_cwd(self):
        with patch.object(gitutil.subprocess, "run") as run:
            run.return_value.returncode = 0
            run.return_value.stdout = "result"
            self.assertEqual((0, "result"), cli.git("status"))
            self.assertEqual(str(self.repo), run.call_args.kwargs["cwd"])
            self.assertEqual((0, "result"), cli.git("status", cwd=self.docs))
            self.assertEqual(str(self.docs), run.call_args.kwargs["cwd"])
        with patch.object(gitutil.subprocess, "run", side_effect=FileNotFoundError):
            self.assertEqual((127, ""), cli.git("status"))

    def test_runner_errors_keep_shared_exception_and_messages(self):
        with patch.object(cli, "git", return_value=(127, "")):
            with self.assertRaisesRegex(cli.OkfError, "git リポジトリが見つかりません"):
                cli.collect_commits(None)
        def runner(*args):
            if args[0] == "log":
                return 128, ""
            return 0, ""
        with self.assertRaisesRegex(cli.OkfError, "範囲: bad"):
            gitutil.collect_commits(self.repo, "bad", runner=runner)
        with patch.object(cli, "git", side_effect=runner):
            with self.assertRaisesRegex(cli.OkfError, "範囲: bad"):
                cli.collect_commits("bad")

    def test_pure_parser_and_commit_exports_keep_identity_and_special_paths(self):
        self.assertIs(cli.Commit, gitutil.Commit)
        self.assertIs(cli._parse_log_z, gitutil._parse_log_z)
        self.assertIs(cli.parse_porcelain_z, gitutil.parse_porcelain_z)
        paths = ["old\t日本語.txt", "new\n日本語.txt"]
        record = gitutil._parse_log_z("@@@sha\tshort\tdate\tsubject\nR100\0" + "\0".join(paths) + "\0", 4)
        self.assertEqual(paths, [path for _, path in record[0][1]])
        self.assertEqual(list(reversed(paths)), gitutil.parse_porcelain_z("R  " + paths[1] + "\0" + paths[0] + "\0"))

    def test_canonical_resource_uses_project_root_not_cli_or_docs_root(self):
        self.write("src/item1.txt", "one")
        self.write("src/itemx.txt", "other")
        with patch.object(cli, "REPO_ROOT", self.docs):
            self.assertEqual(["src/item1.txt"], gitutil.resolve_resource(self.repo, "src/item[0-9].txt"))
            self.assertEqual([], cli.resolve_resource("src/item[0-9].txt"))

    def test_legacy_last_time_keeps_path_cache_patch_and_date_comparison(self):
        with patch.object(cli, "path_commit_times", return_value={"first": "2026-01-01T23:00:00-05:00", "second": "2026-01-02T01:00:00Z"}) as times:
            self.assertEqual("2026-01-01T23:00:00-05:00", cli.last_commit_time(["first", "second"]))
            times.assert_called_once_with()

    def test_gate_and_dirty_helpers_keep_runner_and_root_contract(self):
        with patch.object(cli, "git", return_value=(0, ".git/okf-gate")):
            self.assertEqual(self.repo / ".git/okf-gate", cli.gate_state_dir())
        with patch.object(cli, "git", return_value=(128, "")):
            self.assertTrue(cli._has_local_changes())
        with patch.object(cli, "git", return_value=(0, "")):
            self.assertFalse(cli._has_local_changes())
