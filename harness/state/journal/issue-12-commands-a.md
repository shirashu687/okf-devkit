# Issue #12 stage5a: index/log/lint

Base: `cf00bece3e1719eb799b5e78eab63a32e0236127`. Extract commands individually, retaining legacy CLI adapters; canonical commands never import CLI. Each command receives full Python and compatibility checks before its commit.

## index extraction
Canonical commands/index.py owns marker preflight and generation, using Bundle.repo_root. CLI adapters retain the current root and writer override. Reserved/index Doc construction explicitly receives the bundle root owner. New owner-isolation tests: 2 pass. Full Python: 240 run, failures 0, errors 0, skipped 1 (existing symlink constraint). Compatibility: 13 pass. npm ci --ignore-scripts succeeded. check_changes task and diff --check passed. Evidence: task/issue12-commands-a-index-python.log and -index-compat.log.


## log extraction
Canonical commands/log.py routes all Git calls through explicit Bundle.repo_root and optional runner; legacy CLI forwards current root/git/writer. Pure formatting/routing/hash helpers remain CLI exports. Canonical owner-root and legacy Git/writer observations pass. Full Python: 242 run, failures 0, errors 0, skipped 1. Compatibility: 13 pass. Evidence: task/issue12-commands-a-log-python.log and -log-compat.log.


## lint extraction
Canonical commands/lint.py owns Finding, trust and convention checks; resource resolution and reserved/index Doc construction use Bundle.repo_root. Legacy run_lint forwards the current resource/index callbacks, and cmd_lint retains the current linter override. Full Python: 243 run, failures 0, errors 0, skipped 1. Compatibility: 13 pass. Node native/cleanup: 30 pass. Evidence: task/issue12-commands-a-lint-python.log, -lint-compat.log, -final-node.log.

## Failures detected and corrective audit
The first index full run failed because three reserved/index Doc callsites still omitted canonical Doc's required repo_root. The first lint full run repeated this omission in two reserved index/log Doc callsites; the focused 37-case lint suite reported eight errors. Both were TypeError failures, not successful runs. All five callsites now explicitly receive Bundle.repo_root. An AST audit of every Doc constructor in the extracted commands verified the keyword at every callsite, followed by the unchanged existing tests and full/compatibility suites. Earlier failed full logs were overwritten by their corrected reruns, so no unsupported first-run aggregate counts are claimed. For stage5b, audit all Doc/Bundle constructors and mutable-owner callsites before the first full run. No repository-wide rule or skill change was introduced.
