"""Document convention findings with bundle-owned resource and index paths."""
from __future__ import annotations
import re
from functools import lru_cache
from pathlib import Path
from .. import gitutil, yamlio
from ..config import Bundle
from ..doc import Doc
from ..errors import MarkerError, OkfError
from ..fsutil import is_iso_date, parse_datetime, read_text, rel_posix
from . import index as _index

ACTOR_RE = re.compile(r"^(?:human:\S+|process:\S+|[^\s/]+/[^\s/]+)$")

# 文末記号。`.` `!` `?` は後ろが空白 or 行末のときだけ文末とみなす（`v1.0` 対策）
SENTENCE_END_RE = re.compile(r"[。！？]|[.!?](?=\s|$)")
PLACEHOLDER_RE = re.compile(r"<[^<>\r\n]+>")


@lru_cache(maxsize=1)
def _markdown_parser():
    try:
        from markdown_it import MarkdownIt
    except ImportError:
        # Source-only runs without site-packages still support the metadata checks.
        return None
    return MarkdownIt("commonmark", {"html": False})


@lru_cache(maxsize=1)
def _template_placeholders() -> tuple[set[str], set[str]]:
    templates = Path(__file__).resolve().parents[1] / "scaffold" / "templates"
    frontmatter, body = set(), set()
    for path in templates.glob("*.md"):
        if path.name != "log.md":
            head, _, text = read_text(path).partition("\n---\n")
            frontmatter.update(PLACEHOLDER_RE.findall(head))
            body.update(PLACEHOLDER_RE.findall(text))
    return frontmatter, body


def _yaml_strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, (dict, list)):
        for child in value.values() if isinstance(value, dict) else value:
            yield from _yaml_strings(child)


def _remaining_placeholders(doc: Doc):
    frontmatter, body_tokens = _template_placeholders()
    body_start = doc.text.count("\n") - doc.body.count("\n")
    prefix = "<okf-placeholder-"
    while prefix in doc.text:
        prefix = "<x" + prefix[1:]
    candidates = {}

    # Keep the source location even when a known prompt contains Markdown syntax.
    def mark(text, allowed, start):
        def replace(match):
            token = match.group()
            if token not in allowed:
                return token
            marker = f"{prefix}{len(candidates)}>"
            candidates[marker] = (start + text.count("\n", 0, match.start()), token)
            return marker
        return PLACEHOLDER_RE.sub(replace, text)

    header = mark("\n".join(doc.text.split("\n")[1:body_start - 1]), frontmatter, 2)
    parsed_strings = []
    if candidates:
        try:
            parsed_strings = list(_yaml_strings(yamlio.parse_yaml(header, core=doc.okf03)))
        except OkfError:
            # A marker can change unusual explicit YAML syntax. The original was already validated.
            pass
    body = mark(doc.body, body_tokens, body_start + 1)
    if body != doc.body and (markdown := _markdown_parser()) is not None:
        parsed_strings.extend(
            inline.content
            for block in markdown.parse(body) if block.type == "inline"
            for inline in block.children or [] if inline.type == "text"
        )

    visible = {token for text in parsed_strings for token in PLACEHOLDER_RE.findall(text)}
    found = {}
    for marker, (line, token) in candidates.items():
        if marker in visible:
            found.setdefault(line, token)
    yield from found.items()


class Finding:
    def __init__(self, path: str, line: int | None, level: str, rule: str, message: str):
        self.path = path
        self.line = line
        self.level = level
        self.rule = rule
        self.message = message

    def __str__(self) -> str:
        loc = f"{self.path}:{self.line}" if self.line else self.path
        return f"{loc} {self.level} {self.rule} {self.message}"


def _check_actor_entry(entry, label: str) -> str | None:
    """`{by, at}` 形式の Actor エントリを検証し、問題があればメッセージを返す。"""
    if not isinstance(entry, dict):
        return f"`{label}` はマップ（`by` / `at`）である必要があります"
    by = entry.get("by")
    if not isinstance(by, str) or not ACTOR_RE.match(by.strip()):
        return f"`{label}.by: {by!r}` は Actor 表記（producer/version, human:, process:）ではありません"
    at = entry.get("at")
    if at is not None:
        parsed, _ = parse_datetime(at)
        if parsed is None:
            return f"`{label}.at: {at!r}` は ISO 8601 ではありません"
    return None


def trust_level(doc: Doc) -> str:
    """`verified` の内容から信頼度を返す（CONVENTIONS.md §1-3）。"""
    verified = doc.fm.get("verified")
    if not isinstance(verified, list) or not verified:
        return "unverified"
    actors = []
    for item in verified:
        if isinstance(item, dict) and isinstance(item.get("by"), str):
            actors.append(item["by"].strip())
    if not actors:
        return "unverified"
    if any(a.startswith("human:") for a in actors):
        return "human-reviewed"
    return "machine-confirmed"


def run_lint(bundle: Bundle, *, repo_root: Path | None = None, resource_resolver=None, index_renderer=None, project: bool = False) -> list[Finding]:
    """CONVENTIONS.md §10 の L1〜L15 を検証する。"""
    repo_root = bundle.repo_root if repo_root is None else repo_root
    findings: list[Finding] = []
    add = findings.append
    project = project or not bundle.okf03

    # --- L1〜L6, L9〜L12: 非予約ドキュメント ---
    documents = (bundle.document(p) for p in bundle.md_files()) if bundle.okf03 else bundle.docs()
    for doc in documents:
        path = doc.repo_rel
        if bundle.okf03 and not doc.fm_opened:
            continue
        if not doc.has_fm or doc.fm_error:
            reason = doc.fm_error or "frontmatter がありません"
            add(Finding(path, 1, "error", "L1", f"frontmatter を読めません: {reason}"))
            continue

        if bundle.okf03 and not doc.type:
            continue
        if not project:
            continue

        for line, token in _remaining_placeholders(doc):
            add(Finding(path, line, "warn", "L15", f"雛形の記入例が残っています: {token}"))

        if not doc.type:
            add(Finding(path, doc.key_line("type"), "error", "L2", "`type` が空です"))
        elif doc.type not in bundle.types:
            add(Finding(path, doc.key_line("type"), "error", "L3",
                        f"`type: {doc.type}` は語彙表にありません（CONVENTIONS.md §2）"))

        if "status" in doc.fm and doc.fm.get("status") is not None:
            raw_status = doc.fm.get("status")
            if not isinstance(raw_status, str) or raw_status.strip() not in bundle.statuses:
                add(Finding(path, doc.key_line("status"), "error", "L4",
                            f"`status: {raw_status!r}` は {'/'.join(bundle.statuses)} "
                            "のいずれか（文字列）にしてください"))

        layer = doc.fm.get("layer")
        if not isinstance(layer, str) or layer.strip() not in bundle.layers:
            add(Finding(path, doc.key_line("layer"), "error", "L5",
                        f"`layer` は {'/'.join(bundle.layers)} のいずれかが必要です（現在: {layer!r}）"))

        if "generated" in doc.fm and doc.fm.get("generated") is not None:
            problem = _check_actor_entry(doc.fm.get("generated"), "generated")
            if problem:
                add(Finding(path, doc.key_line("generated"), "warn", "L6", problem))

        if "verified" in doc.fm and doc.fm.get("verified") is not None:
            verified = doc.fm.get("verified")
            if not isinstance(verified, list):
                add(Finding(path, doc.key_line("verified"), "warn", "L6",
                            f"`verified` はリストである必要があります（現在: {type(verified).__name__}）"))
            elif not verified:
                add(Finding(path, doc.key_line("verified"), "warn", "L6", "`verified` が空配列です"))
            else:
                for pos, item in enumerate(verified, start=1):
                    problem = _check_actor_entry(item, f"verified[{pos}]")
                    if problem:
                        add(Finding(path, doc.key_line("verified"), "warn", "L6", problem))

        desc = doc.description
        if desc:
            if len(SENTENCE_END_RE.findall(desc)) > 1:
                add(Finding(path, doc.key_line("description"), "warn", "L9",
                            "`description` は一文にしてください（文末記号が 2 つ以上あります）"))
            if len(desc) > 120:
                add(Finding(path, doc.key_line("description"), "warn", "L9",
                            f"`description` が 120 字を超えています（{len(desc)} 字）"))

        for problem in doc.code_globs_problems():
            add(Finding(path, doc.key_line("code_globs"), "error", "L10", problem))

        globs = doc.code_globs()
        if not globs and doc.requires_code_globs():
            add(Finding(path, doc.key_line("type"), "warn", "L10",
                        f"`code_globs` がありません（type: {doc.type} はコード由来なので更新検知の起点が必要です）"))

        for pattern in globs:
            if not (gitutil.resolve_resource(repo_root, pattern, exclude=bundle.code_glob_exclude) if resource_resolver is None else resource_resolver(pattern)):
                add(Finding(path, doc.key_line("code_globs"), "warn", "L10",
                            f"`code_globs: {pattern}` {gitutil.code_glob_no_match(pattern, bundle.code_glob_exclude)}"))

        for problem in doc.source_problems():
            add(Finding(path, doc.key_line("sources"), "warn", "L14", problem))

        related = doc.fm.get("related")
        if related is not None and not isinstance(related, list):
            add(Finding(path, doc.key_line("related"), "warn", "L11",
                        f"`related` はリストである必要があります（現在: {type(related).__name__}）"))
        elif isinstance(related, list):
            for link in related:
                if not isinstance(link, str) or not link.strip():
                    add(Finding(path, doc.key_line("related"), "warn", "L11",
                                f"`related` の要素が文字列ではありません: {link!r}"))
                    continue
                target = link.split("#", 1)[0].strip()
                if not target or target.startswith(("http://", "https://")):
                    continue
                base = bundle.root if target.startswith("/") else doc.path.parent
                candidate = (base / target.lstrip("/")).resolve()
                try:
                    candidate.relative_to(bundle.root.resolve())
                except ValueError:
                    add(Finding(path, doc.key_line("related"), "warn", "L11",
                                f"`related` はバンドル（{rel_posix(bundle.root, repo_root)}/）内を"
                                f"指す必要があります: {link}"))
                    continue
                if not candidate.exists():
                    add(Finding(path, doc.key_line("related"), "warn", "L11",
                                f"`related` のリンク先が存在しません: {link}"))

        if doc.type == "Backlog Item":
            states = list(bundle.backlog_cfg.get("states") or [])
            state = doc.fm.get("state")
            if not isinstance(state, str) or state.strip() not in states:
                add(Finding(path, doc.key_line("state"), "error", "L12",
                            f"`state` は {'/'.join(states)} のいずれかが必要です（現在: {state!r}）"))
            elif state.strip() == "done":
                done_at = doc.fm.get("done_at")
                if not is_iso_date(done_at if isinstance(done_at, str) else str(done_at or "")):
                    add(Finding(path, doc.key_line("done_at"), "error", "L12",
                                f"`state: done` には `done_at: YYYY-MM-DD`（実在する日付）が必要です"
                                f"（現在: {done_at!r}）"))

    # --- L7: 予約ファイルの frontmatter（ルート index.md の okf_version のみ例外） ---
    for directory in bundle.dirs():
        index_path = directory / "index.md"
        if index_path.exists() and (not bundle.okf03 or not index_path.is_symlink()):
            doc = bundle.document(index_path)
            rel = doc.repo_rel
            is_root = directory.resolve() == bundle.root.resolve()
            if doc.fm_opened and not doc.has_fm:
                add(Finding(rel, 1, "error", "L7",
                            f"index.md の frontmatter が壊れています: {doc.fm_error}"))
            elif doc.has_fm and doc.fm_error:
                add(Finding(rel, 1, "error", "L7",
                            f"index.md の frontmatter を読めません: {doc.fm_error}"))
            elif doc.has_fm and not (is_root and (bundle.okf03 or set(doc.fm) <= {"okf_version"})):
                add(Finding(rel, 1, "error", "L7",
                            "index.md は frontmatter を持てません（ルートの `okf_version` のみ例外）"))

        log_path = directory / "log.md"
        if log_path.exists() and (not bundle.okf03 or not log_path.is_symlink()):
            log_doc = bundle.document(log_path)
            if log_doc.fm_opened:
                add(Finding(log_doc.repo_rel, 1, "error", "L7",
                            "log.md は frontmatter を持てません（OKF v0.2 §8 の予約ファイル）"))

    # --- L8: log.md の日付見出し ---
    for directory in bundle.dirs():
        log_path = directory / "log.md"
        if not log_path.exists() or (bundle.okf03 and log_path.is_symlink()):
            continue
        rel = rel_posix(log_path, repo_root)
        prev: str | None = None
        seen: dict[str, int] = {}
        for no, line in enumerate(read_text(log_path).split("\n"), start=1):
            if not line.startswith("## "):
                continue
            heading = line[3:].strip()
            if not is_iso_date(heading):
                add(Finding(rel, no, "warn", "L8",
                            f"見出しが ISO 8601 の実在する日付ではありません: {heading}"))
                continue
            if heading in seen:
                add(Finding(rel, no, "warn", "L8",
                            f"日付見出しが重複しています: {heading}（{seen[heading]} 行目にもあります）"))
            else:
                seen[heading] = no
            if prev and heading > prev:
                add(Finding(rel, no, "warn", "L8",
                            f"日付見出しが新しい順になっていません: {prev} の後に {heading}"))
            prev = heading

    # --- L13: index.md が最新か ---
    for directory in bundle.dirs() if project else ():
        index_path = directory / "index.md"
        try:
            block = _index.build_index_block(bundle, directory)
            content = (_index.render_index(bundle, directory, block, repo_root=repo_root) if index_renderer is None else index_renderer(bundle, directory, block))
        except MarkerError as exc:
            add(Finding(rel_posix(index_path, repo_root), None, "error", "L13", str(exc)))
            continue
        current = _index.read_index(bundle, index_path) if index_path.exists() else None
        if current != content:
            add(Finding(rel_posix(index_path, repo_root), None, "error", "L13",
                        "index.md が最新ではありません（`okf index --write` を実行してください）"))

    findings.sort(key=lambda f: (f.path, f.line or 0, f.rule))
    return findings


def cmd_lint(bundle: Bundle, args, *, linter=None) -> int:
    lint = run_lint if linter is None else linter
    findings = lint(bundle, project=True) if bundle.okf03 and getattr(args, "project", False) else lint(bundle)
    for finding in findings:
        print(finding)
    errors = sum(1 for f in findings if f.level == "error")
    warns = sum(1 for f in findings if f.level == "warn")
    print(f"\nlint: error {errors} 件 / warn {warns} 件")
    if errors:
        return 1
    if warns and getattr(args, "strict", False):
        return 1
    return 0
