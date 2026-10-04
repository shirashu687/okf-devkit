"""Backlog aggregation with explicit project-root document construction."""
from __future__ import annotations
import json
from pathlib import Path
from ..config import Bundle
from ..doc import Doc

def backlog_docs(bundle: Bundle, *, repo_root: Path | None = None, doc_factory=None) -> list[Doc]:
    directory = bundle.backlog_dir()
    if not directory.exists():
        return []
    return [
        (Doc if doc_factory is None else doc_factory)(p, bundle.root, repo_root=bundle.repo_root if repo_root is None else repo_root)
        for p in sorted(directory.iterdir())
        if p.is_file() and p.suffix == ".md" and p.name not in bundle.reserved
    ]


def cmd_status(bundle: Bundle, args, *, reader=None) -> int:
    docs = (backlog_docs if reader is None else reader)(bundle)
    states = list(bundle.backlog_cfg.get("state_order") or ["doing", "todo", "done", "dropped"])
    priorities = list(bundle.backlog_cfg.get("priorities") or ["high", "medium", "low"])

    by_state: dict[str, list[Doc]] = {s: [] for s in states}
    for doc in docs:
        by_state.setdefault(str(doc.fm.get("state") or "todo"), []).append(doc)

    priority_counts = {
        state: {p: sum(1 for d in items if str(d.fm.get("priority") or "") == p) for p in priorities}
        for state, items in by_state.items()
    }

    if args.format == "json":
        payload = {
            "total": len(docs),
            "states": {s: len(v) for s, v in by_state.items()},
            "priorities": priority_counts,
            "doing": [{"path": d.repo_rel, "title": d.title,
                       "priority": d.fm.get("priority"), "effort": d.fm.get("effort")}
                      for d in by_state.get("doing", [])],
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    print(f"backlog: 全 {len(docs)} 件")
    for state in states + sorted(s for s in by_state if s not in states):
        items = by_state.get(state) or []
        detail = " ".join(f"{p}:{priority_counts.get(state, {}).get(p, 0)}" for p in priorities)
        print(f"  {state:<8} {len(items):>3} 件  ({detail})")
    doing = by_state.get("doing") or []
    if doing:
        print("\ndoing:")
        for doc in doing:
            chips = " ".join(f"`{doc.fm[k]}`" for k in ("priority", "effort") if doc.fm.get(k))
            print(f"  - {doc.title} {chips} ({doc.repo_rel})")
    return 0
