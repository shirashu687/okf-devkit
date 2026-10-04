"""Safe document/backlog scaffolding under the bundle project root."""
from __future__ import annotations
import re
from pathlib import Path
from ..config import Bundle
from ..doc import CODE_GLOBS_REQUIRED_TYPES
from ..errors import OkfError
from ..fsutil import now_iso, today, read_text, rel_posix, write_if_changed
from ..yamlio import yaml_scalar, yaml_flow_list

SLUG_RE = re.compile(r"^[a-z0-9]+(?:[-.][a-z0-9]+)*$")


def slugify(title: str) -> str:
    """タイトルから ASCII の kebab-case slug を作る。作れなければ空文字。"""
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", title).strip("-").lower()
    return slug


def validate_slug(slug: str) -> str:
    if not SLUG_RE.match(slug):
        raise OkfError(
            f"slug は kebab-case（英小文字・数字・ハイフン）で指定してください: {slug!r}"
        )
    return slug


def validate_subdir(value: str) -> str:
    """`--dir` を検証する（相対・kebab-case・`..` 禁止）。"""
    normalized = value.replace("\\", "/").strip("/")
    if not normalized:
        raise OkfError("`--dir` が空です")
    if value.startswith(("/", "\\")) or re.match(r"^[A-Za-z]:", value):
        raise OkfError(f"`--dir` に絶対パスは指定できません: {value!r}")
    for part in normalized.split("/"):
        if part in ("", ".", ".."):
            raise OkfError(f"`--dir` に `.` / `..` は使えません: {value!r}")
        validate_slug(part)
    return normalized


def ensure_inside_bundle(bundle: Bundle, path: Path, *, repo_root: Path | None = None) -> Path:
    repo_root = bundle.repo_root if repo_root is None else repo_root
    resolved = path.resolve()
    try:
        resolved.relative_to(bundle.root.resolve())
    except ValueError:
        raise OkfError(
            f"バンドル（{rel_posix(bundle.root, repo_root)}/）の外には作成できません: {resolved}"
        ) from None
    return resolved


def set_fm_field(text: str, key: str, value: str, parent: str | None = None) -> str:
    """frontmatter の 1 フィールドを置換する（parent 指定でネストしたキーに対応）。

    value は**すでに YAML としてシリアライズ済み**の文字列であること。
    """
    lines = text.split("\n")
    if not lines or lines[0].strip() != "---":
        return text
    end = next((i for i in range(1, len(lines)) if lines[i].strip() == "---"), None)
    if end is None:
        return text
    if parent is None:
        for i in range(1, end):
            if re.match(rf"^{re.escape(key)}\s*:", lines[i]):
                stop = i + 1
                while stop < end and (lines[stop].startswith((" ", "\t")) or not lines[stop].strip()):
                    stop += 1
                lines[i:stop] = [f"{key}: {value}"]
                break
        else:
            lines.insert(end, f"{key}: {value}")
    else:
        in_parent = False
        for i in range(1, end):
            if re.match(rf"^{re.escape(parent)}\s*:", lines[i]):
                in_parent = True
                continue
            if in_parent:
                if not lines[i].startswith((" ", "\t")):
                    break
                if re.match(rf"^\s+{re.escape(key)}\s*:", lines[i]):
                    indent = lines[i][: len(lines[i]) - len(lines[i].lstrip())]
                    lines[i] = f"{indent}{key}: {value}"
                    break
    return "\n".join(lines)


def load_template(bundle: Bundle, type_name: str, *, repo_root: Path | None = None) -> str:
    repo_root = bundle.repo_root if repo_root is None else repo_root
    templates = bundle.cfg.get("templates") or {}
    rel = templates.get(type_name)
    if not rel:
        raise OkfError(f"type '{type_name}' に対応するテンプレートが config.yml にありません")
    path = bundle.root / str(rel)
    if not path.exists():
        raise OkfError(f"テンプレートが見つかりません: {rel_posix(path, repo_root)}")
    return read_text(path)


def next_numbered_id(directory: Path, prefix: str = "") -> int:
    """`<prefix>NNNN-...` の最大値 + 1 を返す（prefix 無しは ADR 用）。"""
    pattern = rf"^{re.escape(prefix)}(\d{{4}})(?:-|\.md$)"
    max_id = 0
    if directory.exists():
        for p in directory.glob("*.md"):
            m = re.match(pattern, p.name)
            if m:
                max_id = max(max_id, int(m.group(1)))
    return max_id + 1


def next_backlog_id(bundle: Bundle) -> int:
    """既存の B-NNNN の最大値 + 1 を返す。"""
    prefix = str(bundle.backlog_cfg.get("prefix", "B"))
    return next_numbered_id(bundle.backlog_dir(), f"{prefix}-")


def _validate_vocab(value: str, allowed: list, label: str) -> str:
    if allowed and value not in allowed:
        raise OkfError(f"`{label} {value}` は語彙表にありません（{', '.join(str(a) for a in allowed)}）")
    return value


def cmd_new(bundle: Bundle, args, *, repo_root: Path | None = None, writer=None, template_loader=None, path_validator=None) -> int:
    repo_root = bundle.repo_root if repo_root is None else repo_root
    if "\n" in args.title or "\r" in args.title:
        raise OkfError("`--title` に改行は使えません")
    _validate_vocab(args.layer, bundle.layers, "--layer")

    if args.kind == "backlog":
        _validate_vocab(args.priority, list(bundle.backlog_cfg.get("priorities") or []), "--priority")
        _validate_vocab(args.effort, list(bundle.backlog_cfg.get("efforts") or []), "--effort")
        text = (load_template(bundle, "Backlog Item", repo_root=repo_root) if template_loader is None else template_loader(bundle, "Backlog Item"))
        number = next_backlog_id(bundle)
        prefix = str(bundle.backlog_cfg.get("prefix", "B"))
        slug = validate_slug(args.slug) if args.slug else slugify(args.title)
        name = f"{prefix}-{number:04d}-{slug}.md" if slug else f"{prefix}-{number:04d}.md"
        out_path = bundle.backlog_dir() / name

        text = set_fm_field(text, "title", yaml_scalar(args.title))
        text = set_fm_field(text, "layer", yaml_scalar(args.layer))
        text = set_fm_field(text, "tags", yaml_flow_list([args.layer]))
        text = set_fm_field(text, "state", yaml_scalar("todo"))
        text = set_fm_field(text, "priority", yaml_scalar(args.priority))
        text = set_fm_field(text, "effort", yaml_scalar(args.effort))
        text = set_fm_field(text, "created", yaml_scalar(today().isoformat()))
        text = set_fm_field(text, "by", yaml_scalar("process:okf-cli"), parent="generated")
        text = set_fm_field(text, "at", yaml_scalar(now_iso()), parent="generated")
    else:
        _validate_vocab(args.type, bundle.types, "--type")
        code_globs = getattr(args, "code_globs", None) or []
        if args.type in CODE_GLOBS_REQUIRED_TYPES and not code_globs:
            raise OkfError("この型では `--code-globs` を指定してください")
        text = (load_template(bundle, args.type, repo_root=repo_root) if template_loader is None else template_loader(bundle, args.type))
        slug = validate_slug(args.slug) if args.slug else slugify(args.title)
        if not slug:
            raise OkfError("タイトルから slug を生成できませんでした。`--slug <kebab-case>` を指定してください。")
        layer_dirs = bundle.cfg.get("layer_dirs") or {}
        base = bundle.root / str(layer_dirs.get(args.layer, args.layer))
        if args.dir:
            base = base / validate_subdir(args.dir)
        filename = f"{slug}.md"
        if args.type == "Decision Record":
            # ADR は CONVENTIONS.md §8 に従い 4 桁連番を前置する
            filename = f"{next_numbered_id(base):04d}-{slug}.md"
        out_path = base / filename

        text = set_fm_field(text, "code_globs", yaml_flow_list(code_globs))
        text = set_fm_field(text, "related", "[]")
        text = set_fm_field(text, "type", yaml_scalar(args.type))
        text = set_fm_field(text, "title", yaml_scalar(args.title))
        text = set_fm_field(text, "layer", yaml_scalar(args.layer))
        text = set_fm_field(text, "by", yaml_scalar("process:okf-cli"), parent="generated")
        text = set_fm_field(text, "at", yaml_scalar(now_iso()), parent="generated")

    out_path = (ensure_inside_bundle(bundle, out_path, repo_root=repo_root) if path_validator is None else path_validator(bundle, out_path))
    text = re.sub(r"^#[ \t]+<[^>\r\n]*>[ \t]*$", lambda _m: f"# {args.title}", text, count=1, flags=re.MULTILINE)

    if out_path.exists():
        raise OkfError(f"既に存在します: {rel_posix(out_path, repo_root)}")
    (write_if_changed if writer is None else writer)(out_path, text)
    print(rel_posix(out_path, repo_root))
    return 0
