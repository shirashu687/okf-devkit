"""Regression seams fixed before decomposing the Python CLI."""
from __future__ import annotations

import contextlib
import io
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from unittest.mock import patch

from helpers import OkfTestCase, CONFIG_TEMPLATE, doc_text
from okf_devkit import cli


class CliContextTest(OkfTestCase):
    def second_repo(self) -> Path:
        root = Path(tempfile.mkdtemp(prefix="okf-context-other-")).resolve()
        self.addCleanup(shutil.rmtree, root, True)
        (root / "docs").mkdir()
        (root / "okf.yml").write_text(CONFIG_TEMPLATE.format(baseline_line="", index_link_style_line=""), encoding="utf8")
        return root

    @staticmethod
    def commit_file(root: Path, name: str) -> None:
        (root / name).write_text(name, encoding="utf8")
        for args in [("init", "--initial-branch=main"), ("config", "user.email", "test@example.invalid"), ("config", "user.name", "Test"), ("config", "commit.gpgsign", "false"), ("add", "-A"), ("commit", "-m", "fixture")]:
            subprocess.run(["git", *args], cwd=root, check=True, capture_output=True)

    def test_repeated_main_and_direct_root_injection_use_current_git_cache(self):
        self.make_config(name="okf.yml")
        other = self.second_repo()
        self.commit_file(self.repo, "first-code.txt")
        self.commit_file(other, "second-code.txt")
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(0, cli.main(["--root", str(self.repo), "status", "--format", "json"]))
            first = cli.path_commit_times()
            self.assertIn("first-code.txt", first)
            self.assertEqual(0, cli.main(["--root", str(other), "status", "--format", "json"]))
            second = cli.path_commit_times()
        self.assertIn("second-code.txt", second)
        self.assertNotIn("first-code.txt", second)
        self.assertIsNot(first, second)
        # Existing helper callers still inject cli.REPO_ROOT directly.
        cli.REPO_ROOT = self.repo
        self.assertIn("first-code.txt", cli.path_commit_times())
        self.assertNotIn("second-code.txt", cli.path_commit_times())

    def test_absolute_config_and_root_from_other_cwd_do_not_change_cwd(self):
        config = self.make_config(name="custom.yml")
        self.write("docs/first.md", doc_text(type_="Convention", title="First", layer="shared", code_globs=None))
        other = self.second_repo()
        (other / "docs/second.md").write_text(doc_text(type_="Convention", title="Second", layer="shared", code_globs=None), encoding="utf8")
        previous = Path.cwd()
        self.addCleanup(os.chdir, previous)
        os.chdir(other)
        with patch("os.chdir", side_effect=AssertionError("main must not change CWD")), contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(0, cli.main(["--config", str(config), "index", "--write"]))
            self.assertEqual(other, Path.cwd())
            self.assertEqual(0, cli.main(["--root", str(other), "index", "--write"]))
        self.assertIn("First", (self.docs / "index.md").read_text(encoding="utf8"))
        self.assertNotIn("Second", (self.docs / "index.md").read_text(encoding="utf8"))
        self.assertIn("Second", (other / "docs/index.md").read_text(encoding="utf8"))

    def test_repeated_main_refreshes_same_root_after_new_commit(self):
        self.make_config(name="okf.yml")
        self.commit_file(self.repo, "first-code.txt")
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(0, cli.main(["--root", str(self.repo), "status"]))
            self.assertNotIn("later-code.txt", cli.path_commit_times())
            self.commit_file(self.repo, "later-code.txt")
            self.assertEqual(0, cli.main(["--root", str(self.repo), "status"]))
        self.assertIn("later-code.txt", cli.path_commit_times())

    def test_yaml_backend_seam_observes_actual_mini_owner_for_config_and_doc(self):
        config = self.make_config()
        doc = self.write("docs/test.md", doc_text(type_="Convention", layer="shared", code_globs=None))
        mini = cli._MiniYaml
        with patch.object(cli, "_pyyaml", None), patch.object(cli, "_MiniYaml", wraps=mini) as observed:
            bundle = cli.Bundle(config)
            parsed = cli.Doc(doc, bundle.root)
            self.assertEqual("Convention", parsed.fm["type"])
            sources = [call.args[1] for call in observed.call_args_list]
            self.assertIn(str(config), sources)
            self.assertIn("docs/test.md", sources)
            with self.assertRaises(cli.YamlSubsetError):
                cli.parse_yaml("key: &anchor text\n", "rejected-source")
            self.assertEqual("rejected-source", observed.call_args.args[1])

    def test_pyyaml_backend_seam_is_exercised_when_available(self):
        if self._orig_pyyaml is None:
            self.skipTest("PyYAML unavailable")
        with patch.object(self._orig_pyyaml, "safe_load", wraps=self._orig_pyyaml.safe_load) as observed:
            self.assertEqual({"key": "value"}, cli.parse_yaml("key: value\n"))
        observed.assert_called_once()
