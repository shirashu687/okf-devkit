"""Project scaffolding using explicit project and installed-package asset roots."""
from __future__ import annotations
import os
import re
from pathlib import Path
from ..config import CONFIG_FILENAME
from ..errors import OkfError
from ..fsutil import now_iso, write_if_changed
from ..yamlio import yaml_flow_list, yaml_scalar

SCAFFOLD_DIR = Path(__file__).resolve().parents[1] / "scaffold"
AGENT_SETTINGS = {
    "claude": ".claude/settings.json",
    "codex": ".codex/hooks.json",
    "copilot": ".github/hooks/okf-render.json",
}


def _selected_agents(value: str | None) -> list[str]:
    if value is None or value == "all":
        return list(AGENT_SETTINGS)
    if value == "none":
        return []
    names = [name.strip() for name in value.split(",")]
    if any(name not in AGENT_SETTINGS for name in names) or len(set(names)) != len(names):
        raise OkfError("--agent は claude,codex,copilot から選ぶか、all / none を指定してください")
    return names

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
        if not sep or not name:
            raise OkfError(f"--layer の書式が不正です（name=glob[:dir]）: {spec}")
        glob_part, _, dir_part = rest.partition(":")
        glob_part = glob_part.strip()
        dir_part = dir_part.strip() or name
        if not re.fullmatch(r"[a-z0-9][a-z0-9_-]*", name):
            raise OkfError(f"層名は英小文字・数字で始め、英小文字・数字・- _ を使用してください: {name}")
        if name in seen:
            raise OkfError(f"層名が重複しています: {name}")
        if name == "shared":
            raise OkfError("`shared` は層をまたぐ知識用に予約されています")
        if not glob_part:
            raise OkfError("層の glob が空です")
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
    dir_lines = [f"  {yaml_scalar(n)}: {yaml_scalar(d)}" for n, _g, d in layers]
    dir_lines.append("  shared: project")
    map_lines = [
        f"  - {{ glob: {yaml_scalar(g)}, layer: {yaml_scalar(n)} }}"
        for n, g, _d in layers
    ]
    map_lines.append(f"  - {{ glob: {yaml_scalar(bundle_root + chr(47) + chr(42) * 2)}, layer: skip }}")
    map_lines.append('  - { glob: "**", layer: shared }')
    # log.paths は log: > paths: の下なのでインデントは4スペース
    log_path_lines = [f"    {yaml_scalar(n)}: {yaml_scalar(d + '/log.md')}" for n, _g, d in layers]
    log_path_lines.append("    shared: log.md")

    return (_scaffold_text if scaffold_reader is None else scaffold_reader)("okf.yml.tmpl").format(
        bundle_root=yaml_scalar(bundle_root),
        site_name=yaml_scalar(site_name),
        root_heading=yaml_scalar(f"{site_name} ドキュメント"),
        layers="\n".join(layer_lines),
        layer_dirs="\n".join(dir_lines),
        layer_map="\n".join(map_lines),
        log_layers=yaml_flow_list(names),
        log_paths="\n".join(log_path_lines),
    )


def scaffold_plan(repo_root: Path, args, *, layers=None, scaffold_dir: Path | None = None, scaffold_reader=None, config_renderer=None):
    """新規初期化と差分確認で共用する、書き込みを伴わない生成計画。"""
    repo_root = Path(repo_root)
    scaffold_dir = SCAFFOLD_DIR if scaffold_dir is None else scaffold_dir
    if scaffold_reader is None:
        scaffold_reader = lambda rel: _scaffold_text(rel, scaffold_dir=scaffold_dir)

    if layers is None:
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
    agents = _selected_agents(getattr(args, "agent", None))
    raw_runner = getattr(args, "runner", None)
    runner = "okf" if raw_runner is None else raw_runner.strip()
    if not runner or re.search(r"[|\x00-\x1f\x60\x7f]", runner):
        raise OkfError("--runner には1行の実行表記を指定してください（バッククォートと | は使用不可）")
    has_node_deps = (repo_root / "package.json").is_file() and (repo_root / "node_modules").is_dir()
    plan: list[tuple[str, str, str]] = []

    def emit(rel: str, text: str, *, preserve: str = "") -> None:
        plan.append((rel, text, preserve))

    layer_table = "\n".join(
        f"| `{bundle_root}/{d}/log.md` | `{g}` の変更 |" for _n, g, d in layers
    ) or "| （層を定義していません） | — |"
    tokens = {
        "GENERATED_AT": now_iso(),
        "RUNNER": runner,
        "LAYER_EXAMPLE": " | ".join([name for name, _glob, _dir in layers] + ["shared"]),
        "BUNDLE_ROOT": bundle_root,
        "SITE_NAME": site_name,
        "LAYER_LIST": "、".join(n for n, _g, _d in layers) or "（層なし）",
        "LAYER_DIRS": " ".join(f"`{d}/`" for _n, _g, d in layers) or "—",
        "LAYER_TABLE": layer_table,
    }

    def expand(text: str) -> str:
        return re.sub(r"\{\{([A-Z_]+)\}\}", lambda m: tokens.get(m[1], m[0]), text)

    emit(CONFIG_FILENAME, (_render_okf_yml(bundle_root, site_name, layers, scaffold_reader=scaffold_reader) if config_renderer is None else config_renderer(bundle_root, site_name, layers)))
    emit(f"{bundle_root}/AGENTS.md", expand(scaffold_reader("AGENTS.md.tmpl")))
    emit(f"{bundle_root}/CONVENTIONS.md", expand(scaffold_reader("CONVENTIONS.md.tmpl")))

    for tmpl in sorted((scaffold_dir / "templates").glob("*.md")):
        emit(f"{bundle_root}/_templates/{tmpl.name}", expand(scaffold_reader(f"templates/{tmpl.name}")))
    for hook in sorted((scaffold_dir / "hooks").iterdir()):
        emit(f".okf/hooks/{hook.name}", scaffold_reader(f"hooks/{hook.name}"))
    if agents:
        for name in ("agent_stop.sh", "agent_stop.ps1"):
            emit(f".okf/hooks/{name}", scaffold_reader(f"agent-hooks/{name}"))
    for name in agents:
        template = "claude-windows" if name == "claude" and os.name == "nt" else name
        emit(AGENT_SETTINGS[name], scaffold_reader(f"agent-hooks/{template}.json"), preserve="settings")
    ignore = "/_site/\n/.okf/render-backups/\n" + ("/node_modules/\n" if has_node_deps else "")
    emit(".gitignore", ignore, preserve="ignore")

    def empty_log(layer_name: str) -> str:
        return (
            f"# 変更履歴 — {layer_name}\n"
            "\n"
            f"<!-- `{runner} log --write` が git 履歴からここに追記する。"
            "書式は /CONVENTIONS.md §7 を参照。 -->\n"
        )

    for name, _glob, directory in layers:
        emit(f"{bundle_root}/{directory}/log.md", empty_log(name))
    emit(f"{bundle_root}/log.md", empty_log("shared"))
    return plan, bundle_root, runner, agents, has_node_deps


def cmd_init(repo_root: Path, args, *, scaffold_dir: Path | None = None, scaffold_reader=None, writer=None, config_renderer=None) -> int:
    """リポジトリに OKF バンドルと設定一式を生成する。"""
    repo_root = Path(repo_root)
    plan, bundle_root, runner, agents, has_node_deps = scaffold_plan(
        repo_root, args, scaffold_dir=scaffold_dir, scaffold_reader=scaffold_reader,
        config_renderer=config_renderer,
    )
    for rel, _text, _preserve in plan:
        try:
            (repo_root / rel).resolve().relative_to(repo_root.resolve())
        except (ValueError, RuntimeError) as exc:
            raise OkfError(f"指定範囲の外には作成できません: {rel}") from exc

    created: list[str] = []
    skipped: list[str] = []
    skipped_settings: list[str] = []
    skipped_ignore: list[str] = []
    for rel, text, preserve in plan:
        path = repo_root / rel
        if (path.exists() or path.is_symlink()) and (preserve or not args.force):
            (skipped_settings if preserve == "settings" else skipped_ignore if preserve == "ignore" else skipped).append(rel)
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        (write_if_changed if writer is None else writer)(path, text)
        created.append(rel)

    for rel in created:
        print(f"作成: {rel}")
    if skipped:
        print(f"既存のためスキップ（--force で上書き）: {len(skipped)} 件")
        for rel in skipped:
            print(f"  {rel}")
    if skipped_settings:
        print("既存のエージェント設定は保持しました（--force でも上書きしません）:")
        for rel in skipped_settings:
            print(f"  {rel}")
        print("必要なら既存設定に .okf/hooks/agent_stop を手動で登録してください。")
    if skipped_ignore:
        paths = "/_site/、/.okf/render-backups/" + ("、/node_modules/" if has_node_deps else "")
        print(f"既存の .gitignore は保持しました。{paths} の除外を確認してください。")
    print("エージェント設定の対象: " + (", ".join(agents) or "なし"))
    print("共通の HTML 生成スクリプト: .okf/hooks/render_hook.sh / .ps1")
    if agents:
        print("利用するエージェントで hook の信頼設定と実行権限を確認してください。")
    print()
    print("次の手順:")
    print(f"  1. {runner} index --write で目次を生成する")
    print(f"  2. {runner} lint で規約を確認する")
    print(f"  3. {runner} render で HTML を生成する")
    print(f"  必要な場合だけ {CONFIG_FILENAME} と {bundle_root}/CONVENTIONS.md を調整する")
    print("  エージェント設定と .gitignore の出力を確認する")
    return 0
