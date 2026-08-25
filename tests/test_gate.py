"""sync --gate: lint error 内容ごとの回数管理と fail-open 防止。"""

from __future__ import annotations

import contextlib
import io
import unittest

from helpers import OkfTestCase, doc_text, ns
from okf_devkit import cli as okf


def quiet(fn, *args) -> int:
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        return fn(*args)


class GateBumpTest(OkfTestCase):
    def setUp(self):
        super().setUp()
        self.git_init()

    def test_counts_per_fingerprint(self):
        self.assertEqual(1, okf.gate_bump("s1", "aaa"))
        self.assertEqual(2, okf.gate_bump("s1", "aaa"))
        self.assertEqual(1, okf.gate_bump("s1", "bbb"), "別のエラー内容ではリセットされる")
        self.assertEqual(2, okf.gate_bump("s1", "bbb"))

    def test_success_resets(self):
        self.assertEqual(1, okf.gate_bump("s1", "aaa"))
        self.assertEqual(0, okf.gate_bump("s1", None))
        self.assertEqual(1, okf.gate_bump("s1", "aaa"), "正常終了後は数え直す")

    def test_sessions_are_isolated(self):
        self.assertEqual(1, okf.gate_bump("s1", "aaa"))
        self.assertEqual(1, okf.gate_bump("s2", "aaa"), "別セッションは互いに影響しない")
        self.assertEqual(2, okf.gate_bump("s1", "aaa"))

    def test_state_is_outside_the_worktree(self):
        okf.gate_bump("s1", "aaa")
        status = self.git("status", "--porcelain")
        self.assertEqual("", status.strip(), "gate 状態ファイルが作業ツリーを dirty にしてはいけない")
        self.assertFalse(okf._has_local_changes())


class GateSyncTest(OkfTestCase):
    """cmd_sync --gate の end-to-end。"""

    def setUp(self):
        super().setUp()
        self.git_init()
        self.write("docs/.keep", "")
        self.sha = self.commit("初期", {"code/a.ts": "x\n"})

    def sync(self, session="s1") -> int:
        self.reset_caches()
        return quiet(okf.cmd_sync, self.bundle(baseline=self.sha),
                     ns(gate=True, session_id=session))

    def test_clean_bundle_returns_zero(self):
        self.write("docs/a.md", doc_text(title="A", layer="shared", code_globs=None))
        self.assertEqual(0, self.sync())

    def test_error_returns_two_then_zero_on_repeat(self):
        self.write("docs/a.md", doc_text(type_="Nope", title="A", layer="shared", code_globs=None))
        self.assertEqual(2, self.sync(), "1 回目は差し戻す")
        self.assertEqual(0, self.sync(), "同じ内容の 2 回目は警告のみ")

    def test_new_error_after_success_is_still_blocked(self):
        """レビュー Critical 3: 正常な Stop の後でも新規違反を差し戻せること。"""
        self.write("docs/a.md", doc_text(title="A", layer="shared", code_globs=None))
        self.assertEqual(0, self.sync(), "まず正常終了する")

        self.write("docs/b.md", doc_text(type_="Nope", title="B", layer="shared", code_globs=None))
        self.assertEqual(2, self.sync(), "その後の新規違反は必ず差し戻す")

    def test_different_error_resets_the_counter(self):
        self.write("docs/a.md", doc_text(type_="Nope", title="A", layer="shared", code_globs=None))
        self.assertEqual(2, self.sync())
        self.assertEqual(0, self.sync())

        self.write("docs/b.md", doc_text(title="B", layer="nope", code_globs=None))
        self.assertEqual(2, self.sync(), "エラー内容が変われば再度差し戻す")

    def test_operational_error_fails_closed(self):
        """git 不在・設定不備などの運用エラーで gate をすり抜けさせない。"""
        rc = quiet(okf.main, ["--config", str(self.repo / "missing.yml"), "sync", "--gate"])
        self.assertEqual(2, rc)

    def test_operational_error_without_gate_is_one(self):
        rc = quiet(okf.main, ["--config", str(self.repo / "missing.yml"), "lint"])
        self.assertEqual(1, rc)


class StdinTest(unittest.TestCase):
    def test_session_id_from_argument(self):
        self.assertEqual("abc", okf.resolve_session_id(ns(session_id="abc")))

    def test_session_id_from_env(self):
        import os
        os.environ["OKF_SESSION_ID"] = "from-env"
        try:
            self.assertEqual("from-env", okf.resolve_session_id(ns(session_id=None)))
        finally:
            del os.environ["OKF_SESSION_ID"]

    def test_stdin_read_times_out_instead_of_hanging(self):
        """writer が EOF を送らなくてもハングしないこと。"""
        import os
        import sys
        import time

        read_fd, write_fd = os.pipe()  # 書き手を開いたままにする（EOF が来ない状況）
        original = sys.stdin
        stream = os.fdopen(read_fd, "r")
        try:
            sys.stdin = stream
            start = time.monotonic()
            result = okf._read_stdin_json(timeout=0.3)
            elapsed = time.monotonic() - start
        finally:
            sys.stdin = original
            os.close(write_fd)  # 先に EOF を渡して読み取りスレッドを解放する
            time.sleep(0.1)
            try:
                stream.close()
            except Exception:
                pass
        self.assertIsNone(result)
        self.assertLess(elapsed, 3.0, "stdin 読み取りでハングしてはいけない")


class FingerprintTest(unittest.TestCase):
    def test_order_independent(self):
        a = okf.Finding("a.md", 1, "error", "L2", "x")
        b = okf.Finding("b.md", 2, "error", "L3", "y")
        self.assertEqual(okf.findings_fingerprint([a, b]), okf.findings_fingerprint([b, a]))

    def test_content_sensitive(self):
        a = okf.Finding("a.md", 1, "error", "L2", "x")
        c = okf.Finding("a.md", 1, "error", "L2", "z")
        self.assertNotEqual(okf.findings_fingerprint([a]), okf.findings_fingerprint([c]))


if __name__ == "__main__":
    unittest.main()
