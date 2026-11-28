# 作業記録 — Issue #83

| 項目 | 値 |
| --- | --- |
| 状態 | 進行中（仕様投稿・実装） |
| 作業場所 | `C:/@git_repogitories/a314/okf-devkit` |
| ブランチ | `codex/issue-83-sync-diagnostics` |
| 開始日時 / 最終更新日時 | 2026-11-28 13:24 / 17:29 JST |
| 設計開始SHA / 実装開始SHA | `21829cc40e7ed3300ed9ca282b391125424a49bf` / `303f94ad2840f93c39787777823fea4fbfade0dd` |
| 作業者 | Codex |
| 参照 | [Issue #83](https://github.com/shirashu687/okf-devkit/issues/83)、[Issue #61](https://github.com/shirashu687/okf-devkit/issues/61)、[PR #99](https://github.com/shirashu687/okf-devkit/pull/99)、[Issue #79](https://github.com/shirashu687/okf-devkit/issues/79) |

## 目的・範囲

Issue #83 の[期待する動作](https://github.com/shirashu687/okf-devkit/issues/83)と[トリアージ](https://github.com/shirashu687/okf-devkit/issues/83#issuecomment-7215190098)の差を詰め、合意した用語と必要な設計判断を記録する。実装、GitHubへの投稿、#61の設定構文や#79のベースライン契約の確定は別作業。

開始時の `git status --short --branch` はクリーン。今回の作業ツリーの変更はこの記録の追加。

## PR #99 に基づく設計合意

再開時の作業ツリーは開始SHAと未追跡の本記録のみ。PR #99 は未マージ。設計の参照版は PR の head `fd7d0c396493224c6756546b9497570317ba5336`、base は `2454b6aaa56162d2618d57931b6d892c59cf5891`。

PR #99 のコードソースは `okf.yml` の `code_sources` で登録し、文書からは `app:src/**` のように名前で参照する。接頭辞なしのパターンは文書リポジトリで照合する。OKF frontmatter の `sources` は出典に使う。用語と判断は PR に含まれる [CONTEXT.md](https://github.com/shirashu687/okf-devkit/blob/fd7d0c396493224c6756546b9497570317ba5336/CONTEXT.md) と [Decision Record 0003](https://github.com/shirashu687/okf-devkit/blob/fd7d0c396493224c6756546b9497570317ba5336/docs/project/decisions/0003-external-code-sources.md) に記録されている。

| 参照と状態 | `lint` の根拠照合 | `stale` のコード側の指摘 |
| --- | --- | --- |
| 名前付き外部ソースが配置済みで一致する | 一致についての警告なし | ソースのコード更新時刻を `info external-unverified` で通知 |
| 外部ソースが未配置または未登録 | 原因別の L10 警告をソース名ごとに1件 | 同じ未検証通知 |
| 外部ソースが配置済みで一致ゼロ | 該当 glob の L10 警告 | 同じ未検証通知 |
| 接頭辞なしの glob が一致ゼロ | 該当 glob の L10 警告 | 同じ一致ゼロを `warn orphan` で報告 |

通常の `lint` は照合の警告を出して検査を続ける。警告は `lint --strict` の終了コード1の対象。OKF 0.3 で L10 を検査する単独コマンドは `lint --project`。外部ソースの未配置と更新時刻の未検証は、[Issue #61 の実装仕様](https://github.com/shirashu687/okf-devkit/issues/61#issuecomment-7234121815)で決まっている。暫定フラグは、名前付きの参照で外部コードソースを特定できるため、この対応に含めない。

**利用者の合意**は、#83 で接頭辞なしの glob の `sync` 重複を解消すること。PR #99 の `external-unverified` は、L10 の根拠照合とは別にコード更新時刻が未検証であることを伝える。#79 の通知やベースライン、#61 の外部履歴による鮮度判定と `log` は別の課題。

### 実装時の受け入れ条件

- 同じ文書・同じ接頭辞なし glob の一致ゼロが `sync` で L10 と orphan に出る場合、行番号付き L10 を表示する。文書パスと glob、一致ゼロという診断の原因を使って対応を判断する。対応する L10 がない orphan は表示する。
- 別々の文書や glob の警告、L10 の形式エラー・必須欄の欠落、鮮度・信頼の診断を表示する。集約した orphan があるために stale 欄が空になる場合は、該当する指摘が lint 欄にあると伝える。
- Python と Node.js の両方で OKF 0.2 と 0.3 を確認する。単独の `lint --strict` と `stale --format json` の診断と終了値、および `sync --gate` の終了条件を既存契約に照らして確認する。

### 再検証

| 識別子 | 結果 | 対象と証拠 |
| --- | --- | --- |
| pr99-fixture-first | 失敗 | 一時フィクスチャの OKF 0.2 索引に 0.3 用のメタデータを入れたため L7 が発生。製品の差分は変更せず、フィクスチャを修正 |
| pr99-fixture-retry | 成功 | PR #99 の固定版を一時展開し、lockfile と一致する Node.js 依存と既存の Python 仮想環境で実CLIを検証。両実装×OKF 0.2/0.3 の4通りで、外部の一致・不一致・未配置・未登録・不正パターン、外部鮮度の通知、接頭辞なし glob の `sync` の2件重複を確認。OKF 0.3 の単独 lint には `--project` が必要 |
| project-required-resume | 実行不能 | この作業ツリーに指定の `.venv/Scripts/python.exe` がない |
| project-venv-resume | 成功 | この作業ツリーで主作業ツリーの既存 `.venv` を使い、前回同様に許可された制限外で `tests/run_all.py` を実行。261件、失敗0、エラー0、スキップ4、exit 0 |
| changes-resume | 成功 | 開始SHAからの変更検査は管理文書1件、exit 0 |

今回の差分は管理文書の更新。仕様軸では #61 の仕様と ADR、PR の Python・Node.js 実装、CLI の再現、利用者の回答を照合した。標準軸では検証対象の版と再試行前後の結果、バンドル外の worklog 配置を照合した。台帳の再開時確認では試行期限・採用済み見直し日の対象なし。一時フィクスチャの修正後に再現を完了し、方針や成果物の手戻りは発生しなかった。full retrospective と台帳変更は不要。PR のCIは今回の検証範囲外。

## 前回の検討（2026-11-28 13:31 JST）

- [GitHub main の参照版](https://github.com/shirashu687/okf-devkit/commit/2454b6aaa56162d2618d57931b6d892c59cf5891)では、`lint` の L10 と `stale` の orphan が同じ glob の一致ゼロをそれぞれ報告する。`sync` は両方の診断を表示する。OKF 0.3 のプロジェクト規約は `lint --project` と `sync` で検査される。根拠は [Python lint](https://github.com/shirashu687/okf-devkit/blob/2454b6aaa56162d2618d57931b6d892c59cf5891/src/okf_devkit/commands/lint.py#L214-L225)、[Python stale](https://github.com/shirashu687/okf-devkit/blob/2454b6aaa56162d2618d57931b6d892c59cf5891/src/okf_devkit/commands/stale.py#L41-L48)、[Python sync](https://github.com/shirashu687/okf-devkit/blob/2454b6aaa56162d2618d57931b6d892c59cf5891/src/okf_devkit/commands/sync.py#L170-L187)、[Node.js sync](https://github.com/shirashu687/okf-devkit/blob/2454b6aaa56162d2618d57931b6d892c59cf5891/src/node/cli.mjs#L397-L410)。
- `lint --strict` は警告で失敗し、`stale` は指摘があっても終了コード 0。単独実行の診断を移すと既存利用に影響する。OKF 文書の `sources` は出典メタデータ。#61 で提案された `okf.yml` の `sources` は外部リポジトリのローカル配置を表す設定。
- 一致ゼロには走査除外も含まれる。診断は「走査条件で一致するファイルがない」までを表す。
- 利用者から、対応中の #61 と並行できる部分を進めたいと回答があった。

| 判断 | 推奨案 | 状態 |
| --- | --- | --- |
| 重複報告と作業順 | `sync` の表示でだけ集約する。単独コマンドの警告と終了条件を維持する | #61 と並行する方針を確認。集約の範囲は提案 |
| 暫定フラグ | 文書ごとの `code_globs_external` は追加せず、#61 の外部ソース宣言で扱う | 回答待ち |
| 宣言済みソースの未配置 | info で「未検査」と報告し、未定義ソース（error）および有効なソースで一致ゼロ（warn）と区別する | 回答待ち |

### 先行作業の受け入れ条件案

- `sync` で同じ文書の同じ glob に対する一致ゼロが L10 と orphan の両方にあれば、行番号がある L10 を1件表示する。比較には診断文の文字列に依存しない情報を使う。
- 別の文書・別の glob の一致ゼロと、L10 の形式エラーや必須項目の欠落、`stale` の期限切れ・コード更新・未検証は引き続き表示する。集約で stale 欄が空になった場合は、lint 欄で指摘済みであることを伝える。
- Python と Node.js の両方で OKF 0.2 と 0.3 を確認する。単独実行の `lint --strict`、`stale --format json`、`sync --gate` の既存契約を維持する。#61 のソース名が使える段階では、同じ glob でも異なるソースの診断を区別する。

### 検証

| 識別子 | 適用 | 結果 | 対象と証拠 |
| --- | --- | --- | --- |
| project-required | はい | 実行不能 | この作業ツリーに指定の `.venv/Scripts/python.exe` がない |
| project-venv-retry | はい | 失敗 | 主作業ツリーの既存 `.venv` をこの作業ツリーから実行。261件、失敗11、エラー0、スキップ4、exit 1。Git Bash の `NtCreateDirectoryObject` と PowerShell の `AuthorizationManager` に起動制限 |
| project-venv-retry-unsandboxed | はい | 成功 | 同じ `C:/Dev/Projects/okf-devkit/.venv/Scripts/python.exe tests/run_all.py` をこの作業ツリーから制限外で再実行。261件、失敗0、エラー0、スキップ4、exit 0 |
| repro-python | はい | 成功 | この作業ツリーの実CLIで一時リポジトリを検証。単独 `lint` は L10 1件・exit 0、`--strict` は1件・exit 1、`stale --format json` は orphan 1件・exit 0、`sync` は重複2件・exit 0 |
| repro-node | はい | 成功 | この作業ツリーの Node.js CLI と既存依存を一時ディレクトリで実行。Python 版と同じ件数と終了コードを確認 |
| pinned-main | はい | 成功 | GitHub mainの固定版で Python/Node.js の重複経路と 0.3 の project lint を静的に確認 |
| changes | はい | 成功 | 既存のプロジェクト `.venv` で `harness/project/check_changes.py --base 21829cc40e7ed3300ed9ca282b391125424a49bf`。通常の変更1件、exit 0 |
| OKF文書・Node.js変更後の検証 | いいえ | — | 管理文書の追加のみ |
| CI test / smoke | いいえ | — | ローカルでの設計検討 |

### review

- 仕様軸では Issue 本文とトリアージの差、関連 Issue への依存、既存の診断と終了条件を照合した。#61 と並行できる集約の受け入れ条件を記録し、実装範囲は判断待ち。
- 標準軸では開始SHAからの未追跡ファイルを含め、作業記録の配置、対象版、再試行前後の検証結果をプロジェクト設定・制約と照合した。記録はOKFバンドル外。

### 摩擦観測とretroゲート

開始時点の台帳は評価中10件、試行0件、採用済み0件。試行期限と採用済み見直し日の対象なし。

依頼・差分・検証・review と再開前提を照合。作業ツリー内の仮想環境の欠如とシェル起動制限は、同じプロジェクトの既存環境と許可された再試行で検証結果を得た。規則や製品の変更を要する作業上の摩擦は確認されず、full retrospective は不要。処理済み事象・台帳更新なし。GitHub main での実CLI検証は行っていない。

## 実装時の再開点

PR #99 のマージ状態を確認し、反映済みの main または PR #99 の head を比較点にして、両実装の `sync` で接頭辞なしの glob の L10 と orphan が1件に集約される回帰を固定する。

## 仕様投稿と実装

利用者の依頼に従い、合意済み仕様を Issue #83 のコメントに投稿し、状態ラベルを `ready-for-agent` に更新する。#83 を単独の実装チケットとして扱う。PR #99 はマージ済みで、実装の比較点は GitHub main の `303f94ad2840f93c39787777823fea4fbfade0dd`。再開時は detached HEAD `21829cc40e7ed3300ed9ca282b391125424a49bf`、未追跡の本記録のみ。

仕様を投稿し、状態ラベルが `enhancement` / `ready-for-agent` になったことを確認した。 [合意仕様](https://github.com/shirashu687/okf-devkit/issues/83#issuecomment-7236542287)

Python と Node.js の既存 CLI 互換テストから集約、診断の保持、終了条件を確認する。作業ブランチを同リポジトリへ push し、`main` 宛てに `Closes #83` の PR を作成する。

実装コミット `3e3dcbbe36323aa1836d226685bf0010f8b516c4` を統合ブランチへ fast-forward した。同じ文書・同じ接頭辞なし glob の一致ゼロについて、CLI の公開診断とは別に照合に必要な値を持たせ、`sync` で表示済みの L10 に対応する orphan を集約する。コマンド仕様に表示の契約を追記した。

| 検証 | 結果 | 証拠 |
| --- | --- | --- |
| CLI 互換の回帰テスト（実装前） | 失敗 | Python・Node.js と OKF 0.2・0.3 の4構成で、同じ glob に L10 と orphan が出た。終了コード1 |
| CLI 互換の回帰テスト（実装後） | 成功 | 4構成で集約、個別の診断、単独のテキスト・JSON、gate の終了コードを確認。終了コード0 |
| 既存 Python gate | 成功 | `test_gate` 15件、終了コード0 |
| Node.js 依存の準備 | 成功 | `npm ci`、終了コード0 |

既存の統合テスト、文書検査、二軸 review の最終結果は確認中。
