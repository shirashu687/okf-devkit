# Issue #34 GitHub distribution and AI installation

## Authorization and scope

User approved the agreed design, implementation and Draft PR on 2026-10-04 07:14 UTC (「進めて下しあ」). Fixed task/PR base: `195252d3354acece9c72c987a9f0ab6559db6aa3`.

Implement GitHub Node tarball distribution workflow, real packed-artifact verification, README and AI installation/update/recovery instructions. Record domain terms and the accepted trade-off in the existing context/decision structure.

No actual tags, GitHub release writes/publication, npm publication, PR merge, user global environment/PATH/credentials/permissions changes. Temporary global prefixes only. Do not add an automatic updater, install-time init/hooks, or CLI managed-scope migration.

## Agreed design

GitHub distributes versioned tgz; dependencies may come from npm. Node >=22/npm/Git are prerequisites. Repo-local fixed versions are standard, global optional. AI updates a specified version only on request. Tags trigger tests, one pack, same-artifact Windows/Linux verification and Draft Release; humans publish. AI applies limited reviewed managed-scope changes while preserving user edits; package rollback and generated/settings rollback are separate.

## Work and verification

Implementation in progress. Fixed-base protected declarations prepared before changes. Final full Python/Node/compatibility, real tgz smoke, docs checks and independent Spec/Standards reviews pending. Final SHA CI pending. Actual GitHub tag-to-Draft-Release write end-to-end deliberately unexecuted.

## Contributors

Root owns Issue record, worklog/declarations, CI/package scripts integration, indices/logs and final PR/CI. Workflow author owns release workflow/helpers. Package author owns smoke/fixture tests. Docs author owns README, glossary, decision and AI guide. Shared-worktree commits are coordinated by root.

## Review findings and retrospective

Independent prereview identified inherited npm global/prefix settings that could redirect a supposedly isolated install. Before publication, the package smoke author removed inherited npm configuration/token variables case-insensitively, passed explicit temporary scopes, and verified a hostile-prefix sentinel remained unchanged. The PowerShell execution-policy override was also removed. Release uploads now recheck draft/identity/source/bytes before each write; the API lacks an atomic draft-only predicate, so human publication waits until the complete workflow finishes.

Full retrospective gate: triggered by an isolation requirement gap found in independent review. Compared approved scope, source changes and targeted tests. Recorded the third independent environment-initialization observation under existing IMP-0005; active ledger remains 10, trials 0, adopted permanent rules 0. Real user-global files/settings were not modified. Actual Release write end-to-end remains intentionally unexecuted.

Fixed Git SHA `195252d3354acece9c72c987a9f0ab6559db6aa3` initial installation and a separate empty-cache npm ci succeeded on Windows with no Git URL rewrite, SSH credentials or interactive authentication. Lockfile bytes were retained despite npm normalizing resolved to git+ssh. Transport internals and all other npm/OS combinations were not observed. Evidence: task workspace issue34-github-install-evidence.json and associated logs (outside repository).
