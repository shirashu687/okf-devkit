# 作業記録: Issues 4 / 5 self docs

## メタデータ

- 課題: #4 / #5。状態: PR準備完了。
- ブランチ: codex/self-docs-ci。開始 SHA: 9d72e0e5798883d81789582d8879f139865d37b5
- 作業場所: 独立 worktree okf-docs-ci。開始時変更なし。
- 作業者: Codex / GPT-6。

## 目的・範囲と判断

Issue #4 の4本文と #5 の self-check CI を追加する。既存 npm 未統合ブランチは読取のみで、そこにある配布・案内変更を取り込まない。merge/release とグローバル hook の変更は対象外。

コードを確認した結果 render --check は HTML 差分チェックではなくメモリ内生成検査。CI はクリーン checkout で直接実行でき、生成 HTML の Git 除外を維持する。stale は参考出力、lint は通常モードを採用する。

## 検証

| 検査 | 結果 | 証拠・対象 |
|---|---|---|
| index --write / --check | 成功 | 3目次更新、全目次最新 |
| lint | 成功 | error 0 / warn 0 |
| render --check | 成功 | 23ページ、書込0、削除0、warn0 |
| affected --paths cli.py ci.yml | 成功 | architecture/commands/scaffold reference の対応を表示 |
| tests/run_all.py | 成功 | 169件、失敗0、エラー0、スキップ0 |
| 二軸独立 review | 成功 | 仕様軸0件、標準軸P2対象版記録修正済み |
| task 宣言検査 | 成功 | workflow変更を宣言済み |
| PR 宣言検査 | 成功 | 1f3df5064b81451d0abc03b3a08ad71d9dcf5cf5でexit0 |
| 最新 SHA CI | 未実行 | Draft PR作成後確認 |

既存指定 venv の Python を読取利用し、PYTHONPATH=worktree/src で対象実装を特定する。

## 摩擦観測と retro ゲート

開始時に手順と ledger を確認。評価中5 / 試行0 / 採用0、期限未定。CIと仕様・差分・検証・reviewを最後に照合する。通常のドキュメント追加と事実確認はトリガーなし。最終reviewとCIは未確認、次の一手は確認結果の追記。

## 次の一手

必須テストと二軸review完了後、宣言検査を通し Draft PR と最新 SHA CI を確認する。Issueはmerge前にはcloseしない。

## 再試行履歴

- ログ追記後の lint: warn1（sharedログ日付順）を検出し、最新日付を先頭へ移動して再検査する。初回の本文 lint warn0とは別対象版。

- log --write --range main..HEAD: 手書きのhashなしエントリにより初回4層が失敗。記録済み変更を一意に特定する036d60aを手書きエントリへ追加して再検査する。

## full retrospective

依頼・Issue4/5・実差分・検証記録を照合し、ログ更新時の要件不適合修正をretroトリガーとして判定。IMP-0011へ一件の観測として記録した。原因は仮説、恒久採用・試行開始なし。最新ログは4層の log --write --range main..HEAD すべてexit0、lint0/0。対象外のnpm未統合作業や環境権限は変更しない。

追加検証: 一時コピーのcli/indexを古くすると index --check exit1。追跡HTMLなし。task/PR宣言検査成功（比較元は開始SHA）。

## 独立 review と対象版の固定

- 仕様軸: 親担当が開始SHAから全16差分を確認し、4本文とself-checkの要件充足、scope追加なし、HTML未追跡を確認。指摘0。後続Issue6/7/11/17との統合時はaffected文書を再更新する。
- 標準軸: investigate担当が1f3df50とclean working treeを独立確認。コード規約・frontmatter・生成物・宣言に指摘なし。P2の検証対象版明記をこの節で修正。
- 初回本文検査と169件Pythonテスト: 開始SHA + 4本文/self-check/索引差分（commit036d60aへ記録した内容）。
- ログ日付順warn1→0/0およびhashなしlog失敗→4層exit0: 036d60aの手書きログにhashを加えた作業差分。修正は1f3df50に記録。
- 最新コード・文書検証対象: 1f3df50（git rev-parse HEADで確認した実装・ログ版）＋このworklogの証拠追記のみ。新規runtime変更なし。必須テストを再実行し最終結果を下記へ追記する。

- 最終ローカル: 対象1f3df5064b81451d0abc03b3a08ad71d9dcf5cf5、worktreeは本証拠追記のみ。Python全169件成功、lint0/0、index最新、render23ページ書込0/warn0、task/PR宣言検査exit0。この後はworklogのみcommitし、最新SHAのCIを別途確認する。

## PR #24 main integration (2026-10-03)

- Merged origin/main 98373cc without rewriting history. Preserved both log entries and ledger observations; evaluation count is 7/10. PR-scope declaration base now matches the complete main SHA; historical task declarations remain intact.
- Local validation: Python 170/170, Node 12/12, compatibility 7/7 successful; docs index --write/--check successful, lint error0/warn0. Compatibility was retried after setting absolute worktree PYTHONPATH and PYTHONUTF8=1; PR24 also required npm ci before Node tests.
- Start-SHA task-scope check cannot accept imported historical declarations with different bases; those declarations were preserved rather than rewritten. PR-scope comparison is the integration gate.
- Claude actual session event remains outside the requested scope. Independent review and final remote CI are separate pending observations; no merge/publish performed. Retro: existing observations preserved, no new trial or adopted rule.

## PR #24 subsequent main integration (2026-10-03)

- Remote PR was OPEN and matched the previous local reviewed SHA before changes. Merged main a16842f02e71a26849f5c094a32653c23af22640 without history rewrite. Preserved both log entries; node-runtime generated timestamp, where conflicted, uses the later main value. Ledger observations are unchanged and counts match the retained rows. Historical task declarations remain intact.
- Local validation on the integrated tree: Python173/173, Node13/13, compatibility7/7 successful; docs index --write/--check successful, lint error0/warn0. npm ci completed in the design worktree before Node tests. PR-scope change check and conflict/diff checks run after commit; independent review and final remote CI remain separate pending observations.
- Retro: no new trial or adopted rule. No merge/publish/Issue close; Claude actual session remains excluded.

## New doc reference follow-up (2026-10-03)

- Reviewed remote PR24 OPEN/head ce410dc, then corrected commands.md to match merged Issue7: four exact required types, multiple --code-globs, optional types may omit, body completion followed by index --write then lint. generated.at uses actual UTC. Documentation commit189eae4 is referenced by the layer log. No code or Node assets changed.
- Python full suite and docs index/lint/check rerun; final PR-scope change check after commit. Node/compat prior integrated results remain separately recorded; not rerun for this prose-only change. Independent review and final SHA CI pending.

## PR #22 main integration (2026-10-03)

- Confirmed PR24 OPEN at remote/local head0e0cbea and clean worktree, then merged exact main5ce845a4deb454919fdec92d5cdff2105dcbc7df. Preserved both cli/render log entries and IMP0011/IMP0009 observations; ledger count is8/10. Both runtimes, browser helper and all imported tests retained. PR-scope base updated; historical task declarations unchanged.
- Updated commands.md to describe --open and browser suppression for check/hook, with actual UTC generated timestamp. No npm development branch edits, rebase or force update.
- Local Python/Node/compat and docs verification results are recorded after completion below; independent review, push and final remote CI pending. Retro retains existing observations without new trial/adoption.

- Verification completed: existing Python176/176, npm ci successful, Node15/15 and compatibility7/7 successful using existing venv, absolute worktree PYTHONPATH and PYTHONUTF8=1. Docs index --write/--check successful, lint error0/warn0. Final PR-scope declarations and diff/conflict checks run on the committed head. Remote CI remains unobserved for this new head.

## PR #31 main integration (2026-10-03)

- Confirmed PR24 OPEN with matching remote/local c53c8b2, then merged exact main50380b3d3a22507b2bd2e329e1d206141ce2432e. Preserved both log entries, all cleanup implementation/tests and CI compatibility entry; regenerated the render index rather than choosing one side. Ledger retains10 observations within the10-item cap, no silent drops/trials/adoption.
- Updated commands/render architecture for CLI_site versus unchanged low-level API default and explicit-only cleanup with safety-contract links. Hash/manifest/receipt/rollback, raw Windows path checks and main AI instructions retained. PR-scope base updated; historical task declarations unchanged. npm development branch untouched.
- Verification results appended after completion. Independent review/push/final remote CI pending; no merge/publish/Issue close performed.

- Verification: Python196 tests, failure0/error0/skip1 (symlink unavailable on this Windows environment); Windows raw alias/manifest tests ran. npm ci successful; Node25/25, compatibility11/11 successful, including cleanup suites. Docs index --write/--check and lint error0/warn0 successful; render --check wrote/deleted0 files and reported warn0. npm pack --dry-run completed; cleanup implementation/tests/package scripts and CI compatibility entry retained. Affected report inspected: imported main documents retained; PR24 references aligned to current CLI semantics. Final committed-head PR-scope/diff/conflict checks below. Independent review and final CI pending.

## Backlog overview main integration (2026-10-04)

- Confirmed PR24 OPEN/Ready remote/local3915599 with clean worktree, merged exact mainc09c6eea9756c05904c6dc2f27f3f832d28e283f. Preserved both log entries and all backlog list/optional kanban/search/readonly features, runtime assets/tests and existing self-check CI. PR-scope base matches exact main; historical task declarations untouched.
- Ledger reconciliation initially contained11 distinct observations. Per parent review instruction, IMP0002 is priority-rejected as an isolated low stale-instruction mismatch already fixed in T0006 with no recorded recurrence/trial/adoption. Original row/date/count/detail/evidence retained in rejection history; reevaluate same ID on recurrence. Evaluation10/rejection1/total11, IMP0011/12 stay distinct; cleanup safety14/15 retained. No adoption or silent drop.
- Validation: existing Python199 tests, failure0/error0/skip1 (Windows symlink unavailable); npm ci successful, Node28/28 and compatibility12/12 successful. Docs index --write/--check successful, lint error0/warn0; render --check25 pages writes0/deletes0/warn0. Final-head PR declaration/diff/marker checks below. Independent review, push and final remote CI pending. PR remains Ready; no PR edit/push/merge/publish, no PR25 changes.

## Final main synchronization and verification (2026-10-04)

- Confirmed PR24 OPEN Ready with matching remote/local4ff229f, merged exact mainf0edc9f8c7649f888f24f310b0837683f53fd5d9 at checkpoint2b395222270726704455356a8a30535d3afd5c33. Both log histories, viewer navigation, advisory hooks, backlog, cleanup safety/tests and self-check CI retained. Historical task declarations unchanged; PR declaration base matches actual main.
- Main ledger preserves updated occurrence counts5/12 and rejected2/8. Own IMP0011 is priority-rejected as a low corrected one-off with no recorded recurrence/trial/adoption; original ID/row/detail/evidence retained, reconsider same ID on recurrence. Active10/rejected3/total13. No silent drop or permanent rule adoption.
- Six protected imports (.claude/settings.json, .codex/hooks.json, three existing runtime test files and tests/test_repo_hooks.py) have main-identical Git blobs and coverage in historical declarations. All19 original task declaration Git blobs remain identical. Initial physical-byte comparison was invalidated by working-tree CRLF normalization; corrected comparison uses Git object IDs, not changed declaration content.
- Original start4ff229f to checkpoint task machine check exit1 invalid: imported historical same-scope bases/duplicate paths conflict. Not reported successful; manual protected-import coverage/main-blob equality is distinct evidence. Post-checkpoint verification task contains metadata only and uses checkpoint as fixed base; actual PR check uses mainf0edc9f and full head. Checker/policy unchanged.
- Local suite: existing Python205 tests fail0/error0/skip1 (Windows symlink unavailable); npm ci successful, Node30/30, compatibility13/13 successful. Docs index write/check and lint error0/warn0 successful; render --check27 pages/write0/delete0/warn0. Affected against actual main inspected; runtime imports match main, no new implementation code in PR scope. Final task/PR checks after metadata commit, independent spec/standards review and remote final CI are separate. No push/PR edit/merge/publish; Ready preserved.
