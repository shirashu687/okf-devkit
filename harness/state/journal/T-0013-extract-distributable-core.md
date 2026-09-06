# 作業記録: T-0013 共通配布版への移行

## 目的・範囲・開始状態

- 目的: 確定配布版への明示移行。完了条件は配布元docs/backlog/T-0013-extract-distributable-core.mdを参照。
- 作業場所: `C:/Users/rinta/Documents/1_projects/okf-devkit`、開始ブランチ `codex/t0003-japanese-entry`、開始SHA `9724d5dc1095a433d654d41444c7fe450b3c7443`、2026-09-06。
- 利用者が移行・保持検証・reviewとT-0013完了を依頼。後続タスク・製品修正・上流更新は対象外。
- 開始時tracked/untracked変更なし、install.jsonなし。配布元 `https://github.com/shirashu687/ai-dev-harness.git`、完全SHA `898d514f0594ff09f6c19292ef4df56f6cc4ac50`。
- 開始時の既存ファイル355本を生バイトで退避: `C:/Users/rinta/AppData/Local/Temp/t0013-pilot-backup.json`。Git開始SHAも復旧根拠。

## 事前に列挙した変更

- コア6本を配布版と正規化一致させる。guideの実採用索引を既存skill-profile末尾へ移設（上流原文・採用状態は変更しない）。
- policyの5制約の強制点・確認方法・限界と適用範囲を既存config末尾へ移設しR1〜R5へ対応。移動に伴う相対リンクを補正。
- config末尾の実効コピーの案内元をguideからprofileへ補正。既存config/profileの他の内容は保持。
- 新設: 本worklog、同名changes.json、必要検証後のharness/install.json。seedで既存設定を置換しない。
- 保持: AGENTS/CLAUDE、CONTEXT、README、全製品コード、テスト、checker、CI、製品設定、上流両コピー、lock、通知、過去journal、ledger。

## 検証

| 識別子 | 結果 | 対象 | 証拠・限界 |
| --- | --- | --- | --- |
| source | 成功 | 配布SHA | 前セッションの独立GitHub cloneを再確認しGit blobから抽出。リモート到達も確認 |
| project-required | 成功 | 開始SHAから今回移行差分 | 対象venv Python 3.14.3、163件/失敗0/error0/skip0、exit0。再実行結果は下記 |
| change-declaration | 成功 | 開始SHAから記録を含む全差分 | 初回失敗後、実差分のない宣言行だけを除去。再試行result=ok/exit0 |
| preservation | 成功 | 既存355本 | 349本生バイト一致、変更6本は許容8本の部分集合。旧policy情報と索引移設も照合 |
| installed-record-links | 成功 | 配布6本・install.json・project | 固定Git blobから生成・再照合。121参照実在、上流両製品25コピー一致 |
| CI / Claude Code | 未実行 | 実機・CI | ローカル検証から推定しない。製品未確認は既存profileを保持 |

## review

仕様軸・標準軸を別担当で固定開始SHAから実施。未コミット・未追跡変更を含み、要修正指摘は両軸0件。checkerが検知する宣言1件は先行共有を受け修正。install.jsonと最終記録の追補確認も依頼する。

## 摩擦観測とretroゲート

開始時ledgerは評価中3・試行0・採用0、期限未定の観測のみ。期限超過試行・判断待ち採用なし。既存台帳は保全対象。権限差は既存IMP-0003に従い、対象venvを許可された環境で使う。恒久ルールは増やさない。

## 復旧・次の一手

途中失敗なら各変更の現物を今回の期待内容と照合し、退避の該当8本だけを戻し、今回新設物だけを除く。並行変更があれば停止する。全体resetは使わない。
保持比較と検証を終え、記録とコアを一つの移行コミットにする。作業状態は完了。配布元T-0013へ移行コミットを渡して完了する。後続タスクへは進まない。

## 初回検証と再試行

既存venv Python 3.14.3で163件・失敗0・エラー0・skip0、41.156秒、終了0。変更宣言検査は初回失敗（exit 1）：配布と同一で差分のないverify-report.mdを宣言していたため。宣言からその行だけを除去し、再検査する。checker・制約・テストを緩めていない。

355本の保持比較は349本が生バイト一致、残り6本は予定8本の部分集合（handoverとverify-reportは元から同一）。config既存本文は案内元の一文以外保持し、profile既存本文は全保持、旧policy5行と範囲・guide採用索引の移設内容を照合済み。導線121参照、両製品25スキルの全ファイル一致を確認した。

宣言修正後checkerはresult=ok、終了0。続くdiff checkがprofile末尾の余分な空行を検出したため、移設末尾だけを整えた。初回diff check失敗を保持し再確認する。

## 最終照合と記録

配布SHAは `898d514f0594ff09f6c19292ef4df56f6cc4ac50`、source.repositoryは `https://github.com/shirashu687/ai-dev-harness.git`。manifest正規化SHA-256は `46d193e267973b8d3b3808f5d0c2fea3f953aff5b234ab3e97b8d2a4d8004a03`。install.jsonのsource/schema/UTC時刻/manifest/6管理ファイルを固定blobから再計算照合し成功。上流・seed・manualは管理一覧外。

保全照合スクリプト: `C:/Users/rinta/AppData/Local/Temp/t0013-verify-pilot.py`、要約JSON: 同Tempの `t0013-pilot-verification.json`。一時ファイルが失われても、開始SHAと移行コミットのGit差分・本記録・install.json・配布固定版から再照合できる。既存のAGENTS/CLAUDE、コード/テスト/checker/CI、製品設定、CONTEXT/README、上流両コピー・lock・通知、過去journal全件、ledger実データは生バイト保持。configは案内元の1文を補正して旧本文を保持し、profile旧本文は全保持。追加された固有説明は旧policy/guideの内容と照合した。

OKF文書は変更なし（harnessは対象configでバンドル外）。対象側のindex生成・OKF lintは適用外、理由は変更対象範囲による。CI matrix/smokeとClaude Code実機は未実行であり、この移行のローカル成功から推定しない。上流の再導入・更新・製品設定変更なし。

retro確認範囲: 依頼、差分、初回検証と再試行、二軸review、保持照合、引継ぎ。宣言候補を実差分へ絞る前に検査したため1回停止し、移設末尾空行もdiff checkで検出・修正。原因は今回の列挙と整形の不足、分類はautomated checks、重要度は低。対処は実差分3件への宣言訂正と末尾整形、確認は既存checker/差分検査の再実行。修正完了、再発・改善効果は未測定。既存検査で検出済みの今回限定修正とし、新たな恒久規定・試行・採用は提案しない。既存台帳3件はそのまま保持し、全ログや演習データを加えていない。

## 完了要約

最終対象（install.json含む）の既存venvテストは163件、失敗0/error0/skip0、40.835秒、exit0。変更宣言とdiff checkは修正後成功。仕様・標準の追補レビューも要修正0件。保持照合・導入記録再計算が成功し、確定配布版への移行を完了した。次の操作は本変更のコミットと配布元T-0013への証拠登録のみ。CI/Claude Codeは未実行、後続タスクには着手しない。
