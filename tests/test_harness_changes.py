"""Behavioral tests for the repository-local protected-change check."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
CHECKER = REPO_ROOT / "harness" / "project" / "check_changes.py"


class HarnessChangesTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.repo = Path(self.tempdir.name)
        self.git("init", "--initial-branch=main")
        self.git("config", "user.email", "test@example.com")
        self.git("config", "user.name", "okf test")
        self.git("config", "commit.gpgsign", "false")

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def git(self, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
        proc = subprocess.run(
            ["git", *args],
            cwd=self.repo,
            text=True,
            encoding="utf-8",
            capture_output=True,
            check=False,
        )
        if check and proc.returncode != 0:
            self.fail(f"git {' '.join(args)} failed: {proc.stderr}")
        return proc

    def write(self, relative: str, content: str = "content\n") -> Path:
        path = self.repo.joinpath(*relative.split("/"))
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path

    def commit_all(self, message: str) -> str:
        self.git("add", "-A")
        self.git("commit", "-m", message)
        return self.git("rev-parse", "HEAD").stdout.strip()

    def base_repository(self) -> str:
        self.write("harness/core/policy/requirements.md", "initial policy\n")
        self.write("harness/project/config.md", "initial config\n")
        self.write(".agents/skills/example/SKILL.md", "upstream codex\n")
        self.write(".claude/skills/example/SKILL.md", "upstream claude\n")
        self.write("skills-lock.json", "{}\n")
        self.write("ordinary.txt", "ordinary\n")
        return self.commit_all("initial repository")

    def run_checker(self, base: str, head: str | None = None) -> subprocess.CompletedProcess[str]:
        command = [sys.executable, str(CHECKER), "--base", base]
        if head is not None:
            command.extend(["--head", head])
        return subprocess.run(
            command,
            cwd=self.repo,
            text=True,
            encoding="utf-8",
            capture_output=True,
            check=False,
        )

    def declaration(
        self,
        base: str,
        changes: list[dict[str, str]],
        *,
        filename: str = "T-0005.changes.json",
        worklog: str = "harness/state/journal/T-0005.md",
    ) -> None:
        self.write(worklog, "# T-0005\n")
        document = {
            "version": 1,
            "base": base,
            "worklog": worklog,
            "changes": changes,
        }
        self.write(f"harness/state/journal/{filename}", json.dumps(document, ensure_ascii=False) + "\n")

    @staticmethod
    def change(path: str, reason: str = "test change") -> dict[str, str]:
        return {"path": path, "reason": reason}

    def test_no_changes_and_ordinary_change_are_allowed(self) -> None:
        base = self.base_repository()

        unchanged = self.run_checker(base)
        self.assertEqual(unchanged.returncode, 0, unchanged.stdout + unchanged.stderr)
        self.assertIn("result=ok", unchanged.stdout)

        self.write("notes with 日本語.txt", "ordinary\n")
        ordinary = self.run_checker(base)
        self.assertEqual(ordinary.returncode, 0, ordinary.stdout + ordinary.stderr)
        self.assertIn("path=notes with 日本語.txt category=ordinary", ordinary.stdout)

    def test_protected_change_fails_then_declared_change_succeeds(self) -> None:
        base = self.base_repository()
        self.write("harness/core/policy/requirements.md", "changed policy\n")

        failed = self.run_checker(base)
        self.assertEqual(failed.returncode, 1, failed.stdout + failed.stderr)
        self.assertIn("undeclared", failed.stdout)
        self.assertIn("harness/core/policy/requirements.md", failed.stdout)

        self.declaration(base, [self.change("harness/core/policy/requirements.md")])
        succeeded = self.run_checker(base)
        self.assertEqual(succeeded.returncode, 0, succeeded.stdout + succeeded.stderr)
        self.assertIn("declaration=declared", succeeded.stdout)
        self.assertIn("declaration presence is not human approval", succeeded.stdout)

    def test_rename_requires_old_and_new_protected_paths(self) -> None:
        base = self.base_repository()
        self.git("mv", "harness/core/policy/requirements.md", "harness/core/policy/requirements-renamed.md")
        self.declaration(base, [self.change("harness/core/policy/requirements-renamed.md")])

        missing_old = self.run_checker(base)
        self.assertEqual(missing_old.returncode, 1, missing_old.stdout + missing_old.stderr)
        self.assertIn("requirements.md", missing_old.stdout)

        self.declaration(
            base,
            [
                self.change("harness/core/policy/requirements.md"),
                self.change("harness/core/policy/requirements-renamed.md"),
            ],
        )
        complete = self.run_checker(base)
        self.assertEqual(complete.returncode, 0, complete.stdout + complete.stderr)
        self.assertIn("status=R", complete.stdout)

    def test_deleted_protected_path_requires_declaration(self) -> None:
        base = self.base_repository()
        (self.repo / "harness" / "core" / "policy" / "requirements.md").unlink()
        self.declaration(base, [self.change("harness/core/policy/requirements.md")])

        result = self.run_checker(base)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("status=D", result.stdout)

    def test_rename_between_protected_and_ordinary_paths_requires_both_names(self) -> None:
        base = self.base_repository()
        self.git("mv", "harness/core/policy/requirements.md", "renamed-policy.txt")
        self.declaration(base, [self.change("harness/core/policy/requirements.md")])

        missing_new = self.run_checker(base)
        self.assertEqual(missing_new.returncode, 1, missing_new.stdout + missing_new.stderr)
        self.assertIn("renamed-policy.txt", missing_new.stdout)

        self.declaration(
            base,
            [self.change("harness/core/policy/requirements.md"), self.change("renamed-policy.txt")],
        )
        complete = self.run_checker(base)
        self.assertEqual(complete.returncode, 0, complete.stdout + complete.stderr)
        self.assertIn("path=renamed-policy.txt category=protected", complete.stdout)

    def test_upstream_copies_and_lock_are_each_reported(self) -> None:
        base = self.base_repository()
        self.write(".agents/skills/example/SKILL.md", "changed upstream\n")
        self.write(".claude/skills/example/SKILL.md", "changed upstream\n")
        self.write("skills-lock.json", '{"changed": true}\n')
        self.declaration(
            base,
            [
                self.change(".agents/skills/example/SKILL.md"),
                self.change(".claude/skills/example/SKILL.md"),
                self.change("skills-lock.json"),
            ],
        )

        result = self.run_checker(base)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        for path in (
            ".agents/skills/example/SKILL.md",
            ".claude/skills/example/SKILL.md",
            "skills-lock.json",
        ):
            self.assertIn(f"path={path} category=upstream", result.stdout)

    def test_invalid_declarations_are_rejected(self) -> None:
        base = self.base_repository()
        self.write("harness/core/policy/requirements.md", "changed policy\n")
        declaration_path = self.repo / "harness" / "state" / "journal" / "T-0005.changes.json"
        declaration_path.parent.mkdir(parents=True, exist_ok=True)
        worklog = "harness/state/journal/T-0005.md"

        valid = {
            "version": 1,
            "base": base,
            "worklog": worklog,
            "changes": [self.change("harness/core/policy/requirements.md")],
        }
        invalid_documents: list[object] = [
            "not json",
            {**valid, "version": 2},
            {**valid, "base": "0" * 40},
            {**valid, "worklog": "harness/state/journal/missing.md"},
            {**valid, "changes": [self.change("harness/core/policy/requirements.md", "")]},
            {**valid, "changes": [{"path": "../requirements.md", "reason": "escape"}]},
            {**valid, "changes": [{"path": "tests/*.py", "reason": "glob"}]},
            {
                **valid,
                "changes": [
                    self.change("harness/core/policy/requirements.md"),
                    self.change("harness/core/policy/requirements.md"),
                ],
            },
            {**valid, "changes": [self.change("ordinary.txt", "ordinary path")]},
        ]

        for document in invalid_documents:
            if isinstance(document, str):
                declaration_path.write_text(document, encoding="utf-8")
            else:
                declaration_path.write_text(json.dumps(document), encoding="utf-8")
            if document != invalid_documents[0]:
                self.write(worklog, "# T-0005\n")
            result = self.run_checker(base)
            self.assertEqual(result.returncode, 1, f"document was accepted: {document!r}\n{result.stdout}")

    def test_unchanged_old_declaration_is_not_reused(self) -> None:
        initial = self.base_repository()
        self.declaration(initial, [self.change("harness/core/policy/requirements.md")])
        comparison_base = self.commit_all("add old declaration")
        self.write("harness/core/policy/requirements.md", "changed after declaration\n")

        result = self.run_checker(comparison_base)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("undeclared", result.stdout)

    def test_head_declaration_worklog_must_be_a_blob(self) -> None:
        base = self.base_repository()
        self.write("harness/core/policy/requirements.md", "changed policy\n")
        directory = self.repo / "harness" / "state" / "journal" / "not-a-file.md"
        directory.mkdir(parents=True)
        (directory / "child.txt").write_text("tree\n", encoding="utf-8")
        document = {
            "version": 1,
            "base": base,
            "worklog": "harness/state/journal/not-a-file.md",
            "changes": [self.change("harness/core/policy/requirements.md")],
        }
        self.write(
            "harness/state/journal/T-0005.changes.json",
            json.dumps(document) + "\n",
        )
        head = self.commit_all("invalid tree worklog")

        result = self.run_checker(base, head)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("worklog does not exist", result.stdout)

    def test_working_tree_covers_staged_unstaged_and_untracked_but_head_does_not(self) -> None:
        base = self.base_repository()
        self.write("harness/core/policy/requirements.md", "staged policy\n")
        self.git("add", "harness/core/policy/requirements.md")
        self.write("harness/project/config.md", "unstaged config\n")
        self.write("tests/日本語 test.py", "untracked test\n")
        self.write(".agents/skills/space 日本語/SKILL.md", "untracked skill\n")
        self.declaration(
            base,
            [
                self.change("harness/core/policy/requirements.md"),
                self.change("harness/project/config.md"),
                self.change("tests/日本語 test.py"),
                self.change(".agents/skills/space 日本語/SKILL.md"),
            ],
        )

        working_tree = self.run_checker(base)
        self.assertEqual(working_tree.returncode, 0, working_tree.stdout + working_tree.stderr)
        for path in (
            "harness/core/policy/requirements.md",
            "harness/project/config.md",
            "tests/日本語 test.py",
            ".agents/skills/space 日本語/SKILL.md",
        ):
            self.assertIn(f"path={path}", working_tree.stdout)

        head = self.commit_all("protected changes")
        self.write("harness/project/config.md", "dirty after head\n")
        self.write("tests/dirty.py", "ignored by two-commit mode\n")
        two_commits = self.run_checker(base, head)
        self.assertEqual(two_commits.returncode, 0, two_commits.stdout + two_commits.stderr)
        self.assertNotIn("dirty after head", two_commits.stdout)
        self.assertNotIn("tests/dirty.py", two_commits.stdout)

    def test_unavailable_base_head_shallow_and_conflict_are_not_success(self) -> None:
        base = self.base_repository()

        unknown = self.run_checker("f" * 40)
        self.assertEqual(unknown.returncode, 2, unknown.stdout + unknown.stderr)

        all_zero = self.run_checker("0" * 40)
        self.assertEqual(all_zero.returncode, 2, all_zero.stdout + all_zero.stderr)

        self.repo.joinpath(".git", "shallow").write_text(base + "\n", encoding="ascii")
        shallow = self.run_checker(base)
        self.assertEqual(shallow.returncode, 2, shallow.stdout + shallow.stderr)

        self.tearDown()
        self.setUp()
        base = self.base_repository()
        self.git("checkout", "-b", "side")
        self.write("harness/project/config.md", "side\n")
        self.git("add", "-A")
        self.git("commit", "-m", "side change")
        self.git("checkout", "main")
        self.write("harness/project/config.md", "main\n")
        self.git("add", "-A")
        self.git("commit", "-m", "main change")
        merge = self.git("merge", "side", "--no-commit", "--no-ff", check=False)
        self.assertNotEqual(merge.returncode, 0)
        conflict = self.run_checker(base)
        self.assertEqual(conflict.returncode, 2, conflict.stdout + conflict.stderr)


if __name__ == "__main__":
    unittest.main()
