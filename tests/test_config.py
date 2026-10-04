"""Bundle caches, package defaults and explicit-root discovery across projects."""
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

from helpers import OkfTestCase, doc_text
from okf_devkit import cli, config, doc, yamlio
from okf_devkit.errors import OkfError


class ConfigTests(OkfTestCase):
    def test_two_bundles_discover_their_own_roots_after_cli_root_changes(self):
        first_cfg = self.write("okf.yml", "bundle_root: nested/knowledge\n")
        self.write("nested/knowledge/first.md", doc_text(title="First", layer="shared"))
        with tempfile.TemporaryDirectory() as temporary:
            other = Path(temporary).resolve()
            (other / "docs").mkdir()
            (other / "okf.yml").write_text("bundle_root: docs\n", encoding="utf-8")
            (other / "docs/second.md").write_text(doc_text(title="Second", layer="shared"), encoding="utf-8")
            canonical = config.Bundle(first_cfg, repo_root=self.repo)
            legacy = cli.Bundle(first_cfg)
            cli.REPO_ROOT = other
            second = cli.Bundle()
            self.assertEqual(canonical.repo_root, self.repo)
            self.assertEqual(canonical.root, self.repo / "nested/knowledge")
            self.assertEqual(canonical.docs()[0].repo_rel, "nested/knowledge/first.md")
            self.assertIsInstance(canonical.docs()[0], doc.Doc)
            self.assertIsInstance(legacy.docs()[0], cli.Doc)
            self.assertEqual(legacy.docs()[0].repo_rel, "nested/knowledge/first.md")
            self.assertEqual(second.docs()[0].repo_rel, "docs/second.md")
            self.assertIs(legacy.docs(), legacy.docs())
            self.assertIsNot(legacy.docs(), second.docs())

    def test_package_defaults_are_not_loaded_from_foreign_cwd(self):
        cfg = self.write("okf.yml", "bundle_root: docs\ntypes: [Convention]\n")
        with tempfile.TemporaryDirectory() as temporary:
            foreign = Path(temporary)
            (foreign / "defaults.yml").write_text("types: [BAD]\n", encoding="utf-8")
            original = Path.cwd()
            try:
                os.chdir(foreign)
                bundle = config.Bundle(cfg, repo_root=self.repo)
            finally:
                os.chdir(original)
        self.assertEqual(bundle.types, ["Convention"])
        self.assertEqual(bundle.reserved, ("index.md", "log.md"))
        self.assertEqual(config.DEFAULTS_PATH.parent, Path(config.__file__).parent)
        self.assertEqual(cli.DEFAULTS_PATH, config.DEFAULTS_PATH)

    def test_exclusions_reserved_order_and_log_paths_preserved(self):
        cfg = self.write("okf.yml", "bundle_root: docs\nlayers: [api, shared]\nexclude: ['_*', '_*/**', 'private', 'private/**']\nlog:\n  layers: [api]\n  paths: {api: custom/log.md}\n")
        for name in ["z.md", "a.md", "index.md", "log.md", "public/item.md", "private/item.md", "_scratch/item.md"]:
            self.write("docs/" + name, "# Fixture\n")
        bundle = config.Bundle(cfg, repo_root=self.repo)
        names = [p.relative_to(bundle.root).as_posix() for p in bundle.md_files()]
        self.assertEqual(names, ["a.md", "z.md", "public/item.md"])
        self.assertEqual(len(bundle.md_files(include_reserved=True)), 5)
        self.assertEqual(bundle.log_layers(), ["api"])
        self.assertEqual(bundle.log_path("api"), self.docs / "custom/log.md")
        self.assertEqual(bundle.log_path("shared"), self.docs / "log.md")
        self.assertEqual(bundle.log_path("unmapped"), self.docs / "unmapped/log.md")

    def test_actual_yaml_owner_parses_project_and_package_defaults(self):
        cfg = self.write("okf.yml", "bundle_root: docs\n")
        with patch.object(yamlio, "_pyyaml", None), patch.object(yamlio, "_MiniYaml", wraps=yamlio._MiniYaml) as parser:
            bundle = config.Bundle(cfg, repo_root=self.repo)
        self.assertEqual(bundle.root, self.docs)
        sources = [call.args[1] for call in parser.call_args_list]
        self.assertEqual(sources, [str(config.DEFAULTS_PATH), str(cfg)])

    def test_invalid_project_and_index_config_use_same_exception_identity(self):
        self.assertIs(cli.OkfError, OkfError)
        for text in ["- not-a-map\n", "index: not-a-map\n", "index: {link_style: invalid}\n"]:
            with self.subTest(text=text):
                cfg = self.write("okf.yml", text)
                with self.assertRaises(OkfError):
                    config.Bundle(cfg, repo_root=self.repo)

    def test_merge_replaces_lists_without_mutating_input(self):
        base = {"types": ["A"], "log": {"layers": ["api"], "paths": {"api": "a.md"}}}
        merged = config.merge_config(base, {"types": ["B"], "log": {"paths": {"api": "b.md"}}})
        self.assertEqual(merged["types"], ["B"])
        self.assertEqual(merged["log"]["layers"], ["api"])
        self.assertEqual(base["log"]["paths"]["api"], "a.md")
        self.assertIs(cli.merge_config, config.merge_config)
