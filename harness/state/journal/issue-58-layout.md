# 作業記録: Issue #58 フォルダ構成

## メタデータ
- 課題: https://github.com/shirashu687/okf-devkit/issues/58 （親 #15）
- 状態: 進行中
- 作業場所: /workspace/okf-devkit / ブランチ: codex/issue-58-repository-layout
- 開始日: 2026-10-29 / 作業者: Codex
- 開始SHA / 最新HEAD: 2d9e5f8c6497f3655f4aa5cfd9f038c7ec0bae1f
- 開始時の既存変更: なし（git status --short）

## 目的・範囲
フォルダの役割と見かけの重複を調査し、Issue #58の方針・完了条件に従ってNode本体と開発スクリプト・テストを整理する。
機能削除、ランタイム廃止、共有資産の複製、公開・mergeは対象外。

## 判断と根拠
- src/okf_devkitはPython importのための標準配置。pyproject.tomlとADR 0001を照合し維持する。
- Node本体はsrc/nodeへ移動し、node/cli.mjsとnpm binは既存hook・直接起動・main importのため維持する。
- 共有資産はPython package-dataとNode dataDirが同じ実体を指す。現配置を維持する。
- scriptsは配布・CI専用、release guardテストはtests/nodeへ移す。
- Python package discoveryをokf_devkitに限定し、新設src/nodeのnamespace混入を防ぐ。
- gh issueの規約経路はsandbox内のsocket制限、ネットワーク許可ありではGraphQL Forbiddenだった。利用可能なGitHub connectorでIssue作成・更新を実施した。

## 摩擦観測とretroゲート
開始時: ledgerは評価10/10・試行0/3・採用0。期限は観測のみ未定で、期限切れ試行・巻戻し競合なし。
完了時: 未判定。ローカルghの制限にはconnectorで対応した。

## 今回の変更
実装移動、互換入口、配布対象・テストimport・文書参照の追随。最終diffで確認する。

## 検証
対象: 開始SHA + 今回の作業ツリー、Ubuntu / Python 3.12.14 / Node 24.19.0。

| 検証 | 結果 | 根拠・限界 |
| --- | --- | --- |
| npm ci初回 | 実行不能 | 既定cacheが書込範囲外。workspaceの.npm-cacheを指定して再実行 |
| npm ci再実行 | 成功 | --ignore-scripts --cache /workspace/okf-devkit/.npm-cache、8 packages |
| Python全件 | 成功 | .venv/bin/python tests/run_all.py、267件・失敗0・エラー0・skip5、/tmp/okf-layout-python.log |
| Node単独・比較初回 | 失敗 | 制限付き実行でファイル単位の失敗だけが返る。/tmp/okf-layout-node.log、compat.log |
| Node単独再実行 | 成功 | 同じ対象・コマンドでネットワーク権限ありの実行。32件・pass30・Windows skip2、/tmp/okf-layout-node-retry.log |
| Python比較再実行 | 成功 | 15件pass、/tmp/okf-layout-compat-retry.log |
| Release guard | 成功 | 14件pass、/tmp/okf-layout-release-retry.log。外部Release書込みなし |
| npm package | 成功 | 3件pass、ローカル/global・再導入・lock復旧・文書保持、/tmp/okf-layout-package.log |
| Python wheel | 成功 | build + zip内容照合 + /tmpへの隔離導入。Node混入なし、共有資産あり、init/index/lint/render --check成功 |
| OKF | 成功 | index --write / lint(error0/warn0) / index --check、affected確認 |
| 変更宣言 | 成功 | check_changes.py --base 開始SHA、result=ok、/tmp/okf-layout-changes.log |
| CI matrix / 独立CI smoke | 未実行 | ローカル結果から推定しない |

Node初回の詳細診断は得られず、環境以外に原因がないという一般保証はしない。同じコードの権限あり実行で全件を確認した。

## review
- 仕様軸: 開始SHAと全作業ツリー（未追跡含む）を完了時に照合する。
- 標準軸: AGENTS/config/requirements、docs規約、保護対象宣言、package-dataを完了時に照合する。

## 残作業・次の一手
最新mainのREADME・レビュー記録簡略化・ライセンス変更を取り込み、最終検証とレビューを行う。
