"""Changed-path mapping using the bundle project root and pure glob matching."""
from __future__ import annotations
import sys
from ..code_sources import split_code_glob
from ..config import Bundle
from .. import gitutil
from ..errors import OkfError
from ..fsutil import path_matches
from .log import layer_of


def compute_affected(bundle: Bundle, paths: list[str], *, source: str | None = None) -> tuple[dict[str, list[str]], list[str]]:
    """変更パス → 更新すべきドキュメントの対応表と、未カバーのパスを返す。"""
    mapping: dict[str, list[str]] = {}
    covered: set[str] = set()
    for doc in bundle.docs():
        resources = [
            pattern for name, pattern in map(split_code_glob, doc.code_globs())
            if name == source and pattern is not None
        ]
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
    source = getattr(args, "source", None)
    if source is not None:
        if not args.base or args.paths:
            raise OkfError("--source には --base を指定してください。--paths と併用できません")
        try:
            root = bundle.code_sources.root(source)
            paths = gitutil.changed_paths(root, args.base, require_history=True)
        except (OkfError, OSError) as exc:
            reason = str(exc) if isinstance(exc, OkfError) else "外部 Git を実行できませんでした"
            print(f"[okf affected] 警告: ソース `{source}` の差分未確認。{reason}", file=sys.stderr)
            return 0
    else:
        base = "main" if args.base is None else args.base
        if args.paths:
            paths = list(args.paths)
        elif path_provider is None:
            paths = gitutil.changed_paths(bundle.repo_root, base, runner=runner)
        else:
            paths = path_provider(base)
    paths = [p.replace("\\", "/") for p in paths if not p.endswith("/")]
    if source is None:
        paths = [p for p in paths if layer_of(bundle, p) is not None]
    if not paths:
        print("変更パスがありません。")
        return 0
    mapping, uncovered = compute_affected(bundle, paths, source=source)
    for doc_path in sorted(mapping):
        print(f"{doc_path}  <- {', '.join(mapping[doc_path])}")
    if not mapping:
        print("更新すべきドキュメントは見つかりませんでした。")
    if uncovered:
        print("\n未カバー:")
        for path in uncovered:
            print(f"  {path}")
    return 0
