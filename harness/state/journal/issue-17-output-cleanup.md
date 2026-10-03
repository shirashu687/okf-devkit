# 作業記録: Issue #17 旧生成物の安全な整理

## メタデータ・開始時の状態

- 状態: 進行中。対象 shirashu687/okf-devkit、独立worktree issue17、ブランチ codex/issue17-site-default。
- 作業者: codex/gpt-6。開始SHA 82adb7b1e65c071d54a67c2ff4b38050834a03f5、PR比較点main 5ce845a4deb454919fdec92d5cdff2105dcbc7df。
- 開始時の追跡/未追跡変更なし。既存PR #31の_site既定化とmain取込みを保持し、その後の今回の差分だけをtask宣言へ列挙。
- ユーザーは同PRで旧HTML整理の設計・実装・独立review・テスト・push・Draft更新・最新SHA CIを依頼済み。親PR #22はmerge済みのためbaseをmainへ変更する。merge/deploy/publish/Issue closeは行わない。
- npm未統合ブランチ、他worktree、元checkout/venv、個人hookに変更なし。実ユーザーの生成物へ整理を実行しない。

## 目的・範囲・判断

出力先変更時、確認できた未編集の旧生成物だけを明示指定で復旧可能な場所へ退避する。製品判断を追加で要求せず、既存renderコマンドに `--cleanup-from OLD` と既存 `--check` の計画表示を接続する。

- 正本: [安全な整理手順](../../../docs/render/output-cleanup.md)。新出力成功後の退避、manifest/hash照合、旧版は現在の生成予定と完全一致、未知/編集済み保持。
- 旧新ルートの範囲・入れ子・symlink/junction・backup経路・新出力衝突を事前拒否。cleanupでは既存stale削除を抑止し、通常低レベルrendererの従来動作を保持する。
- 新manifestとreceiptは原子的保存。receipt plannedをコピー前に保存し、コピー/移動完了を分ける。失敗時は上書きせず復元前後hash確認、復旧必要な場所を記録する。
- 新出力巻戻しや並行改変に対する完全なtransactionを約束しない。再実行の対象ゼロならbackupを作らない。hook併用拒否。
- package.jsonは既存npm test/test:compatへ新規テストを追加するだけ。依存/lock/CI/既存必須検査の緩和なし。

## 検証

4値: 成功 / 失敗 / 未実行 / 実行不能。成功は対象版と実際の終了状態を照合する。

| 検証 | 結果 | 対象・証拠・限界 |
| --- | --- | --- |
| main取込み後の既存検証 | 成功 | 固定SHA82adb7b: Python177 / Node16 / compat8、lint error0/warn0、index/PRscope/diff check。issue17-baseverify-{python,node,compat}.log |
| 初期cleanup互換 | 成功 | 追加3ケース含むcompat11件。cleanup-compat-first.log |
| Python focused | 成功 | 最終15件、skip1（Windows symlink作成権限）。Linux symlink/Windows reparseの実装は残しCIで確認 |
| Node focused | 成功 | 最終7件、partial copy/receipt失敗・hash復元・junction・no-opを含む |
| 全Python・Node・互換 | 成功 | Python192件(失敗0/error0/skip1)、npm ci監査0、Node23件、compat再試行11件成功。cleanup-final-{python,node}.log / cleanup-final-compat-rerun.log |
| affected/index/lint/declarations | 成功 | affectedの3本文更新。index --write 1件、lint error0/warn0、index --check最新、task82adb7b/PRmain5ce双方declared、diff --check成功。未カバーREADME/ignore/scaffoldは直接確認 |
| 最新SHA CI | 未実行 | final push後にhead SHAと全jobを照合。ローカル成功から推定しない |

初回final互換は失敗（6/11失敗）。親のPYTHONPATH指定漏れで元checkoutのPythonが読まれ、新オプション/manifest等の不一致を検出。既存venvを変えずPYTHONPATH=本worktree/srcを明示し再試行11/11成功。cleanup-final-compat.logとrerun.logを保持。製品テストを緩和していない。

初期fixture調整やレビュー前の検証は最終版の証拠へ置き換えず、上記と担当のfocused結果を区別する。障害注入時の期待失敗は復旧挙動を検証するテストであり、実ユーザーデータの操作ではない。

## 独立review

- 比較点: task82adb7b、PRmain5ce845a。working/untracked全体を対象にreview_conflicts担当が仕様軸と標準軸を別評価。
- 初回仕様指摘: Node復元前後hash、ゼロ件backup、ADS/制御パス、Python backup経路事前検査。各回帰追加と修正済み。
- 追加指摘: Node receipt非atomic保存、partialcopy残片の識別不足。両者planned保存とNode atomic保存・永続receipt障害/partialcopy fixtureで修正済み。
- 最終実装review: 成功。仕様軸・標準軸のruntime/docs/test確認でblockingなし。最終commitと宣言は次にSHA限定で照合。

## 摩擦観測とretroゲート

- 開始時ledger評価7/10、試行0/3、採用0。試行期限/採用見直しなし。既存IDとnpm未統合の予約番号を照合。
- 確認範囲: 依頼、既決安全要件、実装、独立reviewと修正、障害注入。最終CIは未確認。
- トリガー: 安全要件を満たさない復元hash/receipt保存が独立reviewで見つかり成果物修正を要したためfull retro実施。
- 処理済み事象: IMP-0014。原因仮説・候補・確認方法はledgerへ参照。今回の安全欠陥修正は既存依頼範囲で優先、恒久ルールや改善試行の採用なし。
- 未確認範囲と次の一手: 最終suite・最終SHA CIを照合する。判断待ちなし。

## 残作業・次の一手

最終検証と二軸再review、実commit参照の層別log、PR base main変更、fast-forward push、PR更新、最新SHA CI確認。ブロッカーなし。実行済み外部操作は最終記録に追記する。

## 実装版と層別log

実装commit 59a0bb515b5bb3ccfd12631c9b672c67fddf3109。cli/render/scaffold logへUpdateと実commit参照を記録。最終検証後、PR #31のbase変更と通常pushを行い最新SHA CIを確認する。PRは現在ready状態であるため、その状態を勝手に変更せず保持する。
