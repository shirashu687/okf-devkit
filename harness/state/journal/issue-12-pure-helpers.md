# Issue12 stages0/1: context regression and pure helpers

- Base: d539e28c51c2a562f9729a07854c0fbf236438d0
- Scope: fix context regression coverage before extracting shared errors and pure path/file/date/glob helpers. Preserve cli public exports, class identity, root injection and YAML backend seam; no command or Node restructuring.
- Verification: targeted regression red/green then fullPython, Node native/compat, docs affected/index/lint/render and task/PR checks. Independent review, push and CI parent-owned.
- Remaining: YAML, Doc/config, Git, commands and <=200line entry stages; first stage does not complete Issue12.

## Regression and implementation

- Authoritative stage0 baseline:4 context tests, one genuine failure at real second-repository Git cache; root/config/CWD and observed mini/PyYAML backend seams passed. Initial test construction used incorrect Doc arguments and absolute source expectation; corrected before authoritative red evidence. Same-root repeated main after real new commit also failed before per-invocation invalidation and passed after.
- errors owns OkfError/MarkerError; fsutil owns rel_posix/read_text/atomic_write_bytes/write_if_changed/today/now_iso/ISO_DATE_RE/is_iso_date/extract_date/parse_datetime/glob_to_regex/path_matches/_GLOB_CACHE. cli reexports exact function/class/cache objects; _pyyaml/REPO_ROOT and YAML subclasses remain actual cli owners.
- Git cache remainscli-owned, keyed to root for direct injection and invalidated at each main invocation. Package asset path resolution remains package-relative; no chdir. Targeted5context+3ownership tests successful. First broader run212/fail0/error0/skip2, Node30/compat13 successful; after added same-root regression new complete run required below.
