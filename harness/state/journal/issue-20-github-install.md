# 作業記録: Issue #20 統合した固定版をGitHubから導入し、再現できる検証結果と履歴を揃える（第1・第2段階）

このファイルは1作業1枚の状態記録であり、仕様・チケット・会話全文の複製ではない。配置は [config.md](../../project/config.md) の「作業記録と引継ぎ」に従う。

## メタデータ

| 項目 | 値 |
| --- | --- |
| 課題ID / 作業名 | `issue-20` / `issue-20-github-install`（GitHub Issue #20。第1段階: 変更履歴生成と統合版検証、第2段階: push済み統合版のGitHub導入確認） |
| 状態 | `完了`（第1・第2段階。Issue更新・クローズは別工程） |
| 作業場所 | `C:/Users/rinta/orca/workspaces/okf-devkit/issue-20` |
| ブランチ | `shirashu687/npm-issue-20` |
| 開始日時 / 最終更新日時 | `2026-09-27T10:30:00Z` / `2026-09-27T11:00:00Z` |
| 開始SHA | `9d72e0e5798883d81789582d8879f139865d37b5`（依頼で固定された比較点。作業基盤は統合済みHEAD `4beaba6d2ae70c6ef935a556c888343849a7f5a2`） |
| 最新HEAD | 本worklogを含むローカルコミット（`shirashu687/npm-issue-20` 先端） |
| 作業者 / 製品 / モデル | Orca dispatched worker / Devin / SWE-2 Max |
| 証拠の保存先 | 第1段階は本worklogとコミット履歴のみ。第2段階smoke: `%LOCALAPPDATA%/Temp/okf i20 1790506313/`（gh-proj・fresh・fakebin・npmcache。認証情報・ログ全文は保存しない） |

## 目的・範囲

### 目的

Issue #20 の第1段階として、統合済みHEAD `4beaba6` を対象に、影響文書と統合版実装の整合を確認・修正し、実在コミットを出典とする変更履歴を該当層の `log.md` へ生成して必須検証を通し、ローカルコミットする。

### 対象

- `docs/cli/log.md`、`docs/scaffold/log.md` — `log --write` による実在コミットの追記
- `docs/cli/node-runtime.md` — 影響文書の整合確認と最小修正（`_templates` の呼出し展開の明記、`code_globs` への `scaffold/templates/*` 追加）
- 本worklog

### 対象外

- push、GitHub Issue への投稿・チェック更新、mainへのmerge、npm/PyPI公開
- `src/`、`node/`、`tests/`、`package*.json` などコード・設定の変更（必要になった場合は監督者へ確認する運用）
- Issue #20 受入条件のうち GitHub からの実導入 smoke・生成案内での実行確認（第2段階）
- `src/okf_devkit/scaffold/okf.yml.tmpl` の裸 `okf` 表記（Issue #19 繰越事項。監督者判断で対象外と確定: 実行案内ではなく説明的参照のため現状維持）

### 完了条件

- [Issue #20](https://github.com/shirashu687/okf-devkit/issues/20) のうち、第1段階に割り当てられた範囲（影響文書の整合、該当層の変更履歴を実在コミットから生成、生成後の必須検証、保護対象変更宣言検査、記録）

## 開始時の状態

### 開始時から存在する変更

- 作業ツリーは checkout 直後で clean。比較点 `9d72e0e` から HEAD `4beaba6` までの差分が「開始時から存在する変更」に相当: 統合コミット `2c3050d`（npm導入・起動設定に沿った初期化案内の実装・文書・テスト・issue-14 worklog）と、Issue #18・#19 のレビュー指摘修正を統合する4件のマージコミット。確認方法: `git log --first-parent --oneline 9d72e0e..HEAD`、`git diff --stat`
- worktree直下に `.venv` がないため、既存venv `C:/Users/rinta/Documents/1_projects/okf-devkit/.venv`（Python 3.14.3）へのjunctionを作成。以後のPythonは `.venv/Scripts/python.exe` に `PYTHONPATH=C:/Users/rinta/orca/workspaces/okf-devkit/issue-20/src` を付けて実行。`npm ci` 済み（終了0）

### 今回の変更

- 変更済み: `docs/cli/log.md` — `log --write` で 2026-09-27 グループに2件追記（`3b32025` Update、`2c3050d` Creation）
- 変更済み: `docs/scaffold/log.md` — 同上2件追記
- 変更済み: `docs/cli/node-runtime.md` — init が揃える対象に `_templates` を明記（統合版では `_templates` 生成も `{{OKF_COMMAND}}` 展開を通るため）、`code_globs` に `src/okf_devkit/scaffold/templates/*` を追加、`generated.at` 更新
- 未追跡: `harness/state/journal/issue-20-github-install.md` — 本記録

## 判断と根拠

| 判断 | 根拠 | 影響 |
| --- | --- | --- |
| 影響文書の整合は `affected --base 9d72e0e` の出力と未カバー一覧の目視で確認 | `affected` 出力: `docs/cli/node-runtime.md`・`docs/project/decisions/0001-node-runtime.md` が影響文書。両者の本文は統合版と整合 | docs/ |
| `node-runtime.md` に `_templates` 明記と `scaffold/templates/*` の code_globs 追加 | `affected` の未カバー一覧に変更済みの `src/okf_devkit/scaffold/templates/{backlog-item,log}.md` が残ったため。`cli.py` L2768・`node/scaffold.mjs` L167 で `_templates` が `expand` を通ることを現物確認 | docs/cli/node-runtime.md |
| log追記の範囲は `--range 9d72e0e..HEAD` のfirst-parent 5件のうち2件（`2c3050d`・`3b32025`）のみが cli/scaffold 層へ振り分け | `okf.yml` の `log.layers: [cli, render, scaffold]` と layer_map（docs→skip、残り→shared）。docs/harnessのみのマージ `36761c5`・`d8f2421`・`4beaba6` は追記対象なし。`--dry-run` で内容を事前確認 | docs/cli/log.md、docs/scaffold/log.md |
| `issue-20-*.changes.json` は作らない | 今回の自分の変更はすべて ordinary。差分内の保護対象 `tests/` 3件は `issue-14-distribution.changes.json`（同一base・task scope）が宣言済みで、`check_changes.py` は宣言間重複を拒否する | 宣言ファイルなし |
| ローカルコミットのみで push・Issue投稿しない | 依頼の編集範囲と R3（許可された外部操作のみ） | なし |

## 摩擦観測とretroゲート

| 項目 | 記録 |
| --- | --- |
| 確認範囲 | 依頼（本タスク記述）・Issue #20/#14 本文・`9d72e0e..4beaba6` の全差分統計・先行2worklog（issue-18・issue-19）の検証・review記録・影響文書の現物・実行した全検証・`check_changes.py` 出力を照合 |
| 該当条件と根拠または非該当理由 | トリガーなし。`affected` の未カバー検出と `_templates` 明記不足は影響文書の整合確認という本タスクの目的作業の範囲内であり、要件の取りこぼし・検証漏れ・やり直し反復は発生していない |
| 短い観測メモ | 開始直後、worktreeのHEADは比較点 `9d72e0e`（ブランチ `shirashu687/issue-20`）にあり、統合済み `4beaba6` から `shirashu687/npm-issue-20` を作成して基盤を揃えた。また `mklink /J .venv` の引数がGit Bash経由で `\C:\...` に化けてjunctionが `C:\C:\...` を指し、PowerShell `New-Item -ItemType Junction` で作り直した（1回の追加操作で解消）。どちらも環境差の軽微な摩擦で要件修正・検証失敗を伴わないためトリガーとしない |
| 処理済み事象・台帳ID | なし（IMP-0009 は作成しない） |
| 未確認範囲と次の一手 | CI・他OS・別PCでの成功は未確認。GitHubからの統合版実導入smokeは第2段階。`okf.yml.tmpl` の裸 `okf` 表記は監督者との確認で繰越確定（下記） |
| full retrospective | 不要 |
| 人の判断待ち | なし（`okf.yml.tmpl` 件は監督者回答により解決） |

開始時台帳確認: 評価中8/10、試行0/3、採用済み0。期限超過の試行・見直し対象なし。IMP-0006の対処案（smokeは独立ルート）は第2段階で適用する事項であり、本段階でsmokeは未実施。

## 検証

対象版: 統合済みHEAD `4beaba6d2ae70c6ef935a556c888343849a7f5a2` + 本タスクの文書変更（docs 3ファイル）を含む作業ツリー。Python は `.venv` junction → `C:/Users/rinta/Documents/1_projects/okf-devkit/.venv`（Python 3.14.3）、`PYTHONPATH` 付きで本worktreeの `src` を参照。Node v24.21.0 / npm 11.19.0。

| 識別子 | 適用 | 結果 | 対象版・範囲 | コマンド / 確認方法 | 期待条件 | 証拠 | 理由・限界 / 再試行 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| affected | はい | 成功 | base `9d72e0e` → 統合HEAD | `okf_devkit.cli affected --base 9d72e0e…`（PYTHONPATH付き） | 終了0・影響文書の列挙 | 終了0。`docs/cli/node-runtime.md`・ADR0001が列挙され本文は統合版と整合。未カバーに `scaffold/templates/*` が残ったため code_globs へ追加して整合 | README・harness文書は層外として目視確認済み |
| docs-index-write | はい | 成功 | 統合HEAD + 本タスク文書変更 | `index --write` | 終了0・索引最新 | `index.md はすべて最新です`、終了0 | なし |
| docs-lint | はい | 成功 | 同上 | `lint` | error 0 / warn 0・終了0 | `lint: error 0 件 / warn 0 件`、終了0 | なし |
| docs-index-check | はい | 成功 | 同上 | `index --check` | 終了0 | `index.md はすべて最新です`、終了0 | なし |
| log-generation | はい | 成功 | `--range 9d72e0e..HEAD` | `log --dry-run` で内容確認後 `log --write` | 実在コミットを出典に該当層へ追記 | `docs/cli/log.md`・`docs/scaffold/log.md` へ各2件（`3b32025` Update、`2c3050d` Creation）。未コミット変更への架空出典なし | 追記はコミット済み履歴のみが対象。shared層は `log.layers` 外のため自動追記なし |
| project-required | はい | 成功 | 統合HEAD + 本タスク文書変更 | `PYTHONPATH=<worktree>/src .venv/Scripts/python.exe tests/run_all.py` | 終了0・失敗0・エラー0 | `実行 171 件 / 失敗 0 / エラー 0 / スキップ 0`、`OK`、終了0 | なし |
| node-install | はい | 成功 | このcheckout | `npm ci` | 終了0 | added 8 packages・終了0 | なし |
| node-native | はい | 成功 | 統合HEAD（node/・tests/node 差分を含む範囲） | `npm test` | 全件pass・終了0 | 13件 pass / 0 fail、終了0 | 統合範囲に node 側差分があるため適用 |
| node-compat | はい | 成功 | 同上 | `OKF_TEST_PYTHON=<worktree>/.venv/Scripts/python.exe` `PYTHONPATH=<worktree>/src` で `npm run test:compat` | 全件pass・終了0 | 8件 pass / 0 fail、終了0 | 編集中のPythonソースを参照していることを PYTHONPATH で担保 |
| change-declarations | はい | 成功 | base `9d72e0e` → 作業ツリー | `.venv/Scripts/python.exe harness/project/check_changes.py --base 9d72e0e…` | 終了0 | `result=ok`、終了0。保護対象 `tests/` 3件は `issue-14-distribution.changes.json` が `declared`。本タスクの新規保護対象変更なし | 宣言の存在は承認や意味上の安全性の証明ではない |
| github-install-smoke | いいえ | — | 第2段階 | — | — | — | 第1段階の範囲外。統合版をGitHubから実導入する検証は未実施であり、公開SHA指定の導入可否は第2段階で確認 |
| CI | いいえ | — | ローカル作業のみ | — | — | — | push・PRを行わないため起動しない。ローカル成功からCI成功を推定しない |

### 再試行履歴

- なし（全検証が初回成功。失敗・実行不能は発生していない）

### 先行の失敗・実行不能履歴との区別

- Issue #14 worklog の `project-required` 実行不能（指定venv不存在、終了1）は当該環境の限界として保持。本worktreeでは既存venvへのjunctionにより必須検証が終了0で成功しており、別の対象版・環境の記録として区別する
- Issue #14 の初回smoke失敗（親探索による生成先の相違、IMP-0006）は対処済みの観測であり、本段階でsmokeは未実施のため新規の失敗・再試行はない
- Issue #18 の `最終コミット再検証`（IMP-0007 の発端）は先行作業の記録であり、本段階の検証は統合HEAD `4beaba6` + 文書変更の作業ツリーが対象。コミット後の最終版に対する必須検証との対応は本worklogの対象版記述で識別可能とした

## review

Issue #20 の受入条件「仕様軸・標準軸のレビュー結果を記録する」に対し、本段階では先行2件（Issue #18・#19）で実施済みの二軸レビューの指摘と、その統合版での解消・繰越を集約して記録する。本タスク自身の差分は docs のみで、lint・index・affected の機械検査（全終了0）と目視照合で確認した。

### 仕様軸

- 比較点: `9d72e0e5798883d81789582d8879f139865d37b5`
- 対象: 統合HEAD `4beaba6` までのコミット済み差分 + 本タスクの文書変更
- 結果: 指摘の集約は次のとおり。
  - 指摘1（#18仕様軸）: `scripts.okf` が別用途で占有される場合の統合先がない → **解消**。`node-runtime.md` に別名スクリプト案内を追加済み（マージ `36761c5` で統合）
  - 指摘2（#18仕様軸）: READMEに `npm install` が package.json 不在でも依存記録を作る注記がない → **解消**。README に注記追加済み（同上）
  - 指摘3（#19仕様軸）: 生成 `docs/_templates/` に裸の `okf` 呼出しが残る → **解消**。`{{OKF_COMMAND}}` トークン化と `_templates` 生成経路の `expand` 適用（`de7c7aa`、マージ `3b32025` で統合）、観測は IMP-0008 へ登録済み
- 繰越（所有範囲外として先行worklogから報告済み・本段階でも未解決）:
  - `init` は空でない任意の `scripts.okf` 値に `npm run okf --` 案内を出す（中身がokf-devkit呼出しか未検証。src/node の変更要否は別判断）
  - `src/okf_devkit/scaffold/okf.yml.tmpl` のコメントに裸 `okf` 表記が残り、生成 `okf.yml` にそのまま出る（`{name}` 形式の別展開経路）。監督者への確認で**繰越確定**: 当該コメントは生成元・出力先・設定が影響するサブコマンドへの説明的言及であり、実行手順・コピペ用コマンド例ではないため対象外と判断。コード変更は行わない

### 標準軸

- 比較点: `9d72e0e5798883d81789582d8879f139865d37b5`
- 標準: AGENTS / config / requirements / docs規約（CONVENTIONS・docs/AGENTS）/ smell baseline
- 結果: 先行の標準軸reviewは修正必須0件（#18・#19とも）。#18の指摘「検証表の対象版と最終コミットの対応が識別不能」は最終コミット再検証の記録で解消済み（マージ `4beaba6` で統合、IMP-0007 登録済み）。本タスクの文書変更は lint error 0 / warn 0・index --check 終了0・log追記の出典が実在コミットのみであることを確認。繰越: `render_hook.sh`/`ps1` の `pip install okf-devkit` 案内は比較点前からの既存文で src/ 編集の判断は別工程、として先行worklogが報告済み

## 残作業・妨げ・再開前提

### 残作業

- 第2段階（別工程）: 許可された公開工程を経た統合版SHAをGitHubから独立した空の利用先へ導入し、生成案内で index・lint まで実行するsmoke、lockfile再導入、PATH上の別okf非依存・欠落時失敗の確認、Issue #20 チェックの更新
- `okf.yml.tmpl` 裸 `okf` 表記は「実行案内ではなく説明的参照」として監督者判断で対象外・繰越確定（コード変更なし）。将来実行案内化が必要になった場合のみ再検討

### 妨げ

- なし

### 再開前提

- worktree `C:/Users/rinta/orca/workspaces/okf-devkit/issue-20`、ブランチ `shirashu687/npm-issue-20`、`.venv` junction と `node_modules`（npm ci 済み）が残っていること

## 次の一手

本worklogを含む変更を `shirashu687/npm-issue-20` へローカルコミットし、コミットSHAと変更範囲をcoordinatorへ報告する。

## 完了 / 中断要約

統合済みHEAD `4beaba6` を対象に Issue #20 第1段階を完了した。`affected --base 9d72e0e` の影響文書を照合し、`node-runtime.md` への `_templates` 明記と `code_globs` 補完で整合させた。`log --range 9d72e0e..HEAD --write` で cli・scaffold 両層の `log.md` へ実在コミット（`2c3050d`・`3b32025`）を出典とする追記を行い、未コミット変更への架空出典はない。必須検証は全て成功: index --write/lint（error 0・warn 0）/index --check、Python 171件・Node 13件・互換8件、`check_changes.py` 終了0（新規宣言不要）。先行の失敗・実行不能履歴は保持したまま本段階の対象版と区別して記録した。繰越: `okf.yml.tmpl` の裸 `okf` 表記（監督者判断で対象外確定・説明的参照のため現状維持）、GitHub実導入smoke（第2段階）、CI・他OS未検証。retroトリガーなしで IMP-0009 は作らない。

## 追記: 2026-09-27 第2段階 — push済み統合版のGitHub導入確認

### 対象版と前提

- 導入元SHA: `662023f57b4ed961ece76621ab208aaf6d190822`（`origin/shirashu687/npm` としてpush済みの統合版。本worktreeの第1段階コミット `6660722` を祖先に含むことを `git merge-base --is-ancestor` で確認）
- 環境: Windows、Node v24.21.0、npm 11.19.0。グローバルの `okf` はPATH上に非存在（`which okf` で確認）
- smoke配置: `%LOCALAPPDATA%/Temp/okf i20 1790506313/` 配下。パスに空白を含み、親ディレクトリに package.json・okf.yml がない独立ルート（IMP-0006 の対処案どおり）

### 実施した操作と結果（4値）

| 識別子 | 適用 | 結果 | 対象・確認 | 終了状態・証拠 | 理由・限界 / 再試行 |
| --- | --- | --- | --- | --- | --- |
| gh-install | はい | 成功 | 空の `gh-proj` で `npm install --save-dev "git+https://github.com/shirashu687/okf-devkit.git#662023f…"` | 終了0、added 9 packages。`package-lock.json` の resolved が対象SHA `662023f57b4ed961ece76621ab208aaf6d190822` と一致 | 公開済み統合版の取得のみ検証 |
| scripts-check | はい | 成功 | `npm pkg get scripts.okf` → `{}`（未設定）→ `npm pkg set "scripts.okf=node node_modules/okf-devkit/node/cli.mjs"` | 既存用途の上書きなし | なし |
| init-guidance | はい | 成功 | `npm run okf -- init --layer "app=src/**"` → 生成物確認 | 終了0。「次の手順」3-4 が `npm run okf --`。生成 `docs/` 全体（AGENTS・CONVENTIONS・`_templates`・各 log.md）に裸 `okf` 呼出し0件・未展開 `{{` 0件。AGENTS 20箇所・CONVENTIONS 9箇所が `npm run okf --` 表記 | IMP-0008 の教訓で列挙ファイルに限定せず生成ツリー全体を確認。生成 `okf.yml` のコメント内 `okf` 言及は監督者判断どおり説明的参照として対象外 |
| index-lint | はい | 成功 | 生成案内どおり `npm run okf -- index --write` → `npm run okf -- lint` | 各終了0、index 3件生成、`lint: error 0 件 / warn 0 件` | 空白を含むパスで実行 |
| path-independence | はい | 成功 | `fakebin` に終了93・`FAKE_OKF_USED` を出す偽 `okf`/`okf.cmd` をPATH先頭へ置き、Python系・元clone先のPATH要素を除去して `npm run okf -- lint` | 終了0、`error 0 / warn 0`、`FAKE_OKF_USED` 出力なし | 導入済みローカルCLI（`node node_modules/okf-devkit/…`）を使用。Python・グローバルokf・元cloneに非依存 |
| missing-dependency | はい | 成功 | `node_modules/okf-devkit` を一時rename → `npm run okf -- lint` | 終了1、`MODULE_NOT_FOUND`、偽okfへの切替なし。復元後の再実行は終了0 | 期待した失敗を検証 |
| fresh-lock | はい | 成功 | `package.json`+`package-lock.json` を独立 `fresh/` へコピー、新規 `--cache` で `npm ci` → init → `index --write` → `lint` | 各終了0、`lint error 0 / warn 0` | 親プロジェクト設定に依存しない再導入。同一マシン上の確認であり別PCではない |
| CI・他OS・別PC | いいえ | — | — | — | ローカル Windows のみ。ローカル成功から他環境の成功を推定しない |

### 再試行履歴（第2段階）

- なし（全確認が初回成功。既存の失敗履歴: Issue #14の初回smoke配置ミス・venv実行不能、Issue #18の最終コミット再検証は保持）

### 摩擦観測とretroゲート（第2段階）

- 確認範囲: 依頼手順1-8、対象SHAの祖先関係、全smoke操作と終了状態、生成物の表記確認、第1段階の検証記録を照合。
- 該当条件: トリガーなし。親探索失敗（IMP-0006）の再発なく、要件欠落・検証漏れ・手戻り反復なし。
- 処理済み事象・台帳ID: なし（IMP-0009 以降の台帳更新なし）。
- 未確認範囲と次の一手: CI・他OS・別PCは未検証。Issue #20 の受入条件チェック更新とクローズ判断は利用者の操作として残る。

## 完了 / 中断要約（第2段階を含む最終版）

第1段階で統合HEAD `4beaba6` の変更履歴生成（cli・scaffold両層へ実在コミット `2c3050d`・`3b32025` の追記）と影響文書の整合（`node-runtime.md` へ `_templates` 明記・`code_globs` 補完）を行い、コミット `6660722` として記録した。第2段階で、そのコミットを祖先に含むpush済み統合版 `662023f57b4ed961ece76621ab208aaf6d190822` を、空白を含む独立した空の利用先へGitHubから導入し、`scripts.okf` 設定→init→生成案内どおりの `index --write`・`lint` まで全て成功した。生成物は `npm run okf --` 表記に揃い、`_templates` を含め裸 `okf` 呼出し・未展開トークンは0件。PATH先頭の偽okf・Python非存在でもローカルCLIを使い、`node_modules/okf-devkit` 欠落時は終了1で失敗し復元を確認した。`package.json`+`package-lock.json` のみの独立フォルダで新規キャッシュの `npm ci` から同じ操作が再現した。必須検証（Python 171件・Node 13件・互換8件・文書検査・宣言検査）は第1段階の対象版で全て成功。繰越・限界: `okf.yml.tmpl` の裸 `okf` 表記は監督者判断で対象外（説明的参照）、CI・他OS・別PCは未検証、Issueのチェック更新・クローズは別工程。retroトリガーなし。
