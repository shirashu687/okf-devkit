"""Canonical commands keep the bundle's project root; CLI adapters retain seams."""
import contextlib
import io
from unittest.mock import patch
from helpers import OkfTestCase, ns
from okf_devkit import cli
from okf_devkit.commands import index

class CommandContextTest(OkfTestCase):
    def test_index_owner_ignores_later_legacy_root_and_executes_owner_writer(self):
        config = self.make_config()
        bundle = cli.Bundle(config)
        original_root = cli.REPO_ROOT
        cli.REPO_ROOT = self.repo / 'different'
        self.addCleanup(setattr, cli, 'REPO_ROOT', original_root)
        with patch.object(index, 'write_if_changed', wraps=index.write_if_changed) as writer, contextlib.redirect_stdout(io.StringIO()) as output:
            self.assertEqual(0, index.cmd_index(bundle, ns(write=True, check=False, quiet=False)))
        self.assertTrue(writer.called)
        self.assertIn('docs/index.md', output.getvalue())
        self.assertTrue((bundle.root / 'index.md').exists())

    def test_legacy_index_uses_current_writer_seam(self):
        config = self.make_config()
        bundle = cli.Bundle(config)
        with patch.object(cli, 'write_if_changed', wraps=cli.write_if_changed) as writer, contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(0, cli.cmd_index(bundle, ns(write=True, check=False, quiet=False)))
        self.assertTrue(writer.called)
