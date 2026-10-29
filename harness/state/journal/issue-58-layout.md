# 作業記録: Issue #58 フォルダ構成

## メタデータ
- 課題: https://github.com/shirashu687/okf-devkit/issues/58 （親 #15）
- 状態: 完了（実装・ローカル検証。Draft PRのレビュー・CIは別途）
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

## 最新mainの統合
- origin/main ec493d190c213067f87c314adf766432dd45f133を取込み（merge e833913）。#52の短いREADME、#57の宣言形式、#55のライセンスを保持した。
- READMEの競合は最新main本文を保持して構成案内だけ追加。想定された同一ファイル編集の統合で、機能・利用手順を旧版へ戻していない。
- taskの開始SHAは変更せず、新しい共通宣言形式でpull_request_baseのみ最新mainへ設定した。
- 層別logに実装コミット2e2fe55を記録。最終作業ツリーで全件検証・PR差分検査を行う。

## review（最終差分）
- 仕様軸: 9個のNode本体は開始版とバイト比較し、coreの共有資産相対パス以外は同一。Release guardもimport以外は同一。旧CLI mainと新mainは同一参照、importは無出力、direct helpは一致し、既存hookは同じ入口を呼ぶ。内部node/*.mjsの直接import先のみsrc/nodeへ変更する必要がある。用途説明と初期整理は#58に対応し、機能廃止は先取りしていない。
- 標準軸: 未追跡を含む全差分を確認。npm files/必須資産一覧、Python package discovery、code_globs/layer_map、README/CONTEXT、層別log、索引を追随。必須テストを削除・弱化していない。上流スキルとCIの変更なし。取込んだ#57の検査変更はmainの既存変更であり、本PR差分には含めない。
- affected未カバー: 旧node内部パスは移動元の削除として新配置と照合。README/CONTEXT/okf.ymlとバンドル外harness記録は直接確認。release-nodeの手順・release仕様はtest:releaseのコマンド名を維持するため本文変更不要。

## 最終検査での修正・再試行
- 変更検査はcommit前（削除+未追跡）で成功、commit後のrename認識で失敗した。testsへのrenameは旧scriptsパスも保護対象になるため、旧名の宣言を追加して両scopeを再検査する。初回失敗: /tmp/okf-layout-changes-final.log、/tmp/okf-layout-pr-changes.log。
- log --writeは既存mainの履歴にもcli20/render4/scaffold6件を補完したため、今回と無関係な自動追記を採用せず、元の履歴を保持して本作業3件だけを手動記録した。未実行を成功に置換していない。
- retroゲート: 依頼・差分・全検証・二軸reviewを照合し、旧名宣言の欠落は既決制約の取りこぼしとしてfull retroを実施。既存IMP-0004へ同じ宣言範囲不一致の独立事象を追記した。新規枠、恒久ルール変更、試行、採用判断待ちはない。最終CIとWindows実行は未確認で、PRのCI結果を次に確認する。

## 最終検証と完了要約
対象: e833913 + log・宣言・台帳・本作業記録の最終差分（取込んだmain: ec493d1）。

| 検証 | 結果 | 証拠・限界 |
| --- | --- | --- |
| Python全件（main統合後） | 成功 | 273件・失敗0・エラー0・skip5、/tmp/okf-layout-python-final.log |
| npm test | 成功 | 32件・pass30・Windows skip2、/tmp/okf-layout-node-final.log |
| npm run test:compat | 成功 | 15件pass、/tmp/okf-layout-compat-final.log |
| npm run test:release | 成功 | 14件pass、/tmp/okf-layout-release-final.log |
| npm run test:package | 成功 | 3件pass、/tmp/okf-layout-package-final.log。最終READMEを含む実tgzを隔離導入・復旧 |
| 最終wheel内容 | 成功 | /tmp/okf-layout-wheel-final、Pythonと共有資産を収録しNode混入なし。初回wheelの隔離init/index/lint/render成功も保持 |
| OKF index生成・lint・index確認 | 成功 | 最終logでもerror0/warn0、索引最新 |
| task/PR宣言の再試行 | 成功 | /tmp/okf-layout-changes-final-retry.log、/tmp/okf-layout-pr-changes-retry.log、両方result=ok |
| diff確認・二軸review | 成功 | origin/mainとの差分、移動元/先のバイト比較、git diff --check。仕様・標準軸の詳細は上記 |
| CI matrix・独立CI smoke | 未実行 | PR作成後に確認。Windows/PowerShell・実製品Stopイベントはローカルで未確認 |

構成調査・初期整理・互換性と両配布物のローカル検証を完了。#58はレビューに向けopenを維持し、#15の機能削減は別途継続する。
retroはIMP-0004への追記を実施し、未処理の採用判断はない。残る操作はDraft PRのCI・レビュー確認。
