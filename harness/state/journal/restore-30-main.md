# Restore hierarchical navigation into main

- Authorized scope: restore only PR30 delta into a new main-based branch/worktree, no updates to merged PR26/30 branches, no merge/publish/Issue close.
- main c09c6eea9756c05904c6dc2f27f3f832d28e283f and original PR26 c008ed0 share tree ea86bc9c5d330b4074e35a80c64361c555caaafc. PR30 squash 9cbc557a4dffb089bfa09bcff1c7e9215bf8ebe5 sole parent c008ed0; cherry-pick into main succeeded without conflicts as 9a347a5. Initial restored tree matches squash tree48d673b3629d90dfe0b7f5e8da03c553673f8a18. Only 39-file PR30 delta restored.
- Preserve hierarchical navigation/source links, grouped backlog/kanban/search, cleanup boundaries, historical worklogs/declarations, ledger counts/priority rejection and screenshot evidence. Exact runtime blobs match original browser capture f7e8aa9; screenshots remain prior observations, not a new capture.
- PR-scope declaration now uses exact current main; historical task declarations unchanged. Local full Python/Node/compat/docs/render/PR checks pending. Parent owns independent review/push/new Draft PR/final CI.

## Local verification outcome

- Fixed restored code9a347a5: npm ci exit0; Python200 run/failure0/error0/skipped1 known Windows symlink unavailable; Node30 and compatibility13 passed including cleanup tests. Symlink boundary remains locally unverified, remote CI not inferred.
- affected identifies restored navigation/runtime docs; existing PR30 docs/logs restored with their exact delta. index --write/check latest, lint error0/warn0, render --check22pages write0/delete0/warn0 and PR declaration check succeeded. git diff --check clean and conflict-marker scan no matches (grep exit1 means no matches).
- Ledger unique11 = observations10/rejected1, counter10/10; original evidence and runtime blob identity verified. Only declaration/worklog bookkeeping differs from original squash after restoration. Parent review/new PR/push/CI pending.
