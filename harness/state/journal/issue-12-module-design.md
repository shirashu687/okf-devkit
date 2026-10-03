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

## PR #27 render-open main integration (2026-10-03)

- 開始HEAD: a1ca954697618ff4297cb1395f457d5be222d006、開始working treeはclean。PR#27 remote head一致/OPEN/CONFLICTING、読取取得時のbaseはa16842f。指定した統合対象は5ce845a4deb454919fdec92d5cdff2105dcbc7df（mainのrender --open #22）。外部writeは行わない。
- 3387010e7f8e7bee46c8736274b563f7727d1ac3でexact mainをmergeした。競合はdocs/cli/log.mdのみ。Issue12調査2c6eeeaとmainのrender-open a731462およびnew-doc be22026のログをすべて保持。mainのCLI/Node/README/テスト/ledgerは変更せず取込み、分割実装や機能削除はしない。
- 履歴task/PR宣言はすべて保存。今回PR scopeはbase5ce845a4deb454919fdec92d5cdff2105dcbc7dfから実diff4ファイル（cli index/log/module-migrationと本journal）であり、保護対象差分なし。空changes宣言は追加せず、actualbase/headでcheckerのno-protected判定を確認した。

| 識別子 | 結果 | 対象版・証拠 |
|---|---|---|
| Python required | 成功 | 3387010のclean tree、既存venv＋PYTHONPATH=worktree/src＋PYTHONUTF8=1、176件/fail0/error0/skip0、session98880 exit0、workspace ../issue27-main-python.txt |
| Node install/native/compat | 成功 | 同じ対象版、npm ci --ignore-scripts exit0、native15/pass15/fail0、compat7/pass7/fail0。OKF_TEST_PYTHON既存venvを明示、session81545 exit0。../issue27-main-node.txt/issue27-main-compat.txt |
| OKF index/lint/render | 成功 | index --write/--check最新、lint error0/warn0、render --check20pages書込0/削除0/warn0 |
| PR declaration | 成功 | exactmain5ce845a4→3387010、4ordinarypaths、result=ok、宣言presenceを独立review成功とは扱わない |
| Conflict/diff checks | 成功 | unmergedなし、diff --checkなし、git grep conflictmarkers一致なし（grep exit1は一致なし） |
| 独立review | 未実行 | rootへ最終localSHAを引継ぎ、今回merge対象とPRscopeを独立確認予定 |
| 最新SHA remote CI | 未実行 | push/PR更新は親担当。今回local成功をCI成功へ置換しない |

今回の変更は既知のmain進行による予定された競合統合。指示取りこぼし・回帰・誤成功報告はなく、ledger新規観測/試行/恒久規約を追加しない。既存記録を保持。次の一手はrootの独立reviewと親担当によるpush/latestCI確認。Issue12分割実装は未完了のまま。
