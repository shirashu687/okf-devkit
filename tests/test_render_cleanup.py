"""Migration tests only use isolated, disposable repositories."""
import json
import contextlib
import io
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from okf_devkit.render_cleanup import (MANIFEST, artifact_bytes, digest, execute_cleanup,
                                      plan_cleanup, validate_roots, write_manifest)
from okf_devkit.renderer import OWNERSHIP_MARKER, RenderError
from okf_devkit import cli, renderer
from helpers import OkfTestCase, ns


class CleanupTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name).resolve()
        self.old, self.new = self.repo / "docs", self.repo / "_site"
        self.old.mkdir()
        self.artifacts = {"index.html": OWNERSHIP_MARKER + "\nhello", "_assets/docs.css": "css"}
        for name, content in self.artifacts.items():
            target = self.old / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(artifact_bytes(content))

    def plan(self):
        return plan_cleanup(self.repo, self.old, self.new, self.artifacts, self.artifacts)

    def test_manifest_migration_preserves_sources_and_backup(self):
        write_manifest(self.repo, self.old, self.artifacts)
        source = self.old / "source.md"
        source.write_text("source")
        moves, lines = self.plan()
        self.assertIn("cleanup keep: docs/source.md (untracked)", lines)
        backup = execute_cleanup(self.repo, self.old, self.new, moves)
        self.assertEqual((backup / "docs/index.html").read_bytes(), artifact_bytes(self.artifacts["index.html"]))
        self.assertFalse((self.old / "index.html").exists())
        self.assertEqual(source.read_text(), "source")
        self.assertEqual(json.loads((backup / "receipt.json").read_text())["status"], "complete")
        self.assertEqual(self.plan()[0], [])

    def test_legacy_exact_only_and_plan_does_not_write(self):
        (self.old / "hand.html").write_text("handwritten")
        before = {p.relative_to(self.repo).as_posix(): p.read_bytes() for p in self.repo.rglob("*") if p.is_file()}
        moves, lines = self.plan()
        self.assertEqual(len(moves), 2)
        self.assertIn("cleanup keep: docs/hand.html (untracked)", lines)
        after = {p.relative_to(self.repo).as_posix(): p.read_bytes() for p in self.repo.rglob("*") if p.is_file()}
        self.assertEqual(before, after)
        (self.old / "index.html").write_text(OWNERSHIP_MARKER + " edited")
        self.assertIn("cleanup keep: docs/index.html (modified)", self.plan()[1])

    def test_changed_and_stale_manifest_entries(self):
        self.artifacts["removed.html"] = OWNERSHIP_MARKER + " stale"
        (self.old / "removed.html").write_text(self.artifacts["removed.html"])
        write_manifest(self.repo, self.old, self.artifacts)
        del self.artifacts["removed.html"]
        (self.old / "index.html").write_text("edited")
        moves, _ = self.plan()
        self.assertEqual({p.name for p, _, _ in moves}, {"removed.html", "docs.css"})

    def test_root_rejections(self):
        for old, new in [(self.old, self.old), (self.old, self.old / "nested"), (self.repo, self.new), (self.repo.parent / "outside", self.new), (self.repo / ".okf", self.new), (self.old, self.repo / ".okf/render-backups/a")]:
            with self.subTest(old=old, new=new), self.assertRaises(RenderError):
                validate_roots(self.repo, old, new)

    @unittest.skipUnless(sys.platform == "win32", "Windows path aliases")
    def test_windows_alias_roots_rejected_before_writes(self):
        snapshot = {p.relative_to(self.repo).as_posix(): p.read_bytes() for p in self.repo.rglob("*") if p.is_file()}
        for name in ("docs.", "docs ", "DOCS", "docs. /site", "docs./site"):
            with self.subTest(name=name), self.assertRaises(RenderError):
                plan_cleanup(self.repo, self.old, self.repo / name, self.artifacts, self.artifacts)
        self.assertEqual(snapshot, {p.relative_to(self.repo).as_posix(): p.read_bytes() for p in self.repo.rglob("*") if p.is_file()})

    def test_actual_directory_alias_is_rejected(self):
        self.new.mkdir()
        with patch("okf_devkit.render_cleanup.os.path.samefile", return_value=True), self.assertRaises(RenderError):
            validate_roots(self.repo, self.old, self.new)

    @unittest.skipUnless(sys.platform == "win32", "Windows case-insensitive artifact names")
    def test_windows_manifest_case_alias_rejected_before_writes(self):
        write_manifest(self.repo, self.old, self.artifacts)
        manifest_path = self.old / MANIFEST
        value = json.loads(manifest_path.read_text())
        value["files"].append({"path": "INDEX.html", "sha256": digest(artifact_bytes(self.artifacts["index.html"]))})
        manifest_path.write_text(json.dumps(value))
        snapshot = {p.relative_to(self.repo).as_posix(): p.read_bytes() for p in self.repo.rglob("*") if p.is_file()}
        with self.assertRaises(RenderError):
            self.plan()
        self.assertEqual(snapshot, {p.relative_to(self.repo).as_posix(): p.read_bytes() for p in self.repo.rglob("*") if p.is_file()})

    def test_invalid_manifest_and_destination_conflict(self):
        write_manifest(self.repo, self.old, self.artifacts)
        manifest = json.loads((self.old / MANIFEST).read_text())
        manifest["files"][0]["path"] = "../outside.html"
        (self.old / MANIFEST).write_text(json.dumps(manifest))
        with self.assertRaises(RenderError):
            self.plan()

        (self.old / MANIFEST).unlink()
        self.new.mkdir()
        (self.new / "index.html").write_text("handwritten")
        with self.assertRaises(RenderError):
            self.plan()

    def test_target_unchanged_manifest_can_be_updated_but_edit_cannot(self):
        self.new.mkdir()
        for name, content in self.artifacts.items():
            target = self.new / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(artifact_bytes(content))
        write_manifest(self.repo, self.new, self.artifacts)
        updated = dict(self.artifacts, **{"index.html": OWNERSHIP_MARKER + " new"})
        self.assertTrue(plan_cleanup(self.repo, self.old, self.new, self.artifacts, updated)[0])
        (self.new / "index.html").write_text(OWNERSHIP_MARKER + " manually edited")
        with self.assertRaises(RenderError):
            plan_cleanup(self.repo, self.old, self.new, self.artifacts, updated)

    def test_symlink_rejected(self):
        link = self.repo / "link"
        try:
            link.symlink_to(self.old, target_is_directory=True)
        except OSError:
            self.skipTest("symlink unavailable")
        with self.assertRaises(RenderError):
            validate_roots(self.repo, link, self.new)
        with self.assertRaises(RenderError):
            validate_roots(self.repo, self.old, link)
        (self.repo / ".okf").mkdir()
        (self.repo / ".okf/render-backups").symlink_to(self.old, target_is_directory=True)
        with self.assertRaises(RenderError):
            self.plan()
        self.assertFalse(self.new.exists())

    def test_backup_anchor_non_directory_rejected_during_plan(self):
        (self.repo / ".okf").mkdir()
        (self.repo / ".okf/render-backups").write_text("unrelated")
        with self.assertRaises(RenderError):
            self.plan()
        self.assertFalse(self.new.exists())

    def test_race_and_partial_failure_rollback(self):
        moves, _ = self.plan()
        original = Path.unlink
        count = 0
        def fail_second(path, *args, **kwargs):
            nonlocal count
            count += 1
            if count == 2:
                raise OSError("injected")
            return original(path, *args, **kwargs)
        with patch.object(Path, "unlink", fail_second), self.assertRaisesRegex(RenderError, "rolled-back"):
            execute_cleanup(self.repo, self.old, self.new, moves)
        for name, content in self.artifacts.items():
            self.assertEqual((self.old / name).read_bytes(), artifact_bytes(content))
        moves, _ = self.plan()
        (self.old / "index.html").write_text("changed after plan")
        with self.assertRaises(RenderError):
            execute_cleanup(self.repo, self.old, self.new, moves)

    def test_manifest_deterministic_hashes(self):
        write_manifest(self.repo, self.old, self.artifacts)
        raw = (self.old / MANIFEST).read_bytes()
        self.assertTrue(raw.endswith(b"\n"))
        self.assertEqual(json.loads(raw)["files"][0], {"path": "_assets/docs.css", "sha256": digest(b"css")})

    def test_partial_backup_copy_is_recorded_and_sources_unchanged(self):
        moves, _ = self.plan()
        original = Path.open
        repo = self.repo
        class PartialWriter:
            def __init__(self, stream):
                self.stream = stream
            def __enter__(self):
                return self
            def __exit__(self, *args):
                self.stream.close()
            def write(self, data):
                self.stream.write(data[:1])
                self.stream.flush()
                raise OSError("injected partial copy")
        def open_partial(path, mode="r", *args, **kwargs):
            stream = original(path, mode, *args, **kwargs)
            if mode == "xb" and path.is_relative_to(repo / ".okf/render-backups"):
                return PartialWriter(stream)
            return stream
        with patch.object(Path, "open", open_partial), self.assertRaisesRegex(RenderError, "rolled-back"):
            execute_cleanup(self.repo, self.old, self.new, moves)
        receipt_path = next((self.repo / ".okf/render-backups").glob("*/receipt.json"))
        receipt = json.loads(receipt_path.read_text())
        self.assertEqual(len(receipt["planned"]), len(moves))
        self.assertEqual(receipt["copies"], [])
        self.assertEqual(receipt["moves"], [])
        entry = receipt["planned"][0]
        self.assertEqual((self.repo / entry["backup"]).read_bytes(), artifact_bytes(self.artifacts[moves[0][0].relative_to(self.old).as_posix()])[:1])
        self.assertEqual(entry["sha256"], moves[0][1])
        for name, content in self.artifacts.items():
            self.assertEqual((self.old / name).read_bytes(), artifact_bytes(content))

    def test_initial_receipt_failure_does_not_copy(self):
        moves, _ = self.plan()
        with patch("okf_devkit.render_cleanup._write_atomic", side_effect=OSError("receipt failure")), self.assertRaises(RenderError):
            execute_cleanup(self.repo, self.old, self.new, moves)
        self.assertFalse(list((self.repo / ".okf/render-backups").glob("*/docs/*")))
        for name, content in self.artifacts.items():
            self.assertEqual((self.old / name).read_bytes(), artifact_bytes(content))

    def test_rollback_never_overwrites_concurrent_file(self):
        moves, _ = self.plan()
        original = Path.unlink
        count = 0
        first = moves[0][0]
        def conflict(path, *args, **kwargs):
            nonlocal count
            count += 1
            if count == 2:
                first.write_bytes(b"concurrent handwritten file")
                raise OSError("injected")
            return original(path, *args, **kwargs)
        with patch.object(Path, "unlink", conflict), self.assertRaisesRegex(RenderError, "recovery-required"):
            execute_cleanup(self.repo, self.old, self.new, moves)
        self.assertEqual(first.read_bytes(), b"concurrent handwritten file")
        receipt_path = next((self.repo / ".okf/render-backups").glob("*/receipt.json"))
        self.assertTrue(json.loads(receipt_path.read_text())["recovery_paths"])


@unittest.skipUnless(renderer.MarkdownIt is not None, "markdown-it-py required")
class CleanupCliTests(OkfTestCase):
    def setUp(self):
        super().setUp()
        self.write("docs/index.md", "# Demo\n")

    def render(self, output, old=None, check=False, hook=False):
        with contextlib.redirect_stdout(io.StringIO()) as stream:
            result = cli.cmd_render(self.bundle(), ns(output=output, cleanup_from=old, check=check, hook=hook, open=False))
        return result, stream.getvalue()

    def test_full_cli_migration_check_and_idempotence(self):
        self.render("docs")
        before = {p.relative_to(self.repo).as_posix(): p.read_bytes() for p in self.repo.rglob("*") if p.is_file()}
        self.assertIn("cleanup move: docs/index.html", self.render("_site", "docs", check=True)[1])
        self.assertEqual(before, {p.relative_to(self.repo).as_posix(): p.read_bytes() for p in self.repo.rglob("*") if p.is_file()})
        self.render("_site", "docs")
        self.assertTrue((self.repo / "_site/index.html").exists())
        self.assertFalse((self.docs / "index.html").exists())
        self.assertEqual(self.read("docs/index.md"), "# Demo\n")
        self.assertNotIn("cleanup move:", self.render("_site", "docs")[1])

    @unittest.skipUnless(sys.platform == "win32", "Windows raw path aliases")
    def test_cli_windows_source_and_target_aliases_rejected_before_write(self):
        self.render("docs")
        snapshot = {p.relative_to(self.repo).as_posix(): p.read_bytes() for p in self.repo.rglob("*") if p.is_file()}
        for output, old in (("_site", "docs "), ("_site", "docs."), ("_site ", "docs"), ("_site.", "docs")):
            for check in (True, False):
                with self.subTest(output=output, old=old, check=check), self.assertRaises(cli.OkfError):
                    self.render(output, old, check=check)
                self.assertEqual(snapshot, {p.relative_to(self.repo).as_posix(): p.read_bytes() for p in self.repo.rglob("*") if p.is_file()})

    def test_hook_rejected_before_write_and_render_failure_keeps_old(self):
        with self.assertRaises(cli.OkfError):
            self.render("_site", "docs", hook=True)
        self.assertFalse((self.repo / "_site").exists())
        self.render("docs")
        previous = (self.docs / "index.html").read_bytes()
        with patch.object(renderer, "render_bundle", side_effect=RenderError("injected")), self.assertRaises(cli.OkfError):
            self.render("_site", "docs")
        self.assertEqual(previous, (self.docs / "index.html").read_bytes())
        with patch.object(renderer, "_write_atomic", side_effect=OSError("write failure")), self.assertRaises(cli.OkfError):
            self.render("_site", "docs")
        self.assertEqual(previous, (self.docs / "index.html").read_bytes())

if __name__ == "__main__":
    unittest.main()
