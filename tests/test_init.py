"""`okf init` と、新しく入った設定マージ / ルート探索の検証。"""

from __future__ import annotations

import contextlib
import io
import os
import unittest
from pathlib import Path

from helpers import OkfTestCase, ns
from okf_devkit import cli as okf


def init_args(**kwargs) -> object:
    base = dict(bundle_root="docs", site_name=None, layer=None, force=False)
    base.update(kwargs)
    return ns(**base)


def run_init(**kwargs) -> str:
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        code = okf.cmd_init(init_args(**kwargs))
    assert code == 0, code
    return out.getvalue()


class MergeConfigTests(unittest.TestCase):
    def test_dicts_merge_recursively(self) -> None:
        merged = okf.merge_config(
            {"log": {"heading_prefix": "H", "paths": {"a": "a.md"}}},
            {"log": {"paths": {"b": "b.md"}}},
        )
        self.assertEqual("H", merged["log"]["heading_prefix"])
        self.assertEqual({"a": "a.md", "b": "b.md"}, merged["log"]["paths"])

    def test_lists_are_replaced_not_appended(self) -> None:
        # 追記にすると「既定の語彙を減らせない」ため、置換が正しい挙動。
        merged = okf.merge_config({"types": ["A", "B"]}, {"types": ["C"]})
        self.assertEqual(["C"], merged["types"])

    def test_override_does_not_mutate_base(self) -> None:
        base = {"index": {"root_heading": "orig"}}
        okf.merge_config(base, {"index": {"root_heading": "new"}})
        self.assertEqual("orig", base["index"]["root_heading"])

    def test_defaults_file_ships_with_the_package(self) -> None:
        self.assertTrue(okf.DEFAULTS_PATH.is_file(), okf.DEFAULTS_PATH)


class FindProjectRootTests(OkfTestCase):
    def test_finds_nearest_ancestor_with_config(self) -> None:
        (self.repo / "okf.yml").write_text("bundle_root: docs\n", encoding="utf-8")
        deep = self.repo / "a" / "b" / "c"
        deep.mkdir(parents=True)
        self.assertEqual(self.repo, okf.find_project_root(deep))

    def test_falls_back_to_start_when_nothing_found(self) -> None:
        # git リポジトリでも okf.yml でもない場所では起点をそのまま返す
        # （init は設定が無い状態から動く必要があるため、ここで落とさない）。
        deep = self.repo / "x"
        deep.mkdir()
        found = okf.find_project_root(deep)
        self.assertIn(found, (deep, self.repo, Path(os.getcwd()).resolve()))


class InitTests(OkfTestCase):
    def test_creates_config_bundle_templates_and_hooks(self) -> None:
        run_init(site_name="Demo", layer=["client=app/client/**"])

        for rel in (
            "okf.yml",
            "docs/AGENTS.md",
            "docs/CONVENTIONS.md",
            "docs/_templates/reference.md",
            "docs/client/log.md",
            "docs/project/log.md",
            ".okf/hooks/render_hook.sh",
            ".okf/hooks/render_hook.ps1",
        ):
            self.assertTrue((self.repo / rel).exists(), rel)

    def test_generated_config_parses_and_keeps_defaults(self) -> None:
        run_init(site_name="Demo", layer=["client=app/client/**", "server=app/server/**"])

        bundle = okf.Bundle(self.repo / "okf.yml")
        self.assertEqual("Demo", bundle.site_name)
        self.assertEqual(["client", "server", "shared"], bundle.layers)
        # 書いていない語彙は defaults.yml から継承される
        self.assertIn("Decision Record", bundle.types)
        self.assertEqual(["draft", "stable", "deprecated"], bundle.statuses)
        self.assertEqual("client/log.md", bundle.log_cfg["paths"]["client"])
        self.assertEqual([("app/client/**", "client"), ("app/server/**", "server")],
                         [(m["glob"], m["layer"]) for m in bundle.cfg["layer_map"][:2]])

    def test_freshly_initialised_bundle_lints_clean(self) -> None:
        run_init(site_name="Demo", layer=["client=app/client/**"])
        bundle = okf.Bundle(self.repo / "okf.yml")

        with contextlib.redirect_stdout(io.StringIO()):
            okf.cmd_index(bundle, ns(write=True, check=False, quiet=True))
            code = okf.cmd_lint(bundle, ns(strict=False))

        self.assertEqual(0, code, "init 直後の lint は error 0 であること")

    def test_existing_files_are_kept_unless_force(self) -> None:
        run_init(layer=["client=app/client/**"])
        (self.repo / "okf.yml").write_text("# 手で編集済み\n", encoding="utf-8")

        out = run_init(layer=["client=app/client/**"])
        self.assertIn("スキップ", out)
        self.assertEqual("# 手で編集済み\n",
                         (self.repo / "okf.yml").read_text(encoding="utf-8"))

        run_init(layer=["client=app/client/**"], force=True)
        self.assertIn("bundle_root", (self.repo / "okf.yml").read_text(encoding="utf-8"))

    def test_layer_spec_supports_explicit_directory(self) -> None:
        run_init(layer=["api=src/api/**:server"])
        bundle = okf.Bundle(self.repo / "okf.yml")
        self.assertEqual("server", bundle.cfg["layer_dirs"]["api"])
        self.assertTrue((self.repo / "docs/server/log.md").exists())

    def test_rejects_invalid_layer_specs(self) -> None:
        for spec in ("client", "=app/**", "client=", "Client=app/**", "shared=app/**"):
            with self.subTest(spec=spec), self.assertRaises(okf.OkfError):
                okf.cmd_init(init_args(layer=[spec]))

    def test_rejects_duplicate_layers(self) -> None:
        with self.assertRaises(okf.OkfError):
            okf.cmd_init(init_args(layer=["a=x/**", "a=y/**"]))

    def test_rejects_bundle_root_escaping_the_project(self) -> None:
        for bad in ("../outside", "/abs", "", "."):
            with self.subTest(bundle_root=bad), self.assertRaises(okf.OkfError):
                okf.cmd_init(init_args(bundle_root=bad))

    def test_custom_bundle_root_is_honoured(self) -> None:
        run_init(bundle_root="knowledge", layer=["client=app/client/**"])
        self.assertTrue((self.repo / "knowledge/AGENTS.md").exists())
        bundle = okf.Bundle(self.repo / "okf.yml")
        self.assertEqual((self.repo / "knowledge").resolve(), bundle.root)
        # bundle_root を変えたら layer_map の skip も追従すること
        globs = [m["glob"] for m in bundle.cfg["layer_map"]]
        self.assertIn("knowledge/**", globs)

    def test_scaffold_tokens_are_fully_expanded(self) -> None:
        run_init(bundle_root="knowledge", site_name="Demo", layer=["client=app/client/**"])
        for rel in ("knowledge/AGENTS.md", "knowledge/CONVENTIONS.md"):
            text = (self.repo / rel).read_text(encoding="utf-8")
            self.assertNotIn("{{", text, rel)
            self.assertIn("knowledge/", text, rel)


if __name__ == "__main__":
    unittest.main()
