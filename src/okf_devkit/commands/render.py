"""HTML rendering entry preserving renderer/cleanup owners and browser behavior."""
from __future__ import annotations
import sys
import webbrowser
from pathlib import Path
from ..config import Bundle
from ..doc import Doc
from ..errors import OkfError

def cmd_render(bundle: Bundle, args, *, repo_root: Path | None = None, doc_factory=None) -> int:
    """Bundle 対象の Markdown を、AI を使わず閲覧用 HTML に変換する。"""
    repo_root = bundle.repo_root if repo_root is None else repo_root

    def read_doc(path, bundle_root):
        return (Doc if doc_factory is None else doc_factory)(path, bundle_root, repo_root=repo_root)

    try:
        from ..renderer import RenderError, render_bundle
    except ImportError as exc:  # pragma: no cover - 壊れたインストール向け
        raise OkfError(f"HTML レンダラーを読み込めません: {exc}") from exc

    cleanup_from = getattr(args, "cleanup_from", None)
    if cleanup_from and args.hook:
        raise OkfError("--cleanup-from cannot be combined with --hook")
    output_root = repo_root / (args.output or "_site")
    if not cleanup_from:
        output_root = output_root.resolve()
    try:
        output_root.relative_to(repo_root.resolve())
    except ValueError as exc:
        raise OkfError("HTML の出力先はリポジトリ内に指定してください") from exc

    try:
        from ..render_cleanup import execute_cleanup, plan_cleanup, validate_roots, write_manifest
        moves = []
        if cleanup_from:
            old_root, output_root = validate_roots(repo_root, repo_root / cleanup_from, output_root)
            old_plan = render_bundle(bundle, read_doc, old_root, write=False)
            new_plan = render_bundle(bundle, read_doc, output_root, write=False)
            moves, lines = plan_cleanup(repo_root, old_root, output_root, old_plan.artifacts, new_plan.artifacts)
            for line in lines:
                print(line)
        report = render_bundle(
            bundle,
            read_doc,
            output_root,
            write=not args.check,
            remove_stale=not bool(cleanup_from),
        )
        if not args.check:
            write_manifest(repo_root, output_root, report.artifacts)
            if cleanup_from:
                backup = execute_cleanup(repo_root, old_root, output_root, moves)
                if backup:
                    print(f"cleanup backup: {backup.relative_to(repo_root.resolve()).as_posix()}")
    except (RenderError, OSError) as exc:
        raise OkfError(str(exc)) from exc

    if args.hook:
        # Codex / Claude の Stop hook は exit 0 時に JSON を要求する。
        # 追加コンテキストや block 指示は返さず、モデル継続を発生させない。
        print("{}")
        return 0

    for warning in report.warnings:
        print(f"warn: {warning}", file=sys.stderr)
    mode = "検証" if args.check else "生成"
    print(
        f"HTML {mode}: {report.pages} ページ / 書き込み {report.written} 件 / "
        f"削除 {report.removed} 件 / "
        f"warn {len(report.warnings)} 件 -> {report.output_root}"
    )
    if getattr(args, "open", False) and not args.check:
        homepage = (report.output_root / "index.html").resolve()
        if not homepage.is_file():
            print(f"warn: トップページがありません: {homepage}", file=sys.stderr)
        else:
            try:
                opened = webbrowser.open(homepage.as_uri())
            except (OSError, webbrowser.Error):
                opened = False
            if not opened:
                print(f"warn: ブラウザを開けません: {homepage.as_uri()}", file=sys.stderr)
    return 0
