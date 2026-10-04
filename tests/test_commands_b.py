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

    def test_new_writes_and_reports_bundle_owner_after_cli_root_change(self):
        from okf_devkit.commands import new
        config = self.make_config()
        self.make_templates()
        bundle = cli.Bundle(config)
        prior = cli.REPO_ROOT
        cli.REPO_ROOT = self.repo / 'different'
        self.addCleanup(setattr, cli, 'REPO_ROOT', prior)
        args = ns(kind='doc', layer='server', type='Reference', title='Owner', dir=None, slug='owner', code_globs=['app/server/api.py'])
        with patch.object(new, 'write_if_changed', wraps=new.write_if_changed) as writer, contextlib.redirect_stdout(io.StringIO()) as output:
            self.assertEqual(0, new.cmd_new(bundle, args))
        self.assertTrue(writer.called)
        self.assertEqual('docs/server/owner.md', output.getvalue().strip())
        self.assertTrue((bundle.root / 'server/owner.md').is_file())
        self.assertFalse((self.repo / 'different').exists())

    def test_status_constructs_backlog_docs_with_explicit_owner_root(self):
        from okf_devkit.commands import status
        config = self.make_config()
        self.write('docs/backlog/B-0001-owner.md', doc_text(type_='Backlog Item', layer='shared', code_globs=None))
        bundle = cli.Bundle(config)
        prior = cli.REPO_ROOT
        cli.REPO_ROOT = self.repo / 'different'
        self.addCleanup(setattr, cli, 'REPO_ROOT', prior)
        with patch.object(status, 'Doc', wraps=status.Doc) as factory:
            docs = status.backlog_docs(bundle)
        self.assertEqual(1, len(docs))
        self.assertEqual('docs/backlog/B-0001-owner.md', docs[0].repo_rel)
        self.assertEqual(bundle.repo_root, factory.call_args.kwargs['repo_root'])
