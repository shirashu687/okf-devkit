# Issue #7 new doc lint-clean generation

- 開始SHA: 9d72e0e5798883d81789582d8879f139865d37b5、task/issue7、branch codex/issue7-new-doc-clean、開始clean。
- 目的: Issue本文A案を採用し両実装で--code-globs複数指定、4必須型の未指定拒否、related[]、H1空行維持。
- 対象外: lintのプレースホルダ検査緩和、既存Markdownの自動書換え、公開・merge・削除。
- 互換性: Project Overview/Architecture/Reference/How-Toのみ新引数必須。Decision Record/Glossary等任意型とnew backlogの省略維持。既存スクリプトの移行をREADME/生成AGENTSで案内。CLI helpも更新。
- npm未統合差分: cli.pyのinit変更とnewは非重複、scaffold AGENTSテンプレートの既存npmコマンド選択変更とは局所競合する可能性があるが同ブランチ未変更。mainから新規PRとして提出し統合時に保持する。
- 設計: set_fm_field/setFieldはblock list子行も置換し、欠落するtop-level fieldはfrontmatterへ追加。backlogはrelated/code_globsを書換えない。H1置換の空白はspace/tabに限定し、Pythonはlambda置換でタイトルのbackslashをそのまま保持。
- 影響文書: affected出力のNode導入手順、Node ADR更新。docs AGENTSと配布テンプレートの新規doc生成コマンド、READMEの移行案内更新。
- 保護変更: tests/test_new.py、tests/node/native.test.mjs、tests/node/compatibility.test.mjs。既存安全性テストを維持し、必須引数を既存生成プローブへ追加、CLI/生成物境界の回帰検証を追加。
- 開始retro: main台帳の評価中/試行中上限、期限、採用済みを確認。実行対象の試行/採用済みなし。
- 検証・二軸独立レビュー: 実行中。

## 検証記録

対象: be22026の製品コードと生成説明。以下は既存venv `C:/Users/rinta/Documents/1_projects/okf-devkit/.venv/Scripts/python.exe` を使用し、PYTHONPATHをこのworktree/srcへ設定。元repo/venvは変更しない。

| 検証 | 状態 | 実コマンド | 証拠 |
| --- | --- | --- | --- |
| Python全suite | 成功 | `<existing-venv-python> tests/run_all.py` | task/issue7-python-release.log: 172件、失敗0/error0/skip0 |
| Node依存 | 成功 | `npm ci` | 依存8取得、audit問題0 |
| Node native | 成功 | `npm test` | task/issue7-node-release.log: 12件、失敗0 |
| Python/Node互換 | 成功 | `OKF_TEST_PYTHON=<existing-venv-python> npm run test:compat` | task/issue7-compat-release.log: 7件、失敗0 |
| 影響文書 | 成功 | `<existing-venv-python> -m okf_devkit.cli affected --base 9d72e0e` | Node手順/ADRを列挙、双方本文更新 |
| OKF index | 成功 | `<existing-venv-python> -m okf_devkit.cli index --write` / `index --check` | すべて最新 |
| OKF lint | 成功 | `<existing-venv-python> -m okf_devkit.cli lint` | error0/warn0 |
| task/PR保護検査 | 成功 | `<existing-venv-python> harness/project/check_changes.py --base 9d72e0e` / `--scope pull-request --base 9d72e0e` | 対象3testパス declared、exit0 |
| 最新SHA CI | 未実行 | Draft PR push後のPR head照合 | 未実行を成功扱いしない |

最終レコードとlog追記後、必須suiteとドキュメントチェックを同じworktreeで再確認した。検証数172/12/7、index最新、lint error0/warn0。独立仕様担当は最終log/記録も再確認し指摘0。

## 独立レビュー

- 仕様軸: investigateがbaseから全tracked差分と未追跡worklog/宣言を確認、製品指摘0。必須4型・任意型・related置換・H1空行・YAML/backslash・backlog互換・strict lint生成検証を確認。
- 標準軸: 親が同じbaseから全code/tests/docsを独立確認、製品違反/重大smellなし。最終記録の対象版/実コマンド/4値/証拠追記を完了項目として要求し対応。
- logは実在実装commit be22026参照でcli/scaffoldへ追記。生成日時は実際のUTC更新時刻。

## 摩擦観測とretroゲート

- 確認範囲: 依頼、Issue完了条件、main/npm差分、実装、検証、独立二軸review、次のCI確認手順を照合。
- 判定: トリガーなし。設計A案と計画済みcompletion記録の反映で、要件の修正・予期しない失敗・再探索は観測していない。full retro/台帳新行を作らない。
- 処理済み事象/台帳ID: なし。
- 未確認: 最新SHA CIのみ。次の一手はDraft PRの9jobとheadSHA照合。実在しないglobや不完全な本文のlint cleanは保証しない。
