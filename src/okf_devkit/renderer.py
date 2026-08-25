"""OKF Markdown bundle を閲覧用 HTML に変換する決定的レンダラー。

Markdown を正本のまま保持し、Bundle 対象の全ページを HTML にミラーする。
生成 HTML 内の Bundle 内リンクだけを ``.html`` へ書き換えるため、ブラウザで
``file://`` として開いても HTML 間を移動できる。
"""

from __future__ import annotations

import hashlib
import html
import os
import posixpath
import re
import shutil
import tempfile
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath
from typing import Any, Callable
from urllib.parse import urlsplit, urlunsplit

try:
    from markdown_it import MarkdownIt
except ImportError:  # pragma: no cover - cmd_render が利用者向けメッセージに変換する
    MarkdownIt = None  # type: ignore[assignment]


ASSET_DIR = Path(__file__).resolve().parent / "assets"
AUTO_MARKER_RE = re.compile(r"^\s*<!--\s*okf:auto:(?:start|end)\s*-->\s*$", re.MULTILINE)
SAFE_TYPE_RE = re.compile(r"[^a-z0-9]+")
TEMPLATE_TOKEN_RE = re.compile(r"\{\{([A-Z0-9_]+)\}\}")
OWNERSHIP_MARKER = "<!-- okf-devkit-owned:v1 -->"


class RenderError(RuntimeError):
    """HTML 生成を完了できない場合のエラー。"""


@dataclass
class Heading:
    level: int
    title: str
    anchor: str


@dataclass
class Page:
    doc: Any
    source_rel: str
    output_rel: str
    tokens: list[Any] = field(default_factory=list)
    headings: list[Heading] = field(default_factory=list)
    body_html: str = ""
    char_count: int = 0
    outbound: set[str] = field(default_factory=set)


@dataclass
class RenderReport:
    pages: int
    written: int
    removed: int
    warnings: list[str]
    output_root: Path


def _asset_text(name: str) -> str:
    path = ASSET_DIR / name
    if not path.exists():
        raise RenderError(f"HTML アセットが見つかりません: {path}")
    return path.read_text(encoding="utf-8").replace("\r\n", "\n")


def _slug(text: str, used: dict[str, int]) -> str:
    normalized = unicodedata.normalize("NFKC", text).strip().lower()
    normalized = re.sub(r"[`*_~\[\](){}<>]", "", normalized)
    normalized = re.sub(r"[^\w\-\u3040-\u30ff\u3400-\u9fff]+", "-", normalized, flags=re.UNICODE)
    normalized = normalized.strip("-_") or "section"
    count = used.get(normalized, 0) + 1
    used[normalized] = count
    return normalized if count == 1 else f"{normalized}-{count}"


def _iter_tokens(tokens: list[Any]):
    for token in tokens:
        yield token
        children = getattr(token, "children", None)
        if children:
            yield from _iter_tokens(children)


def _type_class(type_name: str) -> str:
    value = SAFE_TYPE_RE.sub("-", type_name.lower()).strip("-")
    return value or "document"


def _trust_level(doc: Any) -> tuple[str, str]:
    verified = doc.get("verified", [])
    if not isinstance(verified, list) or not verified:
        return "unverified", "未検証"
    for entry in verified:
        if isinstance(entry, dict) and str(entry.get("by", "")).startswith("human:"):
            return "human-reviewed", "人間レビュー済み"
    return "machine-confirmed", "機械確認済み"


def _normalize_bundle_target(source_rel: str, href_path: str) -> str | None:
    """href のパスを Bundle ルート相対の POSIX パスへ解決する。"""
    if href_path.startswith("/"):
        candidate = href_path.lstrip("/")
    else:
        candidate = posixpath.join(posixpath.dirname(source_rel), href_path)
    if href_path.endswith("/"):
        candidate = posixpath.join(candidate, "index.md")
    candidate = posixpath.normpath(candidate)
    if candidate == ".." or candidate.startswith("../"):
        return None
    return candidate.lstrip("./")


def rewrite_href(
    source_rel: str,
    output_rel: str,
    href: str,
    page_sources: set[str],
) -> tuple[str, str | None, str | None]:
    """Bundle 内 Markdown リンクを生成 HTML への相対リンクに変換する。"""
    if not href or href.startswith("#") or href.startswith("//"):
        return href, None, None
    parsed = urlsplit(href)
    if parsed.scheme or not parsed.path:
        return href, None, None
    if not (parsed.path.lower().endswith(".md") or parsed.path.endswith("/")):
        return href, None, None

    target = _normalize_bundle_target(source_rel, parsed.path)
    if target is None:
        return href, None, f"{source_rel}: Bundle 外を指すリンクを保持しました: {href}"
    if target not in page_sources:
        return href, None, f"{source_rel}: HTML 化できないリンク先を保持しました: {href}"

    target_html = str(PurePosixPath(target).with_suffix(".html"))
    output_dir = posixpath.dirname(output_rel) or "."
    relative = posixpath.relpath(target_html, output_dir)
    rewritten = urlunsplit(("", "", relative, parsed.query, parsed.fragment))
    return rewritten, target, None


def _markdown() -> Any:
    if MarkdownIt is None:
        raise RenderError(
            "markdown-it-py が必要です。"
            " `pip install okf-devkit` を実行してください。"
        )
    md = MarkdownIt("commonmark", {"html": False, "linkify": False, "typographer": False})
    md.enable("table")
    default_fence = md.renderer.rules.get("fence")

    def render_fence(tokens, idx, options, env):
        token = tokens[idx]
        language = token.info.strip().split(maxsplit=1)[0] if token.info.strip() else ""
        if language.lower() == "mermaid":
            source = html.escape(token.content, quote=False)
            return (
                '<figure class="diagram"><div class="mermaid" data-mermaid-source="true">'
                f"{source}</div><figcaption>Mermaid diagram</figcaption></figure>\n"
            )
        rendered = default_fence(tokens, idx, options, env) if default_fence else ""
        if token.content.count("\n") > 40:
            label = html.escape(language or "code")
            return (
                '<details class="long-code"><summary>'
                f"長いコードを表示（{label}）</summary>{rendered}</details>\n"
            )
        return rendered

    md.renderer.rules["fence"] = render_fence
    md.renderer.rules["table_open"] = lambda *_args: '<div class="table-scroll"><table>\n'
    md.renderer.rules["table_close"] = lambda *_args: "</table></div>\n"
    return md


def _prepare_page(page: Page, md: Any) -> None:
    source = AUTO_MARKER_RE.sub("", page.doc.body)
    page.tokens = md.parse(source)
    used: dict[str, int] = {}
    text_parts: list[str] = []
    for idx, token in enumerate(page.tokens):
        if token.type == "heading_open" and idx + 1 < len(page.tokens):
            inline = page.tokens[idx + 1]
            title = getattr(inline, "content", "").strip()
            level = int(token.tag[1:]) if token.tag.startswith("h") else 2
            anchor = _slug(title, used)
            token.attrSet("id", anchor)
            page.headings.append(Heading(level, title, anchor))
        if token.type in {"inline", "fence", "code_block"}:
            text_parts.append(getattr(token, "content", ""))
    page.char_count = len(re.sub(r"\s+", "", "".join(text_parts)))


def _rewrite_page_links(page: Page, page_sources: set[str], warnings: list[str]) -> None:
    for token in _iter_tokens(page.tokens):
        if token.type != "link_open":
            continue
        href = token.attrGet("href")
        if not href:
            continue
        rewritten, target, warning = rewrite_href(
            page.source_rel, page.output_rel, href, page_sources
        )
        token.attrSet("href", rewritten)
        if target:
            page.outbound.add(target)
        if warning:
            token.attrJoin("class", "is-broken")
            warnings.append(warning)


def _render_toc(headings: list[Heading]) -> str:
    visible = [heading for heading in headings if heading.level >= 2]
    if len(visible) < 3:
        return ""
    items = []
    for heading in visible:
        indent = max(0, heading.level - 2)
        items.append(
            f'<li class="toc-level-{indent}"><a href="#{html.escape(heading.anchor, quote=True)}">'
            f"{html.escape(heading.title)}</a></li>"
        )
    return '<nav class="toc" aria-label="ページ内目次"><h2>目次</h2><ol>' + "".join(items) + "</ol></nav>"


def _relative_html(from_output: str, target_source: str) -> str:
    target = str(PurePosixPath(target_source).with_suffix(".html"))
    return posixpath.relpath(target, posixpath.dirname(from_output) or ".")


def _render_navigation(pages: list[Page], current: Page) -> str:
    groups: dict[str, list[Page]] = {}
    for page in pages:
        parts = PurePosixPath(page.source_rel).parts
        group = parts[0] if len(parts) > 1 else "ルート"
        groups.setdefault(group, []).append(page)
    order = ["ルート", "project", "client", "server", "batch", "backlog"]
    group_names = {
        "ルート": "全体",
        "project": "プロジェクト",
        "client": "クライアント",
        "server": "サーバー",
        "batch": "バッチ",
        "backlog": "バックログ",
    }
    chunks = []
    for group in sorted(groups, key=lambda item: (order.index(item) if item in order else 99, item)):
        chunks.append(f"<section><h2>{html.escape(group_names.get(group, group))}</h2><ul>")
        for page in sorted(groups[group], key=lambda item: (item.source_rel != f"{group}/index.md", item.source_rel)):
            active = ' aria-current="page" class="active"' if page.source_rel == current.source_rel else ""
            href = _relative_html(current.output_rel, page.source_rel)
            search = " ".join(
                str(value)
                for value in (
                    page.doc.title,
                    page.doc.description,
                    page.doc.type,
                    " ".join(page.doc.get("tags", [])) if isinstance(page.doc.get("tags", []), list) else "",
                )
            ).lower()
            chunks.append(
                f'<li data-search="{html.escape(search, quote=True)}"><a href="{html.escape(href, quote=True)}"{active}>'
                f"{html.escape(page.doc.title)}</a></li>"
            )
        chunks.append("</ul></section>")
    return "".join(chunks)


def _render_breadcrumbs(page: Page, page_sources: set[str]) -> str:
    parts = PurePosixPath(page.source_rel).parts
    crumbs = [f'<a href="{html.escape(_relative_html(page.output_rel, "index.md"), quote=True)}">docs</a>']
    for idx, part in enumerate(parts[:-1], start=1):
        index_source = "/".join(parts[:idx]) + "/index.md"
        if index_source in page_sources:
            href = _relative_html(page.output_rel, index_source)
            crumbs.append(f'<a href="{html.escape(href, quote=True)}">{html.escape(part)}</a>')
        else:
            crumbs.append(f"<span>{html.escape(part)}</span>")
    if page.source_rel != "index.md":
        crumbs.append(f"<span>{html.escape(page.doc.title)}</span>")
    return '<nav class="breadcrumbs" aria-label="パンくず">' + '<span aria-hidden="true">/</span>'.join(crumbs) + "</nav>"


def _render_badges(doc: Any) -> str:
    type_name = doc.type or ("Index" if doc.name == "index.md" else "Log" if doc.name == "log.md" else "Document")
    status = doc.status
    trust_class, trust_label = _trust_level(doc)
    values = [
        ("type", type_name),
        (f"status-{status}", status),
        (trust_class, trust_label),
    ]
    if doc.type == "Backlog Item":
        for key in ("state", "priority", "effort", "ai"):
            value = doc.get(key)
            if value is not None:
                values.append((key, f"{key}: {value}"))
    return '<div class="badges">' + "".join(
        f'<span class="badge {html.escape(css, quote=True)}">{html.escape(str(label))}</span>'
        for css, label in values
    ) + "</div>"


def _render_related(page: Page, page_sources: set[str]) -> str:
    raw = page.doc.get("related", [])
    if not isinstance(raw, list):
        return ""
    items = []
    for value in raw:
        if not isinstance(value, str):
            continue
        rewritten, target, _warning = rewrite_href(page.source_rel, page.output_rel, value, page_sources)
        if target:
            items.append(f'<li><a href="{html.escape(rewritten, quote=True)}">{html.escape(value)}</a></li>')
    if not items:
        return ""
    return '<aside class="related"><h2>関連ドキュメント</h2><ul>' + "".join(items) + "</ul></aside>"


def _render_backlinks(page: Page, pages_by_source: dict[str, Page]) -> str:
    incoming = [source for source in pages_by_source.values() if page.source_rel in source.outbound]
    if not incoming:
        return ""
    items = []
    for source in sorted(incoming, key=lambda item: item.source_rel):
        href = _relative_html(page.output_rel, source.source_rel)
        items.append(f'<li><a href="{html.escape(href, quote=True)}">{html.escape(source.doc.title)}</a></li>')
    return '<aside class="backlinks"><h2>このページへのリンク</h2><ul>' + "".join(items) + "</ul></aside>"


def _replace_template(template: str, values: dict[str, str], source: str) -> str:
    """テンプレートだけを1回走査し、挿入した本文を再置換しない。"""
    missing: set[str] = set()

    def replace(match: re.Match[str]) -> str:
        key = match.group(1)
        if key not in values:
            missing.add(key)
            return match.group(0)
        return values[key]

    output = TEMPLATE_TOKEN_RE.sub(replace, template)
    if missing:
        raise RenderError(
            f"{source}: HTML テンプレートに未解決の項目があります: {', '.join(sorted(missing))}"
        )
    return output


def _write_atomic(path: Path, content: str) -> bool:
    data = content.replace("\r\n", "\n").encode("utf-8")
    if path.exists() and path.read_bytes() == data:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(tmp_name, path)
    finally:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)
    return True


def render_bundle(
    bundle: Any,
    doc_factory: Callable[[Path, Path], Any],
    output_root: Path | None = None,
    *,
    write: bool = True,
) -> RenderReport:
    """Bundle 全体を HTML 化し、結果を返す。"""
    md = _markdown()
    site_name = str(getattr(bundle, "site_name", "") or "Docs")
    actual_output_root = (output_root or bundle.root).resolve()
    source_paths = bundle.md_files(include_reserved=True)
    pages = []
    for source in source_paths:
        source_rel = source.relative_to(bundle.root).as_posix()
        pages.append(
            Page(
                doc=doc_factory(source, bundle.root),
                source_rel=source_rel,
                output_rel=str(PurePosixPath(source_rel).with_suffix(".html")),
            )
        )

    page_sources = {page.source_rel for page in pages}
    warnings: list[str] = []
    for page in pages:
        _prepare_page(page, md)
        _rewrite_page_links(page, page_sources, warnings)
        related = page.doc.get("related", [])
        if isinstance(related, list):
            for value in related:
                if isinstance(value, str):
                    _rewritten, target, warning = rewrite_href(page.source_rel, page.output_rel, value, page_sources)
                    if target:
                        page.outbound.add(target)
                    if warning:
                        warnings.append(warning)
        page.body_html = md.renderer.render(page.tokens, md.options, {})

    template = _asset_text("page.html")
    pages_by_source = {page.source_rel: page for page in pages}
    planned: list[tuple[Path, str]] = []
    for page in pages:
        target = actual_output_root.joinpath(*PurePosixPath(page.output_rel).parts)
        assets_rel = posixpath.relpath("_assets", posixpath.dirname(page.output_rel) or ".")
        long_page = len([item for item in page.headings if item.level >= 2]) >= 5 or page.char_count >= 3000
        source_hash = hashlib.sha256(page.doc.text.encode("utf-8")).hexdigest()[:16]
        source_path = bundle.root.joinpath(*PurePosixPath(page.source_rel).parts)
        source_link = os.path.relpath(source_path, target.parent).replace("\\", "/")
        type_name = page.doc.type or ("Index" if page.doc.name == "index.md" else "Log")
        values = {
            "TITLE": html.escape(page.doc.title),
            "DESCRIPTION": html.escape(
                page.doc.description or f"{page.doc.title} — {site_name} documentation"
            ),
            "SITE_NAME": html.escape(site_name),
            "LANG": "ja",
            "ASSETS": html.escape(assets_rel, quote=True),
            "SOURCE": html.escape(page.source_rel),
            "SOURCE_LINK": html.escape(source_link, quote=True),
            "HOME_LINK": html.escape(_relative_html(page.output_rel, "index.md"), quote=True),
            "SOURCE_HASH": source_hash,
            "TYPE_CLASS": html.escape(_type_class(type_name), quote=True),
            "LONG_CLASS": " long-document" if long_page else "",
            "BREADCRUMBS": _render_breadcrumbs(page, page_sources),
            "BADGES": _render_badges(page.doc),
            "NAVIGATION": _render_navigation(pages, page),
            "TOC": _render_toc(page.headings),
            "CONTENT": page.body_html,
            "RELATED": _render_related(page, page_sources),
            "BACKLINKS": _render_backlinks(page, pages_by_source),
        }
        planned.append((target, _replace_template(template, values, page.source_rel)))

    assets = {
        actual_output_root / "_assets" / "docs.css": _asset_text("docs.css"),
        actual_output_root / "_assets" / "docs.js": _asset_text("docs.js"),
    }
    written = 0
    removed = 0
    if write:
        for path, content in [*planned, *assets.items()]:
            written += int(_write_atomic(path, content))
        expected = {path.resolve() for path, _content in planned}
        for old_html in actual_output_root.rglob("*.html"):
            if old_html.resolve() in expected or not old_html.is_file():
                continue
            try:
                prefix = old_html.read_text(encoding="utf-8", errors="replace")[:256]
            except OSError:
                continue
            if OWNERSHIP_MARKER in prefix:
                old_html.unlink()
                removed += 1
    return RenderReport(len(pages), written, removed, sorted(set(warnings)), actual_output_root)
