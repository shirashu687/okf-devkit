"""Ownership and compatibility checks for stage1 extraction."""
from __future__ import annotations

from unittest.mock import patch
from helpers import OkfTestCase
from okf_devkit import cli, errors, fsutil


class PureHelperOwnershipTest(OkfTestCase):
    def test_legacy_exports_share_exception_and_function_identities(self):
        self.assertIs(cli.OkfError, errors.OkfError)
        self.assertIs(cli.MarkerError, errors.MarkerError)
        self.assertTrue(issubclass(cli.MarkerError, errors.OkfError))
        for name in ["rel_posix", "read_text", "atomic_write_bytes", "write_if_changed", "today", "now_iso", "is_iso_date", "extract_date", "parse_datetime", "glob_to_regex", "path_matches"]:
            self.assertIs(getattr(cli, name), getattr(fsutil, name), name)
        self.assertIs(cli.ISO_DATE_RE, fsutil.ISO_DATE_RE)
        self.assertIs(cli._GLOB_CACHE, fsutil._GLOB_CACHE)

    def test_legacy_glob_call_uses_new_owner_and_shared_cache_clear(self):
        pattern = "src/**/*.py"
        with patch.object(fsutil, "glob_to_regex", wraps=fsutil.glob_to_regex) as compile_glob:
            self.assertTrue(cli.path_matches("src/a.py", pattern))
            self.assertTrue(cli.path_matches("src/nested/b.py", pattern))
            compile_glob.assert_called_once_with(pattern)
            cli._GLOB_CACHE.clear()
            self.assertTrue(cli.path_matches("src/c.py", pattern))
            self.assertEqual(2, compile_glob.call_count)

    def test_new_owner_failure_is_caught_by_existing_cli_exception(self):
        target = self.write("original.txt", "original")
        with patch.object(fsutil.os, "replace", side_effect=PermissionError("locked")), patch.object(fsutil.time, "sleep"):
            with self.assertRaises(cli.OkfError):
                fsutil.atomic_write_bytes(target, b"replacement", retries=2)
        self.assertEqual("original", target.read_text(encoding="utf8"))
        self.assertEqual([], list(self.repo.glob("*.okftmp")))
