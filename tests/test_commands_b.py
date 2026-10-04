"""Remaining command ownership at public command and compatibility seams."""
import contextlib
import io
from unittest.mock import patch
from helpers import OkfTestCase, ns, doc_text
from okf_devkit import cli, gitutil

class RemainingCommandTest(OkfTestCase):
    def test_stale_uses_one_owner_cache_for_multiple_documents(self):
        from okf_devkit.commands import stale
        self.git_init()
        config = self.make_config()
        self.commit('source', {'src/a.ts': 'code'})
        for name in ('one', 'two'):
            self.write('docs/' + name + '.md', doc_text(type_='Reference', layer='shared'))
        bundle = cli.Bundle(config)
        prior = cli.REPO_ROOT
        cli.REPO_ROOT = self.repo / 'different'
        self.addCleanup(setattr, cli, 'REPO_ROOT', prior)
        with patch.object(gitutil, 'git', wraps=gitutil.git) as observed:
            stale.run_stale(bundle)
        self.assertTrue(observed.called)
        self.assertTrue(all(c.args[0] == bundle.repo_root for c in observed.call_args_list))
        history = [c for c in observed.call_args_list if 'log' in c.args]
        self.assertEqual(1, len(history))

    def test_affected_keeps_bundle_git_root_and_resource_mapping(self):
        from okf_devkit.commands import affected
        self.git_init()
        config = self.make_config()
        self.commit('source', {'app/client/first.ts': 'original'})
        self.write('app/client/first.ts', 'changed')
        self.write('docs/reference.md', doc_text(type_='Reference', layer='shared', code_globs='  - app/client/first.ts'))
        bundle = cli.Bundle(config)
        prior = cli.REPO_ROOT
        cli.REPO_ROOT = self.repo / 'different'
        self.addCleanup(setattr, cli, 'REPO_ROOT', prior)
        with patch.object(gitutil, 'git', wraps=gitutil.git) as runner, contextlib.redirect_stdout(io.StringIO()) as output:
            self.assertEqual(0, affected.cmd_affected(bundle, ns(paths=None, base='HEAD')))
        self.assertTrue(runner.called)
        self.assertTrue(all(c.args[0] == bundle.repo_root for c in runner.call_args_list))
        self.assertIn('docs/reference.md  <- app/client/first.ts', output.getvalue())
