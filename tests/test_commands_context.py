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

    def test_log_owner_keeps_bundle_git_root_after_cli_root_changes(self):
        from okf_devkit.commands import log
        from okf_devkit import gitutil
        self.git_init()
        config = self.make_config()
        self.commit('fixture', {'app/client/first.ts': 'code'})
        bundle = cli.Bundle(config)
        original_root = cli.REPO_ROOT
        cli.REPO_ROOT = self.repo / 'different'
        self.addCleanup(setattr, cli, 'REPO_ROOT', original_root)
        with patch.object(gitutil, 'git', wraps=gitutil.git) as runner, contextlib.redirect_stdout(io.StringIO()) as output:
            self.assertEqual(0, log.cmd_log(bundle, ns(write=True, range=None, layer=None, dry_run=False)))
        self.assertTrue(runner.called)
        self.assertTrue(all(call.args[0] == bundle.repo_root for call in runner.call_args_list))
        self.assertIn('docs/client/log.md', output.getvalue())
        self.assertIn('fixture', (bundle.root / 'client/log.md').read_text(encoding='utf8'))

    def test_legacy_log_keeps_current_git_runner_and_writer(self):
        self.git_init()
        config = self.make_config()
        self.commit('fixture', {'app/client/first.ts': 'code'})
        bundle = cli.Bundle(config)
        with patch.object(cli, 'git', wraps=cli.git) as runner, patch.object(cli, 'write_if_changed', wraps=cli.write_if_changed) as writer, contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(0, cli.cmd_log(bundle, ns(write=True, range=None, layer=None, dry_run=False)))
        self.assertTrue(runner.called)
        self.assertTrue(writer.called)

    def test_lint_owner_resolves_resources_against_bundle_root(self):
        from okf_devkit.commands import lint
        from okf_devkit import gitutil
        from helpers import doc_text
        config = self.make_config()
        self.write('src/a.ts', 'code')
        self.write('docs/reference.md', doc_text(type_='Reference', layer='shared'))
        bundle = cli.Bundle(config)
        original_root = cli.REPO_ROOT
        cli.REPO_ROOT = self.repo / 'different'
        self.addCleanup(setattr, cli, 'REPO_ROOT', original_root)
        with patch.object(gitutil, 'resolve_resource', wraps=gitutil.resolve_resource) as resolver:
            findings = lint.run_lint(bundle)
        self.assertTrue(resolver.called)
        self.assertTrue(all(call.args[0] == bundle.repo_root for call in resolver.call_args_list))
        self.assertFalse(any(f.rule == 'L10' and 'src/a.ts' in f.message for f in findings))
        (self.repo / 'src/a.ts').unlink()
        missing = lint.run_lint(bundle)
        self.assertTrue(any(f.rule == 'L10' and 'src/a.ts' in f.message for f in missing))
