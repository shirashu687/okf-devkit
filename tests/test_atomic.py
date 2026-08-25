"""原子的書き込み: 失敗時に元ファイルを壊さないこと。"""

from __future__ import annotations

import os
import unittest

from helpers import OkfTestCase
from okf_devkit import cli as okf


class AtomicWriteTest(OkfTestCase):
    def test_writes_and_leaves_no_temp_files(self):
        target = self.repo / "out" / "a.txt"
        okf.atomic_write_bytes(target, "こんにちは".encode("utf-8"))
        self.assertEqual("こんにちは", target.read_text(encoding="utf-8"))
        leftovers = [p.name for p in target.parent.iterdir() if p.name != "a.txt"]
        self.assertEqual([], leftovers, "一時ファイルが残ってはいけない")

    def test_failure_keeps_original_intact(self):
        target = self.repo / "a.txt"
        target.write_text("元の内容", encoding="utf-8")

        original_replace = os.replace

        def boom(src, dst):
            raise PermissionError(32, "共有違反（テスト）")

        os.replace = boom
        try:
            with self.assertRaises(okf.OkfError):
                okf.atomic_write_bytes(target, b"new", retries=2)
        finally:
            os.replace = original_replace

        self.assertEqual("元の内容", target.read_text(encoding="utf-8"),
                         "置換に失敗しても元ファイルは無傷であるべき")
        leftovers = [p.name for p in self.repo.iterdir() if p.name.endswith(".okftmp")]
        self.assertEqual([], leftovers, "失敗時も一時ファイルを残さない")

    def test_write_error_does_not_truncate(self):
        """書き込み中のエラーでも対象ファイルは truncate されない。"""
        target = self.repo / "a.txt"
        target.write_text("元の内容", encoding="utf-8")

        class Exploding(bytes):
            pass

        original_fdopen = os.fdopen

        def failing_fdopen(fd, mode, *a, **kw):
            handle = original_fdopen(fd, mode, *a, **kw)
            original_write = handle.write

            def write(data):
                original_write(data[: len(data) // 2])
                raise OSError(28, "No space left on device（テスト）")

            handle.write = write
            return handle

        os.fdopen = failing_fdopen
        try:
            with self.assertRaises(OSError):
                okf.atomic_write_bytes(target, b"x" * 100)
        finally:
            os.fdopen = original_fdopen

        self.assertEqual("元の内容", target.read_text(encoding="utf-8"))

    def test_write_if_changed_skips_identical_content(self):
        target = self.repo / "a.txt"
        self.assertTrue(okf.write_if_changed(target, "same\n"))
        mtime = target.stat().st_mtime_ns
        self.assertFalse(okf.write_if_changed(target, "same\n"))
        self.assertEqual(mtime, target.stat().st_mtime_ns, "内容が同じなら触らない")

    def test_crlf_is_normalized(self):
        target = self.repo / "a.txt"
        okf.write_if_changed(target, "a\r\nb\r\n")
        self.assertEqual(b"a\nb\n", target.read_bytes())


if __name__ == "__main__":
    unittest.main()
