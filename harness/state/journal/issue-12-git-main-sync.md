# Stage4 updated-parent integration

Original immutable author base/head: cf00bece3e1719eb799b5e78eab63a32e0236127. Actual task/PR comparator: 497fe05d813c1b5ecd0da3a39c410129614fcc33.

Normal merge preserves both histories, imported main guide/help/model/YAML behavior and original Git owner/tests. Own old current-tree stage4 declarations replaced; historical commits and original author worktree untouched; inherited declarations retained. Before merge, actual protected difference declared as tests/test_gitutil.py only. Verification and independent review pending.

## Merge and preservation evidence

Merge source commit71717331653a747dad34c23c7c0fa99f778eb16f, parents own declaration02aefe6 and updated-model497fe05. Conflicts only document generated timestamps and CLI/scaffold logs; both sides entries retained, no runtime conflict. Original gitutil.py/test_gitutil.py blobs equal immutablecf00; every imported parent tests/Node/journal declaration/model/YAML/scaffold/operate-guide blob equals497fe05. All non-Git CLI functions/classes have identical AST to parent, including help/guide logic. No sourcefeature change.

Affected includes operate-okf guide plus 5 owner docs; purpose-oriented guide reviewed and retained without inserting implementation notes or mechanically changing timestamps. Owners/globs/current stage4 and historical stage3 separation preserved; architecture/migration body updated legitimately with actual UTC. Layer logs CLI/render/scaffold cite real merge source7171733. Final verification and independent review pending.

## Final local validation

After npm ci completed and all runtime/doc/log content was finalized: full Python244/fail0/error0/skip1 exit0 (test_render_cleanup.CleanupTests.test_symlink_rejected, Windows symlink unavailable); Node31/compat14 allpass/fail0/skip0 exit0. npm ci exit0. Package helpers and packaging configuration unchanged from verified parent, package test not rerun for this Git-only integration.

index --write/check latest; lint error0/warn0; render --check32pages/write0/delete0/warn0. Actual task/PR base497fe05 complete working-tree scope both exit0; committed final scope/diff checks follow freeze. Both CLI/render/scaffold logs original and parent entry lines verified retained. Final metadata-only commit changes actualsourceSHA logs/journal, no runtime/tests/body changes; full suite remains applicable. No GitHub ops or original author worktree changes. Independent exact-SHA reviews and remote CI parent-owned pending.

Evidence SHA256:
- issue12-git-main-sync-npmci.txt: 01c137dca38a3485908bd4ffb35006faa59909102a758ca16cb580effbd88330
- issue12-git-main-sync-python.txt: f94c7513ecf7d822f5c13852ee645d2be4188511875c4ff726c3bc20fae4fc70
- issue12-git-main-sync-node.txt: 3780c772eecf188cb2af207463977cbca78980ba651683ea559729b63a3b2c26
- issue12-git-main-sync-compat.txt: b31484297aa9ae39949c7976452213934d61cdf57824393f33ce761864158260
- issue12-git-main-sync-affected.txt: 60fc6f8e9498885c80aca8e3170a23748332310a7dba0c3bec7fa92006abdcc0
