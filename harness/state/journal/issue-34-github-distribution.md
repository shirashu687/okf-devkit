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

## Implementation freeze

Source/docs implementation commit: `a043c6c254a6b7fbe57b70a073958717a28ce34b`. Added tag-only production Draft workflow and separate no-tag PR CI provenance. PR CI packs once on Ubuntu and existing Windows/Linux Node 22/24 jobs consume the same verified archive. Package synthetic rollback/hostile environment fixtures remain separate tests; they do not represent real historical Release compatibility. Targeted author tests passed: release guards 14, package distribution 3. Final mandatory full suites, docs checks, declarations and exact-SHA independent reviews are next.

## Final local verification

Verified source/docs freeze `7ad1a43d71d5090185625d67204cc528873d68ad` using the existing Python environment with this worktree's src explicitly selected. Python full suite: 205 run, 0 failures/errors, 1 skip; Node native: 30 passed; compatibility: 13 passed; release guards: 14 passed; package distribution: 3 passed. npm ci --ignore-scripts succeeded. Lint: 0 errors/warnings; index current; render --check: 31 pages, 0 writes/deletes/warnings. Task and pull-request declarations both result=ok; diff whitespace check clean.

Independent final implementation reviews: Standards 0 findings, Spec 0 findings, fixed base `195252d3354acece9c72c987a9f0ab6559db6aa3`. Local logs are retained outside the repository as issue34-final-*.txt. This final journal addition only records verification; it changes no source/docs behavior. Exact final-SHA remote CI remains pending until the Draft PR is created. Actual target tag/Release API writes, historical Release compatibility and paid agent Stop turns remain unexecuted.
