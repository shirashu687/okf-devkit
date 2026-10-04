"""Public CLI examples in generated guidance, exercised in isolated projects."""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from helpers import doc_text

PROJECT = Path(__file__).resolve().parents[1]


class AiOperationsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="okf-ai-operations-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()

    def cli(self, *args: str, runtime: str = "python") -> subprocess.CompletedProcess:
        command = ([sys.executable, "-m", "okf_devkit.cli"] if runtime == "python"
                   else ["node", str(PROJECT / "node/cli.mjs")])
        env = os.environ.copy()
        env["PYTHONPATH"] = str(PROJECT / "src")
        env["PYTHONIOENCODING"] = "utf-8"
        return subprocess.run(command + ["--root", str(self.root), *args],
                              cwd=self.root, env=env, capture_output=True,
                              encoding="utf-8", errors="strict", timeout=30)

    def successful(self, *args: str, runtime: str = "python") -> subprocess.CompletedProcess:
        result = self.cli(*args, runtime=runtime)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return result

    def write(self, relative: str, content: str) -> Path:
        target = self.root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8", newline="\n")
        return target

    def snapshot(self) -> dict:
        # Includes hidden/generated files and modification times, not just Markdown.
        return {p.relative_to(self.root).as_posix(): (p.read_bytes(), p.stat().st_mtime_ns)
                for p in self.root.rglob("*") if p.is_file()}

    def git(self, *args: str) -> str:
        result = subprocess.run(["git", *args], cwd=self.root, capture_output=True,
                                encoding="utf-8", timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout

    def require_node(self) -> None:
        if not shutil.which("node") or not (PROJECT / "node_modules/markdown-it").exists():
            self.skipTest("Node runtime/dependencies unavailable; npm tests cover Node setup")

    def prepare(self, runtime: str = "python") -> None:
        self.successful("init", "--bundle-root", "knowledge", runtime=runtime)
        self.write("src/app.py", "VALUE = 1\n")
        self.write("knowledge/project/app.md", doc_text(
            title="App", layer="shared", status="draft", code_globs="  - src/app.py",
            body="# App\n\nFixture documentation.\n"))
        self.successful("new", "backlog", "--title", "Review app", runtime=runtime)
        self.successful("index", "--write", runtime=runtime)

    def check_generated_guidance(self, runtime: str) -> None:
        # Reinitialization must preserve the consumer's instructions and edited docs.
        root_agents = self.write("AGENTS.md", "# Consumer instructions\n")
        self.write("package.json", json.dumps({"scripts": {"okf": "okf"}, "devDependencies": {"okf-devkit": "0.1.0"}}))
        self.successful("init", "--bundle-root", "knowledge", "--layer", "api=src/**", runtime=runtime)
        instructions = self.root / "knowledge/AGENTS.md"
        generated = instructions.read_text(encoding="utf-8")
        self.assertNotRegex(generated, r"\{\{[A-Z_]+\}\}")
        self.assertIn("knowledge/", generated)
        self.assertNotIn("harness/core/", generated)
        self.assertFalse((self.root / "harness").exists())
        for href in re.findall(r"\]\(([^)]+)\)", generated):
            if href.startswith(("http:", "https:", "#")):
                continue
            link = href.split("#", 1)[0]
            target = self.root / "knowledge" / link.lstrip("/") if link.startswith("/") else instructions.parent / link
            self.assertTrue(target.exists(), f"broken generated guidance link: {href}")
        if runtime == "node":
            self.assertIn("node node_modules/okf-devkit/node/cli.mjs", generated)
        self.assertIn("python -m okf_devkit.cli", generated)
        instructions.write_text(generated + "\nConsumer addition.\n", encoding="utf-8")
        convention = self.write("knowledge/CONVENTIONS.md", "Consumer convention\n")
        preserved = {p: (p.read_bytes(), p.stat().st_mtime_ns)
                     for p in [root_agents, instructions, convention]}
        self.successful("init", "--bundle-root", "knowledge", runtime=runtime)
        for p, before in preserved.items():
            self.assertEqual((p.read_bytes(), p.stat().st_mtime_ns), before)

    def check_readonly_operations(self, runtime: str) -> None:
        self.prepare(runtime)
        self.write("_site/index.html", "Previously generated HTML\n")
        self.write(".private-fixture", "not user data\n")
        before = self.snapshot()
        lint = self.successful("lint", "--strict", runtime=runtime)
        self.assertRegex(lint.stdout, r"error 0")
        self.successful("index", "--check", runtime=runtime)
        self.successful("render", "--check", runtime=runtime)
        stale = self.successful("stale", "--format", "json", runtime=runtime)
        findings = json.loads(stale.stdout)
        self.assertTrue(any(item["path"] == "knowledge/project/app.md" and item["kind"] == "draft-stale" for item in findings))
        affected = self.successful("affected", "--paths", "src/app.py", "uncovered/tool.py", runtime=runtime)
        self.assertIn("knowledge/project/app.md", affected.stdout)
        self.assertIn("uncovered/tool.py", affected.stdout)
        status = json.loads(self.successful("status", "--format", "json", runtime=runtime).stdout)
        self.assertEqual(status["total"], 1)
        self.assertEqual(status["states"]["todo"], 1)
        self.assertEqual(self.snapshot(), before)
        self.assertFalse((self.root / "_site/.okf-render-manifest.json").exists())

    def test_python_generated_custom_bundle_guidance_and_reinitialization(self) -> None:
        self.check_generated_guidance("python")

    def test_node_generated_custom_bundle_guidance_and_reinitialization(self) -> None:
        self.require_node()
        self.check_generated_guidance("node")

    def test_python_daily_checks_are_readonly_and_findings_require_interpretation(self) -> None:
        self.check_readonly_operations("python")

    def test_node_daily_checks_are_readonly_and_findings_require_interpretation(self) -> None:
        self.require_node()
        self.check_readonly_operations("node")

    def test_sync_writes_indexes_but_warns_when_log_cannot_record_current_work(self) -> None:
        self.prepare()
        self.successful("init", "--bundle-root", "knowledge", "--layer", "api=src/**", "--force")
        self.successful("index", "--write")
        self.write("knowledge/api/log.md", "# Changes\n\n## 2026-01-01\n- **Creation** Existing migrated item.\n")
        self.git("init", "--initial-branch=main")
        self.git("config", "user.email", "fixture@example.invalid")
        self.git("config", "user.name", "Fixture")
        self.git("config", "commit.gpgsign", "false")
        self.git("add", ".")
        self.git("commit", "-m", "Initial fixture")
        self.write("src/app.py", "VALUE = 2\n")
        self.write("knowledge/project/extra.md", doc_text(
            title="Extra", layer="shared", status="stable", code_globs="  - src/app.py", body="# Extra\n"))
        index = self.root / "knowledge/project/index.md"
        previous_index = index.read_bytes()
        logs = {p: p.read_bytes() for p in (self.root / "knowledge").rglob("log.md")}
        result = self.successful("sync")
        self.assertIn("[okf log]", result.stderr)
        self.assertIn("スキップしました", result.stderr)
        self.assertIn("未コミット", result.stderr)
        self.assertIn("log.baseline", result.stderr)
        self.assertIn("log.md", result.stderr)
        self.assertNotEqual(index.read_bytes(), previous_index)
        self.assertIn("extra.md", index.read_text(encoding="utf-8"))
        self.assertEqual({p: p.read_bytes() for p in logs}, logs)


if __name__ == "__main__":
    unittest.main()
