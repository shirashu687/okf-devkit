# 作業記録 PR #95

## 目的と対象

[PR #95](https://github.com/shirashu687/okf-devkit/pull/95) の `markdown-it` 更新に、保護対象2件のPR変更宣言を追加する。CIの変更検査とテストを通過させる。

- 作業日: 2026-11-28 JST
- 作業場所: `shirashu687/okf-devkit` の一時クローン
- PRブランチ: `dependabot/npm_and_yarn/markdown-it-14.3.3`
- 開始HEAD: `5f83de28ade4ee7b92869419fc43eb8211e251b3`（作業ツリーに変更なし）
- 開始時のPR base: `981d71e88006b6e6323ff2c128f2718106531bd5`
- 更新後のPR比較元: `0531fb7a165148ef93021485d991baaf69f3d8d8`（取り込んだ `main`）

## 判断とレビュー

- 仕様: [上流の変更履歴](https://github.com/markdown-it/markdown-it/blob/14.3.3/CHANGELOG.md#L7-L16) にある修正を取り込む。依存指定は両ファイルで `^14.3.3`、ロック先は `14.3.3`。既存のDependabotコミットを保持した。
- 標準: [変更検査と宣言](../../project/config.md#変更検査と宣言) に従い、現行 `main` からの保護対象差分 `package.json` と `package-lock.json` を [PR変更宣言](PR-0095-markdown-it.changes.json) に記録した。検査スクリプトとCI設定の差分はない。

## 検証

| 検証 | 対象 | 結果 | 証拠・理由 |
| --- | --- | --- | --- |
| PR変更検査 | 開始HEAD | 失敗 | [初回CIログ](https://github.com/shirashu687/okf-devkit/actions/runs/46098159613/job/140834249037) で両ファイルが未宣言、終了コード1 |
| Pythonテスト | 開始HEADのCI | 未実行 | Python 3.11／3.13 × Windows／Ubuntu の全4ジョブで変更検査が先に失敗 |
| Nodeテスト・Node/Python比較・独立smoke | 開始HEADのCI | 成功 | [初回CIジョブ](https://github.com/shirashu687/okf-devkit/actions/runs/46098159613) |
| 変更宣言チェック | PR比較元／作業開始HEADからの差分 | 成功 | `check_changes.py` のpull-request・task両scopeで終了コード0 |
| npm依存のインストール | 更新後のロックファイル | 成功 | `npm ci --ignore-scripts` は通常環境でDNSエラー。ネットワークが使える環境で再実行し、`npm ls markdown-it --depth=0` で14.3.3を確認 |
| Nodeテスト（初回） | Windows / Node 24 | 失敗 | 通常環境でシンボリックリンクの作成が `EPERM` となった |
| Nodeテスト（再実行） | Windows / Node 24 | 成功 | `npm test` 32件成功、終了コード0 |
| Pythonテスト（初回） | Windows / Python 3.14 | 失敗 | 通常環境でGit for Windowsのシェルなどが起動制限を受けた |
| Pythonテスト（再実行） | Windows / Python 3.14 | 成功 | 一時クローンの仮想環境で273件実行、失敗・エラー0、スキップ4、終了コード0 |
| Node/Python互換性（準備段階） | Windows / Node 24 / Python 3.14 | 失敗 | 実行環境でのシンボリックリンク作成、依存とソースの参照、Python CLI導入を順に整備した |
| Node/Python互換性（最終） | Windows / Node 24 / Python 3.14 | 成功 | 一時クローンへ `pip install -e .` 後、`npm run test:compat` で22件成功、終了コード0 |
| リポジトリ文書 | 更新後の統合ツリー | 成功 | lintのエラー・警告0、索引最新、HTML 36ページの検証成功 |
| 更新後のCI（push前の記録） | 本記録を含むPR HEAD | 未実行 | 更新コミット反映後の結果は [PRのChecks](https://github.com/shirashu687/okf-devkit/pull/95/checks) で確認する |

## 振り返り

開始時の差分とCIを照合し、保護対象2件のPR宣言欠落を既存の [IMP-0004](../../ledger.md#imp-0004-pr-95-の追加観測2026-11-28) に記録した。試行と採用済み項目は0件で、期限対応は発生していない。依存更新PRを含め、最終差分の保護対象と宣言を照合する。改善候補の試行や採用は今回行わない。
