# Issue #8 配布準備（部分対応）

- 作業場所: 新規worktree task/issue8-prep、branch codex/issue-8-package-metadata。
- 開始SHA: 9d72e0e5798883d81789582d8879f139865d37b5、既存変更なし。
- 目的: Issue #8の明確な不具合であるproject URLsを実際のoriginに合わせ、wheel資産の同梱を検証する。
- 範囲: メタデータURL2件、隔離したローカルwheel build/install/init/lint検証。配布名とバージョンは保持。
- 保留: PyPI公開、タグ、Trusted Publishing、publish workflow。利用者は公開操作を除外し、Python/Node配布方針は未統合npmブランチに記録されているため、公開方式の決定を先取りしない。
- 台帳開始確認: main評価中5/10、試行0/3、採用0、期限未定。既存venv read-only利用、ビルドdepsは一時build isolationへ。
- 初期検証状態: 全検査が未実行だった。現在の成功結果と未実行のCIは下表に記録。
- review: 仕様軸investigate、標準軸docs_ciで独立review済み。コード指摘0、初期検証状態/次の一手の古い記述を更新。
- 次の一手: 最終コミットをpushし部分対応Draft PRを作成、最新SHAのCIを確認。

## 対象版と検証
検証対象は開始SHA9d72e0e5798883d81789582d8879f139865d37b5＋pyproject.tomlのURL2件変更と今回journal宣言のみ。元repo/venvは変更なし。ビルドのegg-info/build生成物はignore対象としてこのworktree内にのみ存在する。

| 識別子 | 結果 | コマンド・範囲 | 証拠 |
| --- | --- | --- | --- |
| wheel-build | 成功 | 既存venv python -m pip wheel --no-deps --wheel-dir ../evidence8 .（build isolation） | tool session82802 exit0、wheel SHA256 f53e710b21b6c5077e1ae776a20dc1d4ef05530123d7952cdda590f0c771be80 |
| wheel-assets | 成功 | ZipFileでsrc配下defaults/scaffold/assets全ファイルを比較、METADATA project URLsを検証 | 16必須資産、missing[]、tool chunkcdcecf |
| isolated-install | 成功 | python -m pip install --target ../evidence8/site wheel | tool session35952 exit0、元venvへinstallしていない |
| wheel-smoke | 成功 | python -S、PYTHONPATH=evidence8/siteでinit --site-name WheelSmoke --layer app=src/**、index --write、lint --strict、render --check | import元evidence8/site/okf_devkit、lint0/0、7pages writes0 warnings0、tool chunkcab7e3 exit0 |
| python-required | 成功 | PYTHONPATH=worktree/src、既存venv python tests/run_all.py | ../evidence8/python-required.txt、169件 fail0/error0、session68270 exit0 |
| CI-final | 未実行 | Draft PR最新SHA | 作成後確認 |

Nodeコード・依存・hookは変更しないためNode追加検証は適用外。wheel-smokeはこのmain-based版の既存shared log生成先がproject/log.mdのままであることも観測し、Issue #6別PRを包含した検証とは言わない。公開配布に進む前は全採用変更を含む最終版で再build/installが必要。

## retroゲート
依頼・URL差分・ローカルbuild/install・既存suiteを照合し、新規トリガーなし。既存venvのbuild/setuptools/wheel未導入は事前に確認してbuild isolationへ設計した通常の環境準備。恒久ルールや台帳行追加なし。公開操作・Trusted Publishing・配布名空き確認と本番pip installは未実行（公開方針確定後に別作業）。

## 最終ローカル状態
- 実装HEAD3f51be9（gitの短縮SHA、開始SHAとの差分）。未コミットは生成docs/log.mdとこの検証記録のみ、ユーザー変更なし。
- affected --base開始SHA: 更新文書なし、pyproject/journalは未カバー。共有の配布仕様は今回は変更しない。
- log --layer shared --range main..HEAD --write: 成功、1件追加、実装hash3f51be9。index --write/lint/index --check: 成功、error0/warn0（tool chunk86954e）。
- 独立仕様review: 部分対応の範囲・資産検証・非公開方針適合。独立標準review: protected宣言・隔離環境・必要suite適合。両軸の記録整合指摘を修正、製品コード指摘0。
