"""CLI help is useful before initialization and never modifies project files."""
import contextlib
import io
import tempfile
import unittest
from pathlib import Path
from okf_devkit import cli

COMMANDS = [[], ["init"], ["index"], ["log"], ["lint"], ["stale"],
            ["affected"], ["new"], ["new", "doc"], ["new", "backlog"],
            ["status"], ["render"], ["sync"]]

class CliHelpTest(unittest.TestCase):
    def test_help_before_configuration_lookup_never_writes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            sentinel = root / "user-note.txt"
            sentinel.write_bytes(b"user content\x00")
            for command in COMMANDS:
                with self.subTest(command=command):
                    output = io.StringIO()
                    with contextlib.redirect_stdout(output), self.assertRaises(SystemExit) as stopped:
                        cli.main(["--root", str(root), "--config", str(root / "missing.yml"), *command, "--help"])
                    self.assertEqual(stopped.exception.code, 0)
                    self.assertIn("usage:", output.getvalue())
                    if command:
                        self.assertIn("例:", output.getvalue())
                    self.assertEqual([file.name for file in root.iterdir()], ["user-note.txt"])
                    self.assertEqual(sentinel.read_bytes(), b"user content\x00")
