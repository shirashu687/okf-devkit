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
        settings = json.loads(read_text(target))
        if not isinstance(settings, dict):
            raise ValueError("設定の形式が不正です")
        events = settings.get("hooks", {})
        if not isinstance(events, dict):
            raise ValueError("hooks の形式が不正です")
        event_name = "agentStop" if name == "copilot" else "Stop"
        if event_name not in events:
            return "未登録"
        entries = events[event_name]
        if not isinstance(entries, list) or any(
            not isinstance(group, dict) or (name != "copilot" and not isinstance(group.get("hooks"), list))
            for group in entries
        ):
            raise ValueError("hook イベントの形式が不正です")
        if name != "copilot":
            entries = [entry for group in entries for entry in group["hooks"]]
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


def _validated_layers(bundle: Bundle) -> list[dict]:
    bundle.root.relative_to(bundle.repo_root)
    if not bundle.root.is_dir():
        raise OkfError(f"バンドルルートがありません: {bundle.root}")
    names = bundle.cfg.get("layers")
    if not isinstance(names, list) or any(not isinstance(name, str) or not name.strip() for name in names):
        raise OkfError("layers は空でない層名のリストで指定してください")
    maps = bundle.cfg.get("layer_map")
    if not isinstance(maps, list):
        raise OkfError("layer_map はリストで指定してください")
    if any(not isinstance(entry, dict) or not all(isinstance(entry.get(key), str) for key in ("glob", "layer"))
           for entry in maps):
        raise OkfError("layer_map の各項目に glob と layer が必要です")
    if not isinstance(bundle.cfg.get("layer_dirs"), dict):
        raise OkfError("layer_dirs はマップで指定してください")
    return maps


def cmd_doctor(root: Path, config: Path | None) -> int:
    print(f"CLI: okf-devkit {__version__} (Python)")
    print(f"CLI 実体: {Path(__file__).resolve().parents[1] / 'cli.py'}")
    print("導入元: 不明")
    bundle = None
    failed = False
    try:
        candidate = Bundle(config, repo_root=root)
        layer_map = _validated_layers(candidate)
        bundle = candidate
        print("設定: 読み込み成功")
        for entry in layer_map:
            glob, layer = entry["glob"], entry["layer"]
            if layer == "skip":
                continue
            count = len(gitutil.resolve_resource(root, glob, exclude=bundle.code_glob_exclude))
            result = f"{count} 件一致" if count else "要確認（一致なし）"
            print(f"layer_map {layer} ({glob}): {result}")
    except (OkfError, TypeError, ValueError, OSError) as exc:
        failed = True
        print(f"設定 / layer_map: 要確認 ({exc})")
    for name, file in AGENT_SETTINGS.items():
        print(f"hook {name} ({file}): {_report_hook(root, name, file)}")
    ignores = ["_site/index.html", ".okf/render-backups/"]
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
                if not directory.is_symlink()
                for file in directory.iterdir()
                if file.suffix == ".html" and not file.is_symlink() and file.is_file() and not bundle.is_excluded(file)
            ]
            old_manifest = bundle.root / ".okf-render-manifest.json"
            if not old_manifest.is_symlink() and old_manifest.is_file():
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
    end = text.find("\n---\n", 3) if text.startswith("---\n") else -1
    if end < 0:
        return text
    header = re.sub(r"^generated:\n( {2}by:[^\n]*\n) {2}at:[^\n]*$",
                    r"generated:\n\1  at: <timestamp>", text[:end], count=1, flags=re.MULTILINE)
    return header + text[end:]


def cmd_upgrade(bundle: Bundle, args) -> int:
    root = bundle.repo_root
    try:
        bundle_root = rel_posix(bundle.root, root)
        config = bundle.config_path.absolute().relative_to(root.absolute()).as_posix()
    except ValueError as exc:
        raise OkfError("scaffold の比較対象はリポジトリ内に指定してください") from exc
    maps = _validated_layers(bundle)
    layers = []
    log_files = {"log.md": bundle.log_path("shared")}
    for name in bundle.layers:
        if name == "shared":
            continue
        glob = next((entry["glob"] for entry in maps if entry.get("layer") == name), "**")
        directory = (bundle.cfg.get("layer_dirs") or {}).get(name, name)
        layers.append((name, glob, directory))
        log_files[f"{directory}/log.md"] = bundle.log_path(name)
    plan, *_ = scaffold_plan(root, Namespace(
        bundle_root=bundle_root,
        site_name=bundle.site_name, agent=args.agent, runner=args.runner,
    ), layers=layers, allow_repo_root=True)
    counts = dict.fromkeys(("一致", "追加候補", "差分あり（手動確認）", "比較不能（手動確認）"), 0)
    for file, expected, _ in plan:
        timestamped = file in (f"{bundle_root}/AGENTS.md", f"{bundle_root}/CONVENTIONS.md")
        if file == "okf.yml":
            file = config
        elif file.startswith(bundle_root + "/"):
            log_file = log_files.get(file[len(bundle_root) + 1:])
            if log_file is not None:
                file = log_file.relative_to(root).as_posix() if log_file.is_relative_to(root) else str(log_file)
            elif bundle_root == ".":
                file = file[2:]
        target = root / file
        try:
            target.resolve().relative_to(root.resolve())
            if target.is_symlink() or (target.exists() and not target.is_file()):
                status = "比較不能（手動確認）"
            elif not target.exists():
                status = "追加候補"
            else:
                actual = read_text(target)
                if timestamped:
                    actual, expected = _normalize_scaffold(actual), _normalize_scaffold(expected)
                status = "一致" if actual == expected else "差分あり（手動確認）"
        except (ValueError, OSError, RuntimeError):
            status = "比較不能（手動確認）"
        counts[status] += 1
        print(f"{status}: {file}")
    print(" / ".join(f"{status} {count} 件" for status, count in counts.items()))
    return 1 if counts["比較不能（手動確認）"] else 0
