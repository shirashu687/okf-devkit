# Issue12 stages0/1: context regression and pure helpers

- Base: d539e28c51c2a562f9729a07854c0fbf236438d0
- Scope: fix context regression coverage before extracting shared errors and pure path/file/date/glob helpers. Preserve cli public exports, class identity, root injection and YAML backend seam; no command or Node restructuring.
- Verification: targeted regression red/green then fullPython, Node native/compat, docs affected/index/lint/render and task/PR checks. Independent review, push and CI parent-owned.
- Remaining: YAML, Doc/config, Git, commands and <=200line entry stages; first stage does not complete Issue12.

## Regression and implementation

- Authoritative stage0 baseline:4 context tests, one genuine failure at real second-repository Git cache; root/config/CWD and observed mini/PyYAML backend seams passed. Initial test construction used incorrect Doc arguments and absolute source expectation; corrected before authoritative red evidence. Same-root repeated main after real new commit also failed before per-invocation invalidation and passed after.
- errors owns OkfError/MarkerError; fsutil owns rel_posix/read_text/atomic_write_bytes/write_if_changed/today/now_iso/ISO_DATE_RE/is_iso_date/extract_date/parse_datetime/glob_to_regex/path_matches/_GLOB_CACHE. cli reexports exact function/class/cache objects; _pyyaml/REPO_ROOT and YAML subclasses remain actual cli owners.
- Git cache remainscli-owned, keyed to root for direct injection and invalidated at each main invocation. Package asset path resolution remains package-relative; no chdir. Targeted5context+3ownership tests successful. First broader run212/fail0/error0/skip2, Node30/compat13 successful; after added same-root regression new complete run required below.

## Stage0/1 freeze verification

- Final full suite: Python213/failure0/error0/skip1 (test_render_cleanup symlink unavailable), Node30/30 and compatibility13/13 successful. npm ci succeeded in the isolated worktree. Earlier run212/skip2 preceded the added same-root regression and is not the final claim.
- Docs affected inspected; moved code paths are covered by architecture/migration globs. Affectedcli/render/scaffold prose and UTC timestamps updated; corresponding layer logs cite actual implementation commit8981af1. Index write/check successful, lint error0/warn0, render check31pages/write0/delete0/warn0. Task-scope check succeeded before record commit; final commit task/PR checks below.
- Remaining stages2-6: actual YAML owner, Doc/config explicitroot, Git context, commands then <=200line parser/entry. Stage1 cli is2785lines; no line-compression trick and no claim Issue12 complete.
- Retro: authoritative expected-red cache regressions are normal TDD evidence. Initial fixture construction mismatch was corrected and distinguished from product failure. No permanent rule adoption/trial or external action performed; ledger adoption deadlines/cap unchanged. Independent spec/standards review and remote CI pending. Next step: parent-review/freeze then child YAML branch authorized separately.
