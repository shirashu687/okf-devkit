"""Staleness reports with one explicit-root Git cache per invocation."""
from __future__ import annotations
import datetime as _dt
import json
import sys
from ..code_sources import split_code_glob
from ..config import Bundle
from .. import gitutil
from ..fsutil import today, extract_date, parse_datetime
from .lint import trust_level


class _Orphan(dict):
    """Carry the local glob for sync without adding a field to the stale report."""

    def __init__(self, path: str, pattern: str, message: str):
        super().__init__(path=path, kind="orphan", level="warn", message=message)
        self.missing_local_glob = pattern


def run_stale(bundle: Bundle, *, runner=None, resource_resolver=None, commit_time=None) -> list[dict]:
    """陳腐化レポートを組み立てる。"""
    cache = gitutil.CommitTimesCache()
    results: list[dict] = []
    draft_days = int((bundle.cfg.get("stale") or {}).get("draft_days", 30))
    todays = today()
    now = _dt.datetime.now(_dt.timezone.utc)

    for doc in bundle.docs():
        if not doc.has_fm:
            continue
        path = doc.repo_rel
        generated = doc.fm.get("generated")
        gen_raw = generated.get("at") if isinstance(generated, dict) else None
        gen_dt, gen_has_time = parse_datetime(gen_raw)
        gen_at = extract_date(gen_raw)

        stale_after = extract_date(doc.fm.get("stale_after"))
        if bundle.okf03:
            freshness = doc.okf_freshness(now)
            if freshness == "stale":
                results.append({"path": path, "kind": "expired", "level": "warn",
                                "message": f"stale_after: {doc.get('stale_after')} を過ぎています"})
            elif freshness == "malformed":
                results.append({"path": path, "kind": "malformed-stale-after", "level": "warn",
                                "message": "stale_after は RFC 3339 ではありません"})
        elif stale_after and stale_after <= todays.isoformat():
            results.append({"path": path, "kind": "expired", "level": "warn",
                            "message": f"stale_after: {stale_after} を過ぎています"})

        external_sources: set[str] = set()
        for resource in doc.code_globs():
            source, _ = split_code_glob(resource)
            if source is not None:
                if source not in external_sources:
                    external_sources.add(source)
                    results.append({"path": path, "kind": "external-unverified", "level": "info",
                                    "message": f"ソース `{source}` のコード更新時刻は未検証です"})
                continue
            matched = (gitutil.resolve_resource(bundle.repo_root, resource, exclude=bundle.code_glob_exclude) if resource_resolver is None else resource_resolver(resource))
            if not matched:
                reason = gitutil.code_glob_no_match(resource, bundle.code_glob_exclude)
                results.append(_Orphan(path, resource, f"code_globs: {resource} {reason}"))
                continue
            if gen_dt is None:
                continue
            latest_raw = (gitutil.last_commit_time(bundle.repo_root, matched, cache, runner=runner) if commit_time is None else commit_time(matched))
            if not latest_raw:
                continue
            latest_dt, _ = parse_datetime(latest_raw)
            if latest_dt is None:
                continue
            if gen_has_time:
                outdated = latest_dt > gen_dt
                shown = latest_dt.astimezone(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            else:
                # generated.at が日付のみのときは日単位で比較する（誤検知を避ける）
                outdated = latest_dt.date() > gen_dt.date()
                shown = latest_dt.date().isoformat()
            if outdated:
                results.append({"path": path, "kind": "outdated", "level": "warn",
                                "message": f"{resource} の最終コミット {shown} > generated.at {gen_raw}"})

        if trust_level(doc) == "unverified":
            results.append({"path": path, "kind": "unverified", "level": "info",
                            "message": ("現在の内容に有効な verified がありません" if doc.okf03
                                        else "verified がありません（人によるレビュー未実施）")})

        if doc.status == "draft" and gen_at:
            try:
                age = (todays - _dt.date.fromisoformat(gen_at)).days
            except ValueError:
                age = 0
            if age >= draft_days:
                results.append({"path": path, "kind": "draft-stale", "level": "info",
                                "message": f"status: draft のまま {age} 日経過しています"})

    results.sort(key=lambda r: (r["level"] != "warn", r["path"], r["kind"]))
    return results


def cmd_stale(bundle: Bundle, args, *, runner=None, reporter=None) -> int:
    if gitutil.git_available(bundle.repo_root, runner=runner) and gitutil.is_shallow(bundle.repo_root, runner=runner):
        print(
            "[okf stale] 警告: shallow clone のため outdated 判定が不正確になる可能性があります。",
            file=sys.stderr,
        )
    results = (run_stale if reporter is None else reporter)(bundle)
    if args.format == "json":
        print(json.dumps(results, ensure_ascii=False, indent=2))
        return 0
    if not results:
        print("陳腐化の兆候はありません。")
        return 0
    for item in results:
        print(f"{item['path']} {item['level']} {item['kind']} {item['message']}")
    warns = sum(1 for r in results if r["level"] == "warn")
    infos = len(results) - warns
    print(f"\nstale: warn {warns} 件 / info {infos} 件")
    return 0
