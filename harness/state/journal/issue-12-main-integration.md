# Issue #12 stage1 integration with merged #32

Original task base d539e28c51c2a562f9729a07854c0fbf236438d0 retained. Integrate main17761730842870127b37a911297e128e4b852779 and stage1 HEAD5e5dea8899 without feature changes. Five documentation conflicts use previously verified combined tree2fa1cf93 as evidence; preserve both feature bodies and commit-hash logs. Historical declarations untouched. Parent owns remote operations, child commits local merge and final verification records only.

## Resolution and observed validation

Five conflicted documentation files copied byte-exact from previously verified combined commit2fa1cf93. Full `git diff 2fa1cf93 -- src node tests docs` empty: model/source/runtime/help/guidance and both feature hash logs preserved. Main37 source/help additions were automatically merged; no source assertions/features weakened or changed. No original issue12-impl worktree touched.

New PR scope exact17761730842870127b37a911297e128e4b852779 declares protected test_cli_context.py and test_fsutil.py only. First PR declaration check correctly failed because the old pure-helpers PR declaration (base d539) was still newly added relative newmain and duplicated paths. Replaced that stale PR-scoped current-tree file with the new integration declaration; historical TASK declarations remain byte-unchanged and prior PR declaration remains available in Git history. Subsequent PR check succeeds. Original d539 task check succeeds using both feature task declarations.

- Python full219 tests/failures0/errors0/skip1(existing Windows symlink permission), exit0. Evidence workspace issue12-main-integration-python.txt.
- npm ci8 packages/9audit/0vulnerabilities. Native31,compat14,package3 pass,skip0. Absolute worktree PYTHONPATH and authorized existing venv used; evidence workspace issue12-main-integration-{node,compat,package}.txt. Isolated package fixtures only; no publish.
- Python lint0error/0warn,index latest,rendercheck32pages/warn0/write0/delete0; cached whitespace/conflict checks pass. Affected against originald539 includes main37 changes: existing merged main documentation retains its valid updated bodies and stage1 docs retain their globs/semantics. Bundle-external worklogs/root guides checked separately; no unknown source change.
- Remote push/CI/PR handling and independent final-head review are parent-owned, not executed by child.

No merge/publish/deploy to GitHub; the local merge commit only integrates work into the existing Draft branch ancestry. Existing npm branch decision unchanged. No adoption/scoring change or full-retro trigger; historical ledger unchanged.
