# 作業記録 Issue #61 外部コードソースの設計検討

## メタデータ

| 項目 | 値 |
| --- | --- |
| 課題ID / 作業名 | Issue #61 / 外部コードソースの設計検討 |
| 状態 | PR #99 の CI 修正をローカル検証済み |
| 作業場所 | `C:/@git_repogitories/c837/okf-devkit` |
| ブランチ | `codex/external-code-sources` |
| 開始日時 / 最終更新日時 | 2026-11-28T12:18+09:00 / 2026-11-28T17:17+09:00 |
| 設計検討の開始SHA | `21829cc40e7ed3300ed9ca282b391125424a49bf` |
| 実装の開始SHA / 最新HEAD | `2454b6aaa56162d2618d57931b6d892c59cf5891` |
| 作業者 / 製品 / モデル | Codex / Codex デスクトップ / GPT-6 |
| 証拠の保存先 | [Issue #61 の仕様コメント](https://github.com/shirashu687/okf-devkit/issues/61#issuecomment-7234121815) |

## 目的・範囲

- 設計合意を既存 Issue のコメントとして掲載し、初回の提供範囲を実装する。
- 完了条件は [Issue #61 の仕様コメント](https://github.com/shirashu687/okf-devkit/issues/61#issuecomment-7234121815) の振る舞いをレビューと必須検証で確認し、通常の PR を作成すること。

## 開始時の状態

- 設計検討の開始時点で既存変更はなし。実装開始時は設計検討で追加した未コミットの用語、ADR、索引、この作業記録が存在した。
- 仕様コメントの投稿後、最新の `origin/main` を取得し、設計文書の変更を引き継いで実装ブランチを作成した。比較点には OKF 0.3 対応とコード走査除外が含まれる。

## 判断と根拠

- 第1ラウンドで合意した初回範囲は `lint` の根拠照合と `affected --source <name> --base <ref>`。`stale` の外部更新時刻は未検証と表示し、履歴による判定と `log` は後続とする。
- 共有設定は `code_sources`。`code_globs` の `app:src/**` はソース名 `app` からの相対参照で、接頭辞なしは文書のプロジェクト側の従来の参照とする。
- 第2ラウンドで、配置は `path_env` の環境変数で標準の `path` を上書きする方法に合意した。
- 外部ソースを確認できない `affected` は「差分未確認」を警告して終了コード `0` とする。通常の `lint` は警告で続行し、明示的な `lint --strict` は既存の終了値を維持する。
- 外部ソースを指定した `affected` は文書側の `layer_map` で変更パスを絞らない。外部ソースの変更入力は初回の `--base` の範囲に絞り、`--source` と `--paths` の併用は初回の対象外とする。
- 長期の設計判断を [Decision Record 0003](../../../docs/project/decisions/0003-external-code-sources.md) に記録した。
- 以後の質問は、具体的なファイルやコマンドを例にして選択の結果を示し、推奨案と理由を明記する。
- `sources` は OKF 文書の出典にも使う。定義は [執筆規約](../../../docs/CONVENTIONS.md) を参照。
- ソース別の反映済み SHA 管理は [Issue #62](https://github.com/shirashu687/okf-devkit/issues/62)、未配置と一致なしの混同は [Issue #83](https://github.com/shirashu687/okf-devkit/issues/83) に対応する。
- 第3ラウンドで、外部ソースの `affected` は比較対象と現在の HEAD の共通祖先から HEAD までの変更に、未コミット変更を加えることで合意した。比較対象や共通祖先を特定できない場合は「差分未確認」を返す。
- Python と Node.js の共通仕様と互換性は [Decision Record 0001](../../../docs/project/decisions/0001-node-runtime.md) に従う。
- 実装は仕様コメント投稿と再取得による掲載確認の後に開始した。両実装で既存のファイル走査と Git 差分処理を再利用し、外部ソースの Git 起動は呼出し元リポジトリ固有の環境変数を引き継がない。OKF 0.3 の独自規約は既存どおり `lint --project` から検査する。
- 書き込み先は作業用ブランチと既存 Issue の仕様コメント。通常の PR は `main` に向けて作成し、初回範囲後の履歴連携が残るため Issue は参照する。

## 摩擦観測とretroゲート

- 台帳の評価中は10件、試行中と採用済みは0件。期限超過・見直し対象なし。
- 依頼、Issue本文とコメント、現行実装、配置規約、差分、検証結果を照合。指定 `.venv` 不在と補助テストの失敗を記録した。設計の回答を確認する作業は継続可能。台帳更新なし。
- 必須テストは同一リポジトリの既存 `.venv` への一時リンクを使う再試行で成功。既知の環境制約から回復し、検証漏れ・回帰・設計のやり直しは確認されなかったため、full retrospective は不要と判定した。
- 第3ラウンドでは第2ラウンドの回答、ADR と索引の差分、既存テスト、OKF 検査を照合した。追加のトリガーなし。
- 完了時に最後の回答、ADR と索引の差分、最終検証を照合した。新たな摩擦観測はなく、台帳更新なし。
- 実装では仕様reviewで呼出し元の Git インデックスが外部 Git に渡る問題を検出。継承設定が意図した実行先に作用する既存事象として [IMP-0005](../../ledger.md#imp-0005) を更新した。Git インデックスを指定した回帰テストで失敗を再現して修正し、走査・起動失敗の診断と影響文書も二軸reviewの指摘を受けて修正した。恒久採用や試行の判断待ちはない。

## 検証

| 識別子 | 適用 | 結果 | 対象版・範囲 | コマンド / 確認方法 | 期待条件 | 証拠・理由 |
| --- | --- | --- | --- | --- | --- | --- |
| project-required | はい | 実行不能 | 開始SHA＋この記録 | `.venv/Scripts/python.exe tests/run_all.py` | 終了0、失敗0、エラー0 | この worktree に指定の実行ファイルがない。PowerShell で起動不可、終了1 |
| project-supplemental | はい | 失敗 | 同じ worktree の `tests/` と `src/` | 主作業ツリー `C:/Dev/Projects/okf-devkit` の既存 `.venv/Scripts/python.exe` で `tests/run_all.py` | 終了0、失敗0、エラー0 | 終了1。261件、失敗11、エラー0、スキップ4。一部失敗は Git Bash の起動時にアクセス拒否。残りの失敗原因は未確認 |
| project-required（再試行） | はい | 成功 | 開始SHA＋`CONTEXT.md` とこの作業記録 | `.venv/Scripts/python.exe tests/run_all.py` | 終了0、失敗0、エラー0 | 終了0。261件、失敗0、エラー0、スキップ4。既存 `.venv` に一時リンクし、サンドボックス外で実行後にリンクを削除した |
| OKF（第2ラウンドまで） | いいえ | — | バンドル | index生成、lint、index確認 | — | `docs/` の変更なし |
| project-required（第3ラウンド） | はい | 成功 | 開始SHA＋ADR、索引、`CONTEXT.md`、作業記録 | `.venv/Scripts/python.exe tests/run_all.py` | 終了0、失敗0、エラー0 | 終了0。261件、失敗0、エラー0、スキップ4。既存 `.venv` への一時リンクを再利用する方法で実行し、テスト後に削除 |
| OKF index生成 | はい | 成功 | ADRを含むバンドル | `.venv/Scripts/python.exe -m okf_devkit.cli index --write` | 終了0 | 終了0。`docs/project/decisions/index.md` を更新 |
| OKF lint | はい | 成功 | 生成後のバンドル | `.venv/Scripts/python.exe -m okf_devkit.cli lint` | 終了0、error 0、warn 0 | 終了0、error 0、warn 0 |
| OKF index確認 | はい | 成功 | 生成後の索引 | `.venv/Scripts/python.exe -m okf_devkit.cli index --check` | 終了0 | 終了0、すべて最新 |
| project-required（最終版） | はい | 成功 | 比較範囲の決定を追記した作業ツリー | `.venv/Scripts/python.exe tests/run_all.py` | 終了0、失敗0、エラー0 | 終了0。261件、失敗0、エラー0、スキップ4。既存 `.venv` への一時リンクを使い、実行後に削除 |
| OKF index生成（最終版） | はい | 成功 | 最終版のバンドル | `.venv/Scripts/python.exe -m okf_devkit.cli index --write` | 終了0 | 終了0、すべて最新 |
| OKF lint（最終版） | はい | 成功 | 最終版のバンドル | `.venv/Scripts/python.exe -m okf_devkit.cli lint` | 終了0、error 0、warn 0 | 終了0、error 0、warn 0 |
| OKF index確認（最終版） | はい | 成功 | 最終版の索引 | `.venv/Scripts/python.exe -m okf_devkit.cli index --check` | 終了0 | 終了0、すべて最新 |
| npm依存（実装初回） | はい | 失敗 | 開発環境 | `npm ci` | 終了0 | サンドボックスで npm レジストリの名前解決に失敗 |
| npm依存（再試行） | はい | 成功 | 実装開始SHAのロックファイル | `npm ci` | 終了0 | アクセス承認後に正常終了 |
| CLI追試（レッド） | はい | 失敗 | 機能追加前、Git環境分離前 | 追加した CLI 比較ケースの絞り込み実行 | 仕様の期待出力 | `--source` 未認識、外部 glob の一致なし、および呼出し元インデックスによる差分未確認を各ケースで確認 |
| 互換（実装初回） | はい | 失敗 | 初回review前の作業ツリー | `npm run test:compat` | 終了0 | 24件中3件失敗。既存環境に現行 main の `mdit-py-plugins` がなかったため、宣言済み依存を検証専用ディレクトリへ導入 |
| 互換（依存追加後） | はい | 成功 | 再レビューの最後の走査修正より前 | `npm run test:compat` | 終了0 | 24件成功。最終差分の再実行を下記に記録する |
| Python（実装最終版） | はい | 成功 | 実装開始SHAからの最終差分 | `.venv/Scripts/python.exe tests/run_all.py` | 終了0、失敗・エラー0 | 273件、失敗・エラー0、スキップ4。既存 `.venv` を一時リンクし、検証専用ディレクトリに不足依存を補った |
| Node.js（実装最終版） | はい | 成功 | 実装開始SHAからの最終差分 | `npm test` | 終了0 | 32件成功 |
| 互換（実装最終版） | はい | 成功 | 実装開始SHAからの最終差分 | `npm run test:compat` | 終了0 | 24件成功。比較の Python は既存 `.venv` を指定した |
| OKF（実装最終版） | はい | 成功 | 変更後のバンドル | `index --write`、`lint`、`index --check` | 各終了0、lint error 0 / warn 0 | すべて満たした |
| 影響文書と読み取り検査 | はい | 成功 | 変更後のバンドルと最終差分 | `affected --base`、`log --dry-run --range <開始SHA>..HEAD`、`stale --format json`、`render --check` | 各終了0、影響文書と未カバーの照合 | 各終了0。HTML検査37ページ、警告0。差分範囲にコミットがない時点の log は追記候補0 |
| 変更宣言 | はい | 成功 | 実装開始SHAから最終作業ツリー | `check_changes.py` の task と pull-request scope | 両方終了0 | 保護対象の互換テストファイルの宣言を確認 |

## review

- 仕様軸は実装開始SHAからの差分と未追跡ファイルを、Issue の仕様コメントと照合した。外部 Git の環境分離、ファイル走査の失敗と一致なしの区別、Git の起動失敗を差分未確認とする処理を修正した。再レビューの Node.js 再帰走査指摘は、存在確認より先にソース内のパスを解決する順序に直した。
- 標準軸は CLI の処理構造、執筆規約、配布雛形、変更宣言を照合した。ローカルと外部の動作を記載し、再レビューで指摘された外部鮮度の出力種別を Node.js の機能一覧に追記した。保護対象は互換テストの1ファイルで、宣言を記載した。
- 影響文書のうち現行コマンド・利用導線を更新した。旧版のリリース記録、移行履歴、配布方式、HTML と cleanup は対象コードの共通 glob に一致したが今回の仕様の変更はないため、現行の記述を維持する。未カバーの用語、作業記録、宣言、改善台帳は OKF バンドル外で差分を照合する。

## 残作業・妨げ・再開前提

- 実装・二軸review・ローカル最終検証は完了。公開手順では作業用ブランチを push し、通常の PR を作成する。GitHub Actions の結果は PR 側を参照する。

## 設計検討の完了要約

外部コードソースの参照と配置、照合できない場合の診断、初回に提供する差分の範囲を合意し、Decision Record 0003 と CONTEXT.md に記録した。最終版の既存テスト、索引生成、lint、索引確認が成功した。

## 実装の完了要約

仕様コメントの範囲を Python と Node.js の CLI に実装し、外部ソースの照合、差分による逆引き、比較できない場合の診断を両版の CLI から確認した。最終検証が成功し、通常の PR へ進める状態になった。

## PR #99 の CI 修正

- 修正前の比較点は `fd7d0c396493224c6756546b9497570317ba5336`。PR の比較元は実装開始時の `2454b6a` のまま。修正と検証結果は [既存の PR](https://github.com/shirashu687/okf-devkit/pull/99) へ反映する。
- [CI の初回実行](https://github.com/shirashu687/okf-devkit/actions/runs/46124302945)では、Windows の Node.js 22 と 24 で `affected` と `lint` の外部ソース比較が失敗。テスト用の一時パスは DOS 短縮名を含んでいた。ローカルで短縮名を `TEMP` と `TMP` に設定し、同じ2件の失敗を再現した。Git は正常にルートを返しており、通常の表記へ展開したその値と設定パスの文字列比較が原因だった。
- Node.js はネイティブの実体パスを使って比較し、Python は `samefile` で同じディレクトリか比較する。Windows のデバイスパスを使う回帰テストを追加した。通常のパスと短縮名を使った一時領域の両方で対象の2件が成功し、配下のフォルダを拒否する既存条件も確認した。
- 仕様軸は CLI の成功条件とルート境界、標準軸は保護対象宣言と差分を独立レビューした。追加指摘なし。`affected` が示す CLI と利用者文書は既定の外部ルート照合の説明と一致するため、バンドル本文の改訂は不要。
- retro は既存の Windows パス別名に関する [IMP-0015](../../ledger.md#imp-0015) に再発を記録。対処は製品コードの同一性判定と回帰テスト。試行や恒久ルールの変更を伴う判断事項はない。

| 検証 | 結果 | 証拠 |
| --- | --- | --- |
| 初回 CI の Windows 互換テスト | 失敗 | Node.js 22 と 24 で外部ソースの2件が失敗 |
| 短縮名を使ったローカル再現 | 失敗 → 成功 | `node --test --test-name-pattern 'affected only uses changes\|lint and stale distinguish' tests/node/compatibility.test.mjs`。短縮名の一時領域で修正前に2件失敗、修正後に2件成功 |
| Windows のデバイスパス回帰テスト | 失敗 → 成功 | 追加した `lint --strict` の別表記チェックは修正前の Node.js と Python で拒否され、修正後は両実装で成功 |
| Python 全体 | 成功 | `.venv/Scripts/python.exe tests/run_all.py` 終了0。273件、失敗・エラー0、スキップ4 |
| Node.js 全体・両版の比較 | 成功 | `npm ci`、`npm test` 32件、`npm run test:compat` 24件、いずれも終了0 |
| OKF と宣言の確認 | 成功 | `lint` はエラー・警告0、`index --check`・`affected`・タスクと PR の変更検査は終了0 |

修正コミットを既存の PR に push し、GitHub Actions の再検証結果を PR のチェック欄で確認する。
