"""Index generation and marker preflight for a bundle-owned project root."""
from __future__ import annotations
import os
import re
import sys
from pathlib import Path
from ..config import Bundle
from ..doc import Doc
from ..errors import MarkerError
from ..fsutil import extract_date, read_text, rel_posix, write_if_changed

def md_escape_label(text: str) -> str:
    """Markdown のリンクラベルとして安全な文字列にする。"""
    cleaned = re.sub(r"\s*[\r\n]+\s*", " ", str(text)).strip()
    return cleaned.replace("\\", "\\\\").replace("[", "\\[").replace("]", "\\]")


def md_escape_link(link: str) -> str:
    """Markdown のリンク先として安全な文字列にする。"""
    cleaned = re.sub(r"\s*[\r\n]+\s*", "", str(link)).strip()
    return (
        cleaned.replace("%", "%25")
        .replace("(", "%28")
        .replace(")", "%29")
        .replace(" ", "%20")
    )


def md_escape_text(text: str) -> str:
    """説明文として安全な 1 行文字列にする。"""
    return re.sub(r"\s*[\r\n]+\s*", " ", str(text)).strip()


def _entry_line(title: str, link: str, description: str, extra: str = "") -> str:
    parts = f"* [{md_escape_label(title)}]({md_escape_link(link)})"
    tail = " - ".join(md_escape_text(x) for x in (extra, description) if x)
    return f"{parts} - {tail}" if tail else parts


def _index_link(bundle: Bundle, directory: Path, target: Path) -> str:
    """index.md の場所を起点に、設定された形式のリンク先を返す。"""
    if bundle.index_link_style == "bundle-absolute":
        return "/" + rel_posix(target, bundle.root)

    index_dir = (directory / "index.md").parent.resolve()
    relative = Path(os.path.relpath(target.resolve(), index_dir)).as_posix()
    if not relative.startswith((".", "/")):
        relative = "./" + relative
    return relative


def _display_title(doc: Doc) -> str:
    title = doc.title
    if doc.status == "draft":
        title += " (draft)"
    return title


def build_index_block(bundle: Bundle, directory: Path) -> str:
    """1 ディレクトリ分の自動生成ブロック（マーカーの内側）を作る。"""
    if directory.resolve() == bundle.backlog_dir().resolve():
        return build_backlog_block(bundle, directory)

    icfg = bundle.index_cfg
    sections: list[tuple[str, list[str]]] = []

    # サブディレクトリ（その index.md を 1 エントリとして表現する＝段階的開示）
    subdir_lines = []
    for sub in sorted(p for p in directory.iterdir() if p.is_dir()):
        if sub.name.startswith(("_", ".")) or bundle.is_excluded(sub):
            continue
        idx = sub / "index.md"
        # index.md が未生成でも同じ結果になるよう、既定値は render_index の見出しと揃える
        title = f"{sub.name}{icfg.get('heading_suffix', ' ドキュメント')}"
        if idx.exists():
            doc = Doc(idx, bundle.root, repo_root=bundle.repo_root)
            title = doc.h1 or title
        link = _index_link(bundle, directory, idx)
        subdir_lines.append(_entry_line(title, link, ""))
    if subdir_lines:
        sections.append((str(icfg.get("subdir_section", "ディレクトリ")), sorted(subdir_lines)))

    # 直下の非予約ファイル
    docs: list[Doc] = []
    for p in sorted(directory.iterdir()):
        if not (p.is_file() and p.suffix == ".md"):
            continue
        if p.name in bundle.reserved or bundle.is_excluded(p):
            continue
        docs.append(Doc(p, bundle.root, repo_root=bundle.repo_root))

    deprecated = [d for d in docs if d.status == "deprecated"]
    active = [d for d in docs if d.status != "deprecated"]

    def lines_for(items: list[Doc]) -> list[str]:
        items = sorted(items, key=lambda d: (d.title, d.bundle_rel))
        return [
            _entry_line(_display_title(d), _index_link(bundle, directory, d.path), d.description)
            for d in items
        ]

    for type_name in bundle.types:
        group = [d for d in active if d.type == type_name]
        if group:
            sections.append((type_name, lines_for(group)))

    others = [d for d in active if d.type not in bundle.types]
    if others:
        sections.append((str(icfg.get("other_section", "その他")), lines_for(others)))

    if deprecated:
        sections.append((str(icfg.get("deprecated_section", "非推奨")), lines_for(deprecated)))

    if not sections:
        return ""
    blocks = [f"## {name}\n" + "\n".join(lines) for name, lines in sections]
    return "\n\n".join(blocks) + "\n"


def build_backlog_block(bundle: Bundle, directory: Path) -> str:
    """backlog/index.md 用のブロック（state でグルーピング + 件数サマリ）。"""
    bcfg = bundle.backlog_cfg
    state_order = list(bcfg.get("state_order") or ["doing", "todo", "done", "dropped"])
    prio_order = list(bcfg.get("priorities") or ["high", "medium", "low"])

    docs = [
        Doc(p, bundle.root, repo_root=bundle.repo_root)
        for p in sorted(directory.iterdir())
        if p.is_file() and p.suffix == ".md" and p.name not in bundle.reserved and not bundle.is_excluded(p)
    ]

    by_state: dict[str, list[Doc]] = {s: [] for s in state_order}
    for d in docs:
        state = str(d.fm.get("state") or "todo")
        by_state.setdefault(state, []).append(d)

    # 件数サマリ表（doing / todo / done / dropped の順）
    summary = ["| state | 件数 |", "|---|---|"]
    for state in state_order:
        summary.append(f"| {state} | {len(by_state.get(state, []))} |")
    for state in sorted(by_state):
        if state not in state_order:
            summary.append(f"| {state} | {len(by_state[state])} |")

    def prio_key(d: Doc) -> tuple:
        prio = str(d.fm.get("priority") or "")
        rank = prio_order.index(prio) if prio in prio_order else len(prio_order)
        return (rank, d.title, d.bundle_rel)

    def meta(d: Doc) -> str:
        chips = [f"`{d.fm[k]}`" for k in ("priority", "effort") if d.fm.get(k)]
        return " ".join(chips)

    sections: list[str] = ["\n".join(summary)]
    for state in state_order + sorted(s for s in by_state if s not in state_order):
        items = by_state.get(state) or []
        if not items:
            continue
        if state == "done":
            items = sorted(
                items,
                key=lambda d: (extract_date(d.fm.get("done_at")) or "", d.title),
                reverse=True,
            )
            lines = [
                _entry_line(
                    _display_title(d),
                    _index_link(bundle, directory, d.path),
                    d.description,
                    f"{extract_date(d.fm.get('done_at')) or '日付不明'} 完了",
                )
                for d in items
            ]
        else:
            items = sorted(items, key=prio_key)
            lines = [
                _entry_line(
                    _display_title(d),
                    _index_link(bundle, directory, d.path),
                    d.description,
                    meta(d),
                )
                for d in items
            ]
        sections.append(f"## {state}\n" + "\n".join(lines))

    return "\n\n".join(sections) + "\n"


def split_markers(text: str, start: str, end: str, where: str) -> tuple[str, str] | None:
    """自動生成マーカーを検証し、(前文, 後文) を返す。マーカーが無ければ None。

    許可するのは次の 2 通りだけ。それ以外は ``MarkerError`` にして
    **一切書き込まない**（壊れたまま実行し続けると内容が増殖するため）。

    * start / end がどちらも 0 個 → 末尾に新規追加（None を返す）
    * start / end がちょうど 1 個ずつで start が end より前 → その間を置換
    """
    n_start = text.count(start)
    n_end = text.count(end)
    if n_start == 0 and n_end == 0:
        return None
    if n_start == 1 and n_end == 1:
        i_start = text.index(start)
        i_end = text.index(end)
        if i_start < i_end:
            return text[:i_start], text[i_end + len(end):]
        raise MarkerError(
            f"{where}: 自動生成マーカーの順序が逆です（`{end}` が `{start}` より前にあります）。"
            " 手で修正してから再実行してください。"
        )
    if n_start == 0 or n_end == 0:
        missing, present = (start, end) if n_start == 0 else (end, start)
        raise MarkerError(
            f"{where}: 自動生成マーカー `{missing}` がありません（`{present}` は {max(n_start, n_end)} 個あります）。"
            " 片方だけのマーカーは自動修復できません。手で修正してから再実行してください。"
        )
    raise MarkerError(
        f"{where}: 自動生成マーカーが重複しています（start {n_start} 個 / end {n_end} 個）。"
        " 1 組だけ残るように手で修正してから再実行してください。"
    )


def render_index(bundle: Bundle, directory: Path, block: str, *, repo_root: Path | None = None) -> str:
    """既存 index.md のマーカー間だけを置換した全文を返す。"""
    repo_root = bundle.repo_root if repo_root is None else repo_root
    icfg = bundle.index_cfg
    start = str(icfg.get("start_marker", "<!-- okf:auto:start -->"))
    end = str(icfg.get("end_marker", "<!-- okf:auto:end -->"))
    auto = f"{start}\n{block}{end}\n"

    index_path = directory / "index.md"
    is_root = directory.resolve() == bundle.root.resolve()

    if not index_path.exists():
        head = ""
        if is_root:
            head = f'---\nokf_version: "{icfg.get("okf_version", "0.2")}"\n---\n\n'
            heading = str(icfg.get("root_heading", "ドキュメント"))
        else:
            heading = f"{directory.name}{icfg.get('heading_suffix', ' ドキュメント')}"
        return f"{head}# {heading}\n\n{auto}"

    text = read_text(index_path)
    where = rel_posix(index_path, repo_root)
    parts = split_markers(text, start, end, where)
    if parts is not None:
        pre, post = parts
        return f"{pre}{auto[:-1]}{post}"
    # マーカーが無ければ末尾に追加する
    return text.rstrip("\n") + "\n\n" + auto


def _plan_index(bundle: Bundle, *, repo_root: Path | None = None) -> tuple[list[tuple[Path, str]], list[MarkerError]]:
    """全ディレクトリ分の生成結果と、マーカー破損エラーをまとめて返す。"""
    plan: list[tuple[Path, str]] = []
    errors: list[MarkerError] = []
    for directory in bundle.dirs():
        try:
            block = build_index_block(bundle, directory)
            content = render_index(bundle, directory, block, repo_root=repo_root)
        except MarkerError as exc:
            errors.append(exc)
            continue
        plan.append((directory / "index.md", content))
    return plan, errors


def cmd_index(bundle: Bundle, args, *, repo_root: Path | None = None, writer=None) -> int:
    repo_root = bundle.repo_root if repo_root is None else repo_root
    plan, marker_errors = _plan_index(bundle, repo_root=repo_root)
    if marker_errors:
        # 1 件でも壊れていたら「どのファイルも書かない」。
        print("index.md の自動生成マーカーが壊れています。書き込みを中止しました:", file=sys.stderr)
        for exc in marker_errors:
            print(f"  {exc}", file=sys.stderr)
        return 1

    changed: list[str] = []
    for index_path, content in plan:
        current = read_text(index_path) if index_path.exists() else None
        if current == content:
            continue
        changed.append(rel_posix(index_path, repo_root))
        if args.write:
            (write_if_changed if writer is None else writer)(index_path, content)

    if args.check:
        if changed:
            print("index.md が最新ではありません:")
            for path in changed:
                print(f"  {path}")
            return 1
        if not args.quiet:
            print("index.md はすべて最新です。")
        return 0

    if changed:
        verb = "更新しました" if args.write else "更新が必要です（--write で書き込み）"
        print(f"index.md を {len(changed)} 件 {verb}:")
        for path in changed:
            print(f"  {path}")
    elif not args.quiet:
        print("index.md はすべて最新です。")
    return 0
