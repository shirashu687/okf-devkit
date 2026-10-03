# Issue #12 モジュール分割事前調査

- 状態: 設計成果完成（分割実装未着手）、分割実装未着手。
- 独立worktree issue12-design / codex/issue12-module-design。
- 開始SHA: 9d72e0e5798883d81789582d8879f139865d37b5、開始時変更なし。
- 目的: Issue12の可変root・YAML monkeypatch・キャッシュ・再exportを保つ段階案を作り、並行コマンドPRとnpm未統合差分を壊さない。
- 技術判断: 純粋helpers→YAML→Doc/Bundle→Git→commandsの順。rootを明示引数で渡し移行中cliの可変状態adapterを保持。大規模分割は先行PR統合後。
- 証拠: cli.py2922行、ASTroot Name27参照、tests49属性。helpersとtest_yamlの直接代入を現物確認。npm差分は読取のみ。
- 対象外: runtime実装、200行条件達成、配布変更、merge/publish。
- 検証: ローカル成功（下記）、独立二軸review成功、CIはDraftPR後確認。
- retro開始: ledger評価5/試行0/採用0、期限付き試行なし。通常の調査と並行分担。最終差分・検証・review照合後判定。
- 次: 調査文書の独立仕様/標準reviewと必須検証を済ませ、部分成果としてDraftPRを作る。Issue12をcloseしない。

## 検証対象と結果

| 検査 | 結果 | 対象・証拠 |
|---|---|---|
| Python必須全件 | 成功 | 開始SHA＋module-migration/index/journal差分（2c6eeea91c9fe5e2d9fbdb231e49eefed5c9d40dへ記録）、169件/失敗0/error0/skip0、session18886 exit0 |
| log/lint/index/render | 成功 | 2c6eeea＋cli/logのhash付き調査記録。log追記不要、lint0/0、index最新、20ページ書込0/warn0 |
| affected | 成功 | 固定開始SHA、コード変更なし。影響0、journal未カバー表示 |
| 保護検査task / PR | 成功 | 開始SHA→worktree / 2c6eeea、保護変更なし、両scope exit0 |
| 仕様軸独立review | 成功 | 親が事前調査範囲を確認し指摘0。分割実装完了として扱わない |
| 標準軸独立review | 成功 | investigate担当、開始SHA→57d18333bdbb50fda8db7463c4c7d5f7aa5a1bd5全4ファイル、clean tree。規約違反0、smells0 |
| 最終SHA CI | 未実行 | DraftPR作成後確認 |

Nodeコード・依存・hook変更なし、追加Nodeローカル検証は適用外。既存CIのNode比較は最終SHAで確認する。文書・ログのみの変更、失敗・回帰・指示取りこぼしなし、retroトリガーなし。新規ledger行は作らない。

最新内容版57d18333bdbb50fda8db7463c4c7d5f7aa5a1bd5を独立review済み。この追記はreview証拠のみ。最終SHAはpush後のCI対象としてPRに記録する。Issue12の200行以下・実分割は未達、先行PR統合後の実装で扱う。

## PR #27 main integration (2026-10-03)

- Merged origin/main 98373cc without conflict or history rewrite. Historical declarations retained; PR diff contains no protected files, so no new declaration is needed.
- Local validation: Python170/170 successful; docs index --write/--check successful, lint error0/warn0, git diff --check successful. PR-scope change check at main/head successful. Node code/assets/hooks were not changed in this design-only PR; independent review and final remote CI remain separate pending observations.
- Retro: retained main ledger observations, no new observation/trial/adoption. No implementation, merge or publication performed.

## PR #27 subsequent main integration (2026-10-03)

- Remote PR was OPEN and matched the previous local reviewed SHA before changes. Merged main a16842f02e71a26849f5c094a32653c23af22640 without history rewrite. Preserved both log entries; node-runtime generated timestamp, where conflicted, uses the later main value. Ledger observations are unchanged and counts match the retained rows. Historical task declarations remain intact.
- Local validation on the integrated tree: Python173/173, Node13/13, compatibility7/7 successful; docs index --write/--check successful, lint error0/warn0. npm ci completed in the design worktree before Node tests. PR-scope change check and conflict/diff checks run after commit; independent review and final remote CI remain separate pending observations.
- Retro: no new trial or adopted rule. No merge/publish/Issue close; Claude actual session remains excluded.
