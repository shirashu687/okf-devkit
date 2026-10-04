# Issue32 AI daily operations and help

User authorized implementation on 2026-10-04 09:01 UTC. Start/main base `d539e28c51c2a562f9729a07854c0fbf236438d0`; dedicated branch codex/issue32-ai-operations clean at start. Do not include closed PR36 rules.

Scope: short daily operations navigation, actual read/write/result guidance, generated scaffold instructions and minimal Python/Node help corrections with regression/nonwrite tests. Preserve existing features, local npm command selection and init preserving user files. Existing #35 installation/update guide stays distinct. Root owns integration/tests/docsindex/log/journal, help author CLI/tests, docs authorguide.

Excluded: Issue/label/comment/close actions (parent worker owns), global hooks/environment, paid model calls, merge/publication, command removal. Draft first; Ready only after actual scope passes review and exacthead/base CI. Refs #32 until whole acceptance confirmed.

Verification pending: allPython,Node/compat,newtests, generatedfixture/read-only snapshots, affected/documentlint/index/render/declarations, independentStandards/Spec,latestCI. Root provenance immutable exceptexplicit verificationmetadata afterfreeze.

## Integration review

Reviewed all affected output and uncovered paths. Help changed parser/help only; navigation/backlog/cleanup rendering and existing runtime decision are unchanged by new help cases in broad test globs. Reviewed those bodies and retained them rather than mechanically refreshing generated.at. Updated actual architecture/help/scaffold guidance and linked install/accepted distribution decision to the new daily guide. Uncovered root README/AGENTS, journals and new tests were explicitly reviewed.

Targeted author evidence: Python211 fail0/error0/skip1; Node31/compat14; final help2; generated fixture5 + existing gate15 passed. Initial fixture assumptions (npm-script selection absent in current main; invalid Git baseline resolved as absent rather than forcing log skip) were corrected to current explicit local Node and a real hashless-log migration fixture; initial failures retained outside repo. No existing feature or global environment was changed. Node new --help exit2 was observed before fix and exit0/no writes after. Root final frozen suite/review/CI follows.

## Final local verification

Frozen source/docs `fd46b62b95a981e4eea1c0ded64bf85b14d6c9b3`: Python211 run/fail0/error0/skip1(existingWindows symlink); Node31 passed; compatibility14 passed; actual packed distribution3 passed. npm ci --ignore-scripts succeeded. Docs lint error0/warn0/index current/render32 pages writes0/deletes0/warn0. Protected task/PR declarations and diff checks succeeded. Logs retained outside repository as issue32-final-*.txt.

Independent Spec: 0 findings/blocking0. Independent Standards: documented violations0/blocking0, optional Duplication heuristic1 (Node help common-option epilog repeated). This optional metadata duplication is retained because current public help parity is explicitly tested; no missing behavior or requirement. Current head/base, all required execution, then remote exact-SHA CI determine Ready; no GitHub APPROVED claim. Final record changes journal only.

Retro gate: approved scope, diff, targeted failures/corrections, final suites and two-axis review were compared. Help regression red was intended TDD; fixture assumptions were corrected before acceptance without changing existing CLI behavior. No prior requirement omission, unexpected runtime regression or false success. Ordinary requested guidance work, no new permanent rule/ledger adoption. Target repo paid Stop/Release/merge are outside scope and unexecuted. Latest SHA CI and GitHub PR preparation are next; Issue state/labels remain parent worker responsibility.
