# PR #2: CIの変更宣言検査を修正

## 目的・完了条件・対象外

PR #2のCI失敗を修正し、既存4環境のtestと独立smokeを成功させる。タスク単位の宣言・過去worklog・台帳・固定配布コア・上流コピーを保持し、PR全体の保護/上流差分を漏れなく宣言する。後続タスクへの着手・詳細化、GitHub権限変更、PRのマージは対象外。

## 作業状態

- 区分: 通常。開始: 2026-09-07T12:00:49.421626+00:00
- 場所: `C:/Users/rinta/Documents/1_projects/okf-devkit`
- ブランチ: `codex/harness-integration`
- 開始SHA: `d06b428e8d110d70dd9399ac4fd499f22076590d`
- 固定PR base: `85d4b0ef3a349198f03cbcfe71817e6451b6aff2`
- 開始時の既存変更・未追跡: なし（`git status --short`）。
- 対象版: 上記開始SHAと今回の未コミット・未追跡差分。最終版は本記録を含むcommitとPR本文で固定する。

## 診断と判断

- 実CI [run 34118513444](https://github.com/shirashu687/okf-devkit/actions/runs/34118513444) は4環境とも `Check protected and upstream changes (pull requests)` で失敗し、`Run tests` はskipped。独立smokeは成功。
- 同じbase/headのローカル `check_changes.py --base 85d4b0ef3a349198f03cbcfe71817e6451b6aff2 --head d06b428e8d110d70dd9399ac4fd499f22076590d` はexit 1、165診断（base不一致6、重複7、未宣言152）。再現証拠は `%TEMP%/pr2-ci-before.txt`。
- 最小再現は、同じ保護パスを変更した2タスクの異なるbaseを持つ宣言を、一つのPR差分として検査する一時Gitリポジトリ。既存checkerを実際に呼ぶ回帰テストへ追加し、混同時の失敗とscope分離後の成功を確認した。
- CIログと固定SHAでの再現が一致しているため、環境差の多仮説・二分探索・追加ログ計装は省略する。原因は比較文脈の混同と、PR全体の宣言不足。
- タスク宣言は従来のversion 1（scope省略時task）を保持。PR宣言もversion 1とし `scope: pull-request` を明示、CIが `--scope pull-request` を選択する。baseの完全一致、同じ比較差分内の宣言、実差分の全保護/上流パス、理由、worklog、重複・余分なパスの拒否を維持する。
- 別scopeは現在の変更を許可しない。JSON/version/scope/必須項目/理由/越境など構造上の不備は別scopeでも拒否し、比較対象のパス一覧を狭めない。
- scope選択と宣言の有無は人の承認や意味上の安全を証明しない。checkerとCIを同じ差分で更新できる既存の限界は維持する。

## 検証

| 識別子 | 結果 | 対象版・証拠・限界 |
| --- | --- | --- |
| original-ci | 失敗 | 上記固定headの4job。テスト本体未実行 |
| original-local | 失敗 | 上記固定base/head、exit 1、165診断 |
| regression-red | 失敗 | 修正前checkerへ専用16テスト（既存11+追加5）を実行し、subtestを含む14失敗、20.598秒。実際の複数タスク比較のbase不一致/重複と、新scope未対応を検出。`%TEMP%/pr2-ci-regression-red.txt` |
| regression-green | 成功 | 同じ専用16テスト、exit 0、23.219秒。`%TEMP%/pr2-ci-regression-green.txt`。scope分離・別scopeによる許可漏れ・不正宣言・古い宣言・基本schemaを検証 |
| required-tests | 成功 | 既存venv Python 3.14.3、`tests/run_all.py`、exit 0、168件・失敗0・エラー0・skip0、50.831秒。`%TEMP%/pr2-ci-all-tests.txt`。開始SHAに本修正を加えた作業ツリー |
| task-changes | 成功 | `check_changes.py --base d06b428e8d110d70dd9399ac4fd499f22076590d`、exit 0。今回の保護対象4件を同名changes.jsonで宣言。`%TEMP%/pr2-ci-task-green.txt` |
| pr-changes | 成功 | `check_changes.py --scope pull-request --base 85d4b0ef3a349198f03cbcfe71817e6451b6aff2`、exit 0。PR全対象164件（保護13/上流151）を `PR-0002-integration.changes.json` で宣言。`%TEMP%/pr2-ci-pr-green.txt` |
| preservation | 成功 | 過去journal 28本が内容一致、ledger既存3件の本文・回数を保持しIMP-0004だけ追加。core 6本のSHA-256再一致、install/上流両コピー/lock/通知/profile/製品src/docs/入口/okf.ymlは開始SHAから差分なし。`%TEMP%/pr2-ci-preservation.json` |
| affected / OKF | 成功 | `affected --base d06b428e8d110d70dd9399ac4fd499f22076590d` は対象文書0件、変更箇所は未カバー。ハーネスはバンドル外なのでconfigへ反映。OKF lintはexit 0、error 0/warn 0、index --checkは全索引最新。docs本文は変更なし。code_globsの新設や後続Backlogには着手しない |
| CI test / smoke | 未実行 | push後の新headをGitHubで確認 |

## review

- 仕様軸: 指摘0件。固定開始SHAからの作業ツリー・新規ファイルをreview。reviewerがcheckerとは独立にPR全差分を分類し、164対象と宣言164行の過不足・重複なしを確認。別scopeによる許可加算がなく、過去証拠・全対象・base一致を保持していることを確認。
- 標準軸: 指摘0件。scope省略互換、未知scope拒否、別scopeの基本検査、未宣言拒否、CIのbase/head・終了状態・matrix/test/smoke保持を確認。
- 両軸は今回のCI修正と宣言照合のreview。統合PR全体の意味review完了とは区別し、実CI結果もローカル結果から推定しない。

## 摩擦観測とretroゲート

開始時にledgerの評価中3/10、試行0/3、採用済み0を確認。期限超過・見直し・巻戻し競合なし。タスク単位検査だけではPR統合が成立せずCIが停止した実観測についてfull retrospectiveを実施。既存3件とは症状・適用範囲が異なるため [IMP-0004](../../ledger.md#imp-0004) に観測として記録した。同じ事象の再実行は回数へ加算しない。評価中4/10、試行0/3、採用済み0。採用済みの改善や別プロジェクトへの効果へ読み替えない。対象coreや上流へ変更を広げていない。

## 残作業・次の一手

修正、red/green・全suite・両比較点の変更検査・保持検証と二軸reviewを完了。最終差分をcommitしてPR #2へpushし、GitHubの新headで4環境のtestと独立smokeを確認する。

今回の変更はchecker/CI/config/回帰テストと、その宣言・worklog・実観測の追記。検査コードの自動宣言機能・通信・書込み機能は追加していない。作成補助と詳細出力は `%TEMP%/pr2-ci-*` に置き、リポジトリへ実行ログ全文や一時スクリプトを保存していない。
