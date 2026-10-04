"""Public entry metadata and independently owned live compatibility state."""
from __future__ import annotations

import argparse
import datetime
import inspect
import json
import os
import pickle
import time
import typing
import webbrowser
from pathlib import Path

from helpers import OkfTestCase, doc_text
from okf_devkit import cli, errors, yamlio


class CliFacadeTest(OkfTestCase):
    def test_entry_is_readable_small_and_keeps_top_level_legacy_classes(self):
        import ast
        source = Path(cli.__file__).read_text(encoding="utf-8")
        self.assertLessEqual(len(source.splitlines()), 200)
        tree = ast.parse(source)
        self.assertEqual({"Doc", "Bundle"}, {n.name for n in tree.body if isinstance(n, ast.ClassDef)})
        self.assertIs(cli.argparse, argparse)
        self.assertIs(cli._dt, datetime)
        self.assertIs(cli.webbrowser, webbrowser)
        self.assertIs(cli.OkfError, errors.OkfError)
        self.assertIs(cli.MarkerError, errors.MarkerError)
        self.assertIs(cli.YamlSubsetError, yamlio.YamlSubsetError)

    def test_public_metadata_signatures_hints_and_pickle_lookup(self):
        for name in ("Doc", "Bundle", "git", "path_commit_times", "backlog_docs", "cmd_render", "build_parser", "main", "run"):
            value = getattr(cli, name)
            self.assertEqual(name, value.__name__)
            self.assertEqual("okf_devkit.cli", value.__module__)
            self.assertEqual(name, value.__qualname__)
            self.assertIs(value, pickle.loads(pickle.dumps(value)))
        signature = inspect.signature(cli.git)
        self.assertEqual(["args", "cwd"], list(signature.parameters))
        self.assertEqual(inspect.Parameter.VAR_POSITIONAL, signature.parameters["args"].kind)
        self.assertEqual(inspect.Parameter.KEYWORD_ONLY, signature.parameters["cwd"].kind)
        self.assertIsNone(signature.parameters["cwd"].default)
        self.assertEqual({"bundle": cli.Bundle, "return": list[cli.Doc]}, typing.get_type_hints(cli.backlog_docs))
        self.assertEqual({"rev_range": str | None, "exclude": str | None, "return": list[cli.Commit]}, typing.get_type_hints(cli.collect_commits))
        self.assertEqual({"return": cli.argparse.ArgumentParser}, typing.get_type_hints(cli.build_parser))
        self.make_config(name="okf.yml")
        path = self.write("docs/pickle.md", doc_text(type_="Convention", title="Pickled", layer="shared", code_globs=None))
        bundle = cli.Bundle()
        document = cli.Doc(path, bundle.root)
        restored = pickle.loads(pickle.dumps(document))
        self.assertIs(cli.Doc, type(restored))
        self.assertEqual("Pickled", restored.fm["title"])
        self.assertEqual(document.repo_rel, restored.repo_rel)
        self.assertIs(cli.Bundle, type(pickle.loads(pickle.dumps(bundle))))

    def namespaces(self, other):
        from okf_devkit import compat
        namespaces = []
        for root in (self.repo, other):
            ns = dict(vars(cli))
            ns.update(REPO_ROOT=root, _PATH_TIME_MAP=None, _PATH_TIME_ROOT=None)
            compat.install_legacy_exports(ns)
            namespaces.append(ns)
        return namespaces

    def test_installed_wrappers_use_late_callbacks_and_isolated_yaml_cache(self):
        other = self.repo / "other"
        other.mkdir()
        first, second = self.namespaces(other)
        first["git"] = lambda *args, **kwargs: (0, "?? first.txt\0")
        second["git"] = lambda *args, **kwargs: (0, "")
        self.assertTrue(first["_has_local_changes"]())
        self.assertFalse(second["_has_local_changes"]())
        first["git"] = lambda *args, **kwargs: (0, "")
        self.assertFalse(first["_has_local_changes"]())
        class Backend:
            def __init__(self, name):
                self.name = name
            def safe_load(self, text):
                return {"owner": self.name}
        first["_pyyaml"], second["_pyyaml"] = Backend("first"), Backend("second")
        self.assertEqual({"owner": "first"}, first["parse_yaml"]("x: y"))
        self.assertEqual({"owner": "second"}, second["parse_yaml"]("x: y"))
        first["_PATH_TIME_ROOT"], first["_PATH_TIME_MAP"] = self.repo.resolve(), {"first.txt": "2026-01-01"}
        second["_PATH_TIME_ROOT"], second["_PATH_TIME_MAP"] = other.resolve(), {"second.txt": "2026-01-02"}
        self.assertEqual({"first.txt": "2026-01-01"}, first["path_commit_times"]())
        self.assertEqual({"second.txt": "2026-01-02"}, second["path_commit_times"]())
        first["REPO_ROOT"] = other
        self.assertEqual({}, first["path_commit_times"]())
        self.assertEqual({"second.txt": "2026-01-02"}, second["path_commit_times"]())

    def test_installed_wrappers_keep_independent_live_ttl_and_scaffold(self):
        other = self.repo / "other"
        other.mkdir()
        first, second = self.namespaces(other)
        for index, ns in enumerate((first, second)):
            state = self.repo / (str(index) + ".json")
            state.write_text(json.dumps({"fingerprint": "same", "count": 1}), encoding="utf-8")
            os.utime(state, (time.time() - 10, time.time() - 10))
            ns["_gate_state_file"] = lambda session, state=state: state
            assets = self.repo / ("assets" + str(index))
            assets.mkdir()
            (assets / "owner.txt").write_text(str(index), encoding="utf-8")
            ns["SCAFFOLD_DIR"] = assets
        first["GATE_TTL"], second["GATE_TTL"] = 0, 3600
        self.assertEqual(1, first["gate_bump"](None, "same"))
        self.assertEqual(2, second["gate_bump"](None, "same"))
        self.assertEqual("0", first["_scaffold_text"]("owner.txt"))
        self.assertEqual("1", second["_scaffold_text"]("owner.txt"))
