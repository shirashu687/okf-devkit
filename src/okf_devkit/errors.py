"""Shared CLI exception identities; legacy cli exports remain available."""

class OkfError(Exception):
    """CLI が利用者に見せる想定のエラー。"""


class MarkerError(OkfError):
    """index.md の自動生成マーカーが壊れている。"""
