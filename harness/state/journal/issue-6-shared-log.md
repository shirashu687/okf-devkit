# Issue #6 shared log 生成先

- 状態: 進行中 / Draft PR準備
- 作業場所: 新規clone `task/okf-devkit`、ブランチ `codex/issue-6-shared-log`
- 開始SHA: 9d72e0e5798883d81789582d8879f139865d37b5、開始時変更なし。
- 目的: Issue #6。Python/Node initのshared logを既存設定 `log.paths.shared: log.md` に揃える。
- 対象外: 既存利用者のlog移動、npm未統合ブランチの変更、merge/publish。
- 判断: main基点。未統合npmブランチのinit案内とは同じ関数を触るが独立した1行変更。npm側テストの `project/log.md` は統合時に `log.md` へ合わせる必要がある。
- 検証環境: 既存 `.venv` を読み取り専用利用し `PYTHONPATH` はこのcloneのsrc。Node24。
- 検証: 必須Python / npm ci・test・compat / affected / index・lint・check / change checkを実行予定。
- review: 開始SHAから作業ツリーと未追跡ファイルを含め、仕様軸・標準軸の独立review予定。
- 台帳: 評価中5/10、試行0/3、採用0。期限未定の観測のみ、恒久採用なし。
- 摩擦: 通常sandboxがプロセス作成前に失敗。同じ限定操作の許可された昇格実行が成功。元repo・venvは変更しない。
- 次の一手: 回帰と必須検証、独立review後Draft PR作成。

## 検証履歴
- Python初回: 失敗、170件 / error2。追加テストが既存cmd_logのrange引数を渡していなかった。range=Noneへ修正。
- Node初回: 失敗、12件 / fail1。追加テストのsnapshot helperがdocs固定でcustom bundleのknowledgeを扱えなかった。bundle内の再帰log列挙へ修正。
- 上記はテスト実装の誤りで、成果物修正と再実行を記録する。

## 現在の検証
- Python再実行: 成功、170件 / fail0 / error0。範囲: 引数修正済み作業ツリー。
- npm ci: 成功、lock更新なし。npm test再実行: 成功、12件。test:compat: 成功、7件。
- affected: node/scaffold.mjsからnode-runtime/ADRを検出、更新済み。cli.pyは既存未カバー（Issue #4が別PRで対応）。
- index --write / lint / index --check: 成功、error0/warn0。task/PR変更検査: 成功。
- docs/scaffold/log.mdはlog --layer scaffold --writeで生成後、Issue #6参照が自動でpull/6になった箇所を実際のissues/6へ修正した。
- ruleset読取: 2026-10-03 active main protect ID22445153、deletion/non_fast_forward/pull_request、bypass空。設定変更なし。

## 摩擦観測とfull retro
- 確認範囲: 依頼、差分、初回テスト失敗と再試行を照合。レビューとCIは進行中。
- トリガーあり: 追加テストのAPI/ヘルパー前提不一致により最初のPython/Node suiteが失敗。要約根拠は上の検証履歴。
- 原因: 既存cmd_logのrange契約とsnapshotのdocs固定を新しいテストへ正しく反映しなかった。
- 候補: テスト追加前に呼出引数とbundle_root対応範囲を既存ヘルパーと照合する。分類 automated checks、重要度低（製品回帰ではなく検証の手戻り）。確認はdefault/custom bundle双方を実行する。
- 対処: 今回テストを修正し、既存suiteで確認。恒久ルール・試行・採用はしない。観測 IMP-0008へ参照。
- 元sandboxのプロセス作成不能は限定的な昇格再試行で解消。原因未確定、既存IMP-0003に類似するがこの作業の実測はvenv前のsandbox provisioning失敗なので発生回数を推測加算しない。

## 独立review
- 仕様軸: review6_spec が開始SHA〜4c951ec＋未コミットscaffold logを確認。製品実装適合、logのpull/6誤リンク1件をissues/6へ修正済み。
- 標準軸: review6_standardsが全差分（retro/ledger追加含む）を確認。製品コードの規約違反0。検証対象版/コマンド/証跡不足と固定更新時刻の2件を修正する。
- 修正確認: rootがissues/6リンクと現在UTCによるgenerated.at、下記検証表を現物照合。製品挙動はreview後変更なし。

## 対象版と証拠
初回と再試行は開始SHA9d72e0eの作業ツリー（cli.py/node/scaffoldと両テスト変更）を検証。製品変更とテスト修正は4c951ecに保存。最終検証は4c951ec＋未コミットnode-runtime/ADR時刻更新、scaffold log、ledger、worklogの状態。CIは未実行、Draft PR作成後に最終SHAで確認する。

| 識別子 | 結果 | コマンド | 対象版・証拠 |
| --- | --- | --- | --- |
| python-required | 成功 | 既存.venv/Scripts/python.exe tests/run_all.py（PYTHONPATH=clone/src） | 4c951ecに収録した修正済み作業ツリー、170/失敗0/エラー0、tool session81200 exit0 |
| node-native | 成功 | npm test | 同版、12/pass12/fail0、session1851 exit0 |
| node-compat | 成功 | OKF_TEST_PYTHON=既存venv、PYTHONPATH=clone/src npm run test:compat | 同版、7/pass7/fail0、session62179 exit0 |
| dependency | 成功 | npm ci | clone内、8 packages、exit0、lock変更なし |
| docs | 成功 | python -m okf_devkit.cli index --write / lint / index --check | 4c951ec収録の文書、lint0/0、tool chunk822a20 exit0 |
| declarations | 成功 | python harness/project/check_changes.py --base 9d72e0e5798883d81789582d8879f139865d37b5、--scope pull-request | 両scope宣言漏れ0、tool chunk822a20 exit0 |
| CI-final | 未実行 | GitHub Actions PR/push最終SHA | Draft PR作成後に確認、ローカル結果から推定しない |

証跡はこの作業のtool終了状態と以下最終ログで照合。公開記録には認証情報・ログ全文を含めない。
