"""Changed-path mapping using the bundle project root and pure glob matching."""
from __future__ import annotations
from ..config import Bundle
from .. import gitutil
from ..fsutil import path_matches
from .log import layer_of

def compute_affected(bundle: Bundle, paths: list[str]) -> tuple[dict[str, list[str]], list[str]]:
    """変更パス → 更新すべきドキュメントの対応表と、未カバーのパスを返す。"""
    mapping: dict[str, list[str]] = {}
    covered: set[str] = set()
    for doc in bundle.docs():
        resources = doc.code_globs()
        if not resources:
            continue
        hits = []
        for path in paths:
            if any(path == r.lstrip("/") or path_matches(path, r.lstrip("/")) for r in resources):
                hits.append(path)
        if hits:
            mapping[doc.repo_rel] = sorted(set(hits))
            covered.update(hits)
    uncovered = sorted(p for p in paths if p not in covered)
    return mapping, uncovered


def cmd_affected(bundle: Bundle, args, *, runner=None, path_provider=None) -> int:
    paths = list(args.paths) if args.paths else (gitutil.changed_paths(bundle.repo_root, args.base, runner=runner) if path_provider is None else path_provider(args.base))
    # layer_map で skip 指定のパス（docs/** など）は対象外にする
    paths = [
        p.replace("\\", "/")
        for p in paths
        if not p.endswith("/") and layer_of(bundle, p.replace("\\", "/")) is not None
    ]
    if not paths:
        print("変更パスがありません。")
        return 0
    mapping, uncovered = compute_affected(bundle, paths)
    for doc_path in sorted(mapping):
        print(f"{doc_path}  <- {', '.join(mapping[doc_path])}")
    if not mapping:
        print("更新すべきドキュメントは見つかりませんでした。")
    if uncovered:
        print("\n未カバー:")
        for path in uncovered:
            print(f"  {path}")
    return 0
