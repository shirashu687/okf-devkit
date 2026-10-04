"""Project scaffolding using explicit project and installed-package asset roots."""
from __future__ import annotations
import re
from pathlib import Path
from ..config import CONFIG_FILENAME
from ..errors import OkfError
from ..fsutil import now_iso, write_if_changed
from ..yamlio import yaml_scalar

SCAFFOLD_DIR = Path(__file__).resolve().parents[1] / "scaffold"

def _scaffold_text(rel: str, *, scaffold_dir: Path | None = None) -> str:
    path = (SCAFFOLD_DIR if scaffold_dir is None else scaffold_dir) / rel
    if not path.is_file():  # pragma: no cover - 壊れたインストール向け
        raise OkfError(f"scaffold が見つかりません: {path}")
    return path.read_text(encoding="utf-8").replace("\r\n", "\n")


def _parse_layer_specs(specs: list[str] | None) -> list[tuple[str, str, str]]:
    """``--layer name=glob[:dir]`` を (name, glob, dir) に分解する。

    ``glob`` は「その層に属するコードのパス」で、log の振り分けと affected の
    起点になる。``dir`` 省略時は層名をそのままバンドル内のディレクトリ名に使う。
    """
    parsed: list[tuple[str, str, str]] = []
    seen: set[str] = set()
    for spec in specs or []:
        name, sep, rest = spec.partition("=")
        name = name.strip()
        if not sep or not name or not rest.strip():
            raise OkfError(f"--layer の書式が不正です（name=glob[:dir]）: {spec}")
        glob_part, _, dir_part = rest.partition(":")
        glob_part = glob_part.strip()
        dir_part = dir_part.strip() or name
        if not re.fullmatch(r"[a-z0-9][a-z0-9_-]*", name):
            raise OkfError(f"層名は英小文字・数字・- _ のみ使えます: {name}")
        if name in seen:
            raise OkfError(f"層名が重複しています: {name}")
        if name == "shared":
            raise OkfError("`shared` は層をまたぐ知識用に予約されています")
        if dir_part.startswith((".", "/")) or ".." in dir_part.split("/"):
            raise OkfError(f"層のディレクトリが不正です: {dir_part}")
        seen.add(name)
        parsed.append((name, glob_part, dir_part))
    return parsed


def _render_okf_yml(
    bundle_root: str, site_name: str, layers: list[tuple[str, str, str]], *, scaffold_reader=None
) -> str:
    """``okf.yml`` を組み立てる。値はすべて ``yaml_scalar`` で安全に引用する。"""
    names = [name for name, _glob, _dir in layers]

    layer_lines = [f"  - {yaml_scalar(n)}" for n in names] + ["  - shared"]
    dir_lines = [f"  {n}: {yaml_scalar(d)}" for n, _g, d in layers]
    dir_lines.append("  shared: project")
    map_lines = [
        f"  - {{ glob: {yaml_scalar(g)}, layer: {yaml_scalar(n)} }}"
        for n, g, _d in layers
    ]
    map_lines.append(f"  - {{ glob: {yaml_scalar(bundle_root + chr(47) + chr(42) * 2)}, layer: skip }}")
    map_lines.append('  - { glob: "**", layer: shared }')
    # log.paths は log: > paths: の下なのでインデントは4スペース
    log_path_lines = [f"    {n}: {yaml_scalar(d + '/log.md')}" for n, _g, d in layers]
    log_path_lines.append("    shared: log.md")

    return (_scaffold_text if scaffold_reader is None else scaffold_reader)("okf.yml.tmpl").format(
        bundle_root=yaml_scalar(bundle_root),
        site_name=yaml_scalar(site_name),
        root_heading=yaml_scalar(f"{site_name} ドキュメント"),
        layers="\n".join(layer_lines),
        layer_dirs="\n".join(dir_lines),
        layer_map="\n".join(map_lines),
        log_layers=("[" + ", ".join(names) + "]") if names else "[]",
        log_paths="\n".join(log_path_lines),
    )


def cmd_init(repo_root: Path, args, *, scaffold_dir: Path | None = None, scaffold_reader=None, writer=None, config_renderer=None) -> int:
    """リポジトリに OKF バンドルと設定一式を生成する。"""
    repo_root = Path(repo_root)
    scaffold_dir = SCAFFOLD_DIR if scaffold_dir is None else scaffold_dir
    if scaffold_reader is None:
        scaffold_reader = lambda rel: _scaffold_text(rel, scaffold_dir=scaffold_dir)

    layers = _parse_layer_specs(args.layer)
    raw = args.bundle_root if args.bundle_root is not None else "docs"
    bundle_root = raw.strip().replace("\\", "/")
    # 末尾スラッシュを落とす前に判定する（"/abs" が "abs" に化けるのを防ぐ）。
    if bundle_root.startswith(("/", ".")) or ":" in bundle_root:
        raise OkfError(f"bundle_root はプロジェクト内の相対パスで指定してください: {raw!r}")
    bundle_root = bundle_root.rstrip("/")
    if not bundle_root or ".." in bundle_root.split("/"):
        raise OkfError(f"bundle_root が不正です: {raw!r}")
    site_name = (args.site_name or repo_root.name).strip() or "Project"

    created: list[str] = []
    skipped: list[str] = []

    def emit(rel: str, text: str) -> None:
        path = repo_root / rel
        if path.exists() and not args.force:
            skipped.append(rel)
            return
        path.parent.mkdir(parents=True, exist_ok=True)
        (write_if_changed if writer is None else writer)(path, text)
        created.append(rel)

    layer_table = "\n".join(
        f"| `{bundle_root}/{d}/log.md` | `{g}` の変更 |" for _n, g, d in layers
    ) or "| （層を定義していません） | — |"
    tokens = {
        "GENERATED_AT": now_iso(),
        "BUNDLE_ROOT": bundle_root,
        "SITE_NAME": site_name,
        "LAYER_LIST": "、".join(n for n, _g, _d in layers) or "（層なし）",
        "LAYER_DIRS": " ".join(f"`{d}/`" for _n, _g, d in layers) or "—",
        "LAYER_TABLE": layer_table,
    }

    def expand(text: str) -> str:
        for key, value in tokens.items():
            text = text.replace("{{" + key + "}}", value)
        return text

    emit(CONFIG_FILENAME, (_render_okf_yml(bundle_root, site_name, layers, scaffold_reader=scaffold_reader) if config_renderer is None else config_renderer(bundle_root, site_name, layers)))
    emit(f"{bundle_root}/AGENTS.md", expand(scaffold_reader("AGENTS.md.tmpl")))
    emit(f"{bundle_root}/CONVENTIONS.md", expand(scaffold_reader("CONVENTIONS.md.tmpl")))

    for tmpl in sorted((scaffold_dir / "templates").glob("*.md")):
        emit(f"{bundle_root}/_templates/{tmpl.name}", scaffold_reader(f"templates/{tmpl.name}"))
    for hook in sorted((scaffold_dir / "hooks").iterdir()):
        emit(f".okf/hooks/{hook.name}", scaffold_reader(f"hooks/{hook.name}"))

    def empty_log(layer_name: str) -> str:
        return (
            f"# 変更履歴 — {layer_name}\n"
            "\n"
            "<!-- `okf log --write` が git 履歴からここに追記する。"
            "書式は /CONVENTIONS.md §7 を参照。 -->\n"
        )

    for name, _glob, directory in layers:
        emit(f"{bundle_root}/{directory}/log.md", empty_log(name))
    emit(f"{bundle_root}/log.md", empty_log("shared"))

    for rel in created:
        print(f"作成: {rel}")
    if skipped:
        print(f"既存のためスキップ（--force で上書き）: {len(skipped)} 件")
        for rel in skipped:
            print(f"  {rel}")
    print()
    print("次の手順:")
    print(f"  1. {bundle_root}/CONVENTIONS.md の語彙を確認・調整する")
    print(f"  2. {CONFIG_FILENAME} の layer_map が実際のコード配置と合っているか確認する")
    print("  3. okf index --write で目次を生成する")
    print("  4. okf lint で規約違反が無いか確認する")
    print("  5. .gitignore に _site/ を追加する（HTML生成物）")
    return 0
