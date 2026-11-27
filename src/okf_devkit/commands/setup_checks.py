"""Read-only checks for installed runtime and generated scaffold."""
from __future__ import annotations

import json
import re
from argparse import Namespace
from pathlib import Path

from .. import __version__, gitutil
from ..config import Bundle
from ..errors import OkfError
from ..fsutil import read_text, rel_posix
from .init import AGENT_SETTINGS, scaffold_plan


def _report_hook(root: Path, name: str, file: str) -> str:
    try:
        target = root / file
        target.resolve().relative_to(root.resolve())
        if not target.exists():
            return "未登録"
        events = json.loads(read_text(target)).get("hooks", {})
        entries = events.get("agentStop" if name == "copilot" else "Stop")
        if not isinstance(entries, list):
            return "未登録"
        if name != "copilot":
            entries = [
                entry
                for group in entries
                if isinstance(group, dict) and isinstance(group.get("hooks"), list)
                for entry in group["hooks"]
            ]
        for entry in entries:
            if isinstance(entry, dict) and any(
                isinstance(entry.get(key), str)
                and re.search(r"\.okf[\\/]hooks[\\/]agent_stop\.(?:sh|ps1)\b", entry[key])
                for key in ("command", "commandWindows", "bash", "powershell")
            ):
                return "登録あり（設定のみ確認）"
        return "OKF の登録を確認できません"
    except (ValueError, OSError, AttributeError, RuntimeError):
        return "判定不能（設定を確認してください）"


def cmd_doctor(root: Path, config: Path | None) -> int:
    print(f"CLI: okf-devkit {__version__} (Python)")
    print(f"CLI 実体: {Path(__file__).resolve().parents[1] / 'cli.py'}")
    print("導入元: 不明")
    bundle = None
    failed = False
    try:
        candidate = Bundle(config, repo_root=root)
        candidate.root.relative_to(root.resolve())
        if not candidate.root.is_dir():
            raise OkfError(f"バンドルルートがありません: {candidate.root}")
        bundle = candidate
        print("設定: 読み込み成功")
        layer_map = bundle.cfg.get("layer_map")
        if not isinstance(layer_map, list):
            raise OkfError("layer_map はリストで指定してください")
        for entry in layer_map:
            if not isinstance(entry, dict) or not all(isinstance(entry.get(key), str) for key in ("glob", "layer")):
                raise OkfError("layer_map の各項目に glob と layer が必要です")
            glob, layer = entry["glob"], entry["layer"]
            if layer == "skip":
                continue
            count = len(gitutil.resolve_resource(root, glob, exclude=bundle.code_glob_exclude))
            result = f"{count} 件一致" if count else "要確認（一致なし）"
            print(f"layer_map {layer} ({glob}): {result}")
    except (OkfError, ValueError, OSError) as exc:
        failed = True
        print(f"設定 / layer_map: 要確認 ({exc})")
    for name, file in AGENT_SETTINGS.items():
        print(f"hook {name} ({file}): {_report_hook(root, name, file)}")
    ignores = ["_site/", ".okf/render-backups/"]
    if (root / "package.json").exists():
        ignores.append("node_modules/")
    for item in ignores:
        code, _ = gitutil.git(root, "check-ignore", "--no-index", "-q", "--", item)
        result = {0: "除外済み", 1: "要確認（除外なし）"}.get(code, "判定不能（Git）")
        print(f"Git 除外 {item}: {result}")
    legacy = None
    if bundle is not None:
        try:
            legacy = [
                file
                for directory in bundle.dirs()
                for file in directory.iterdir()
                if file.suffix == ".html" and file.is_file() and not bundle.is_excluded(file)
            ]
            old_manifest = bundle.root / ".okf-render-manifest.json"
            if old_manifest.is_file():
                legacy.append(old_manifest)
            legacy.sort()
        except OSError:
            pass
    status = "判定不能（バンドル）" if legacy is None else f"{len(legacy)} 件"
    print(f"旧出力候補: {status}")
    for file in legacy or ():
        print(f"  {rel_posix(file, root)}")
    return 1 if failed else 0


def _normalize_scaffold(text: str) -> str:
    return re.sub(r"^generated:\n( {2}by:[^\n]*\n) {2}at:[^\n]*$",
                  r"generated:\n\1  at: <timestamp>", text, count=1, flags=re.MULTILINE)


def cmd_upgrade(bundle: Bundle, args) -> int:
    root = bundle.repo_root
    maps = bundle.cfg.get("layer_map") or []
    layers = []
    for name in bundle.layers:
        if name == "shared":
            continue
        glob = next((entry["glob"] for entry in maps if entry.get("layer") == name), "**")
        layers.append((name, glob, (bundle.cfg.get("layer_dirs") or {}).get(name, name)))
    plan, *_ = scaffold_plan(root, Namespace(
        bundle_root=bundle.root.relative_to(root.resolve()).as_posix(),
        site_name=bundle.site_name, agent=args.agent, runner=args.runner,
    ), layers=layers)
    counts = dict.fromkeys(("一致", "追加候補", "差分あり（手動確認）", "比較不能（手動確認）"), 0)
    for file, expected, _ in plan:
        if file == "okf.yml":
            file = rel_posix(bundle.config_path, root)
        target = root / file
        try:
            target.resolve().relative_to(root.resolve())
            if target.is_symlink() or (target.exists() and not target.is_file()):
                status = "比較不能（手動確認）"
            elif not target.exists():
                status = "追加候補"
            else:
                status = "一致" if _normalize_scaffold(read_text(target)) == _normalize_scaffold(expected) else "差分あり（手動確認）"
        except (ValueError, OSError, RuntimeError):
            status = "比較不能（手動確認）"
        counts[status] += 1
        print(f"{status}: {file}")
    print(" / ".join(f"{status} {count} 件" for status, count in counts.items()))
    return 1 if counts["比較不能（手動確認）"] else 0
