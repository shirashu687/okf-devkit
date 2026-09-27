# 作業記録: Issue #19 初期化したAI向け説明と既存プロジェクトの案内を起動設定に揃える

## メタデータ

| 項目 | 値 |
| --- | --- |
| 課題ID / 作業名 | `issue-19` / `issue-19-init-guidance` |
| 状態 | `完了` |
| 作業場所 | `C:/Users/rinta/orca/workspaces/okf-devkit/issue-19` |
| ブランチ | `shirashu687/npm-issue-19` |
| 開始日時 / 最終更新日時 | `2026-09-27T09:20:00Z` / `2026-09-27T10:30:00Z` |
| 開始SHA | `9d72e0e5798883d81789582d8879f139865d37b5`（依頼で固定された比較点） |
| 最新HEAD | `2c3050df98422cbf258b7bd093468e338bc10afc`（引継ぎコミット） |
| 作業者 / 製品 / モデル | Orca dispatched worker / Devin / SWE-2 Max |
| 証拠の保存先 | 一時smoke `%TEMP%/okf-i19-2780322701`（ローカル一時フォルダ。認証情報・ログ全文なし） |

## 目的・範囲

### 目的

Issue #19 の受入条件8項目すべてについて、引継ぎコミット `2c3050d` の既存実装と検証記録を照合し、不足があれば最小限補う。同じ実装を作り直さない。

### 対象

- `src/okf_devkit/cli.py`、`node/scaffold.mjs`、`src/okf_devkit/scaffold/*.tmpl` の初期化時の呼出し案内選択
- `tests/test_init.py`、`tests/node/*.mjs` の設定あり・なし・設定保持の検証
- `docs/cli/node-runtime.md` の移行案内セクション（所有は別ワーカー。不足時は報告に回す）
- 本worklog

### 対象外

- README.md、`docs/cli/node-runtime.md`、`docs/project/decisions/0001-node-runtime.md`、`package.json`、`package-lock.json`、`CONTEXT.md`、`harness/state/journal/issue-14-distribution.*` の編集（別ワーカー所有・凍結）
- push、GitHub Issue への投稿、main への merge、`harness/ledger.md` の更新（retroトリガーなしのため）

### 完了条件

- [Issue #19](https://github.com/shirashu687/okf-devkit/issues/19) の Acceptance criteria 8項目

## 開始時の状態

### 開始時から存在する変更

- 作業ツリー自体は checkout 直後で clean。比較点 `9d72e0e` から HEAD `2c3050d` までの差分が「開始時から存在する変更」に相当し、内容は引継ぎコミット1件: Python/Node 両 init の `scripts.okf` 判定と `OKF_COMMAND` トークン、AGENTS/CONVENTIONS テンプレートの `{{OKF_COMMAND}}` 化と「実行場所と呼出し」節、3テストファイルの追加検証、README/Node手順/ADR/ledger/ issue-14 worklog・宣言。確認方法: `git diff --stat 9d72e0e..2c3050d`

### 今回の変更

- 未追跡: `harness/state/journal/issue-19-init-guidance.md` — 本worklog
- コード・テスト・docs の変更なし（照合の結果、不足は検出されなかった）

## 判断と根拠

| 判断 | 根拠 | 影響 |
| --- | --- | --- |
| 実装の作り直しは行わず、照合と検証の再実行で受入条件を確認した | Issue #19 本文「同じ変更を作り直さない」、issue-14 worklog の検証記録、引継ぎコミットの差分実読 | 変更範囲を最小化 |
| 独自の `issue-19-*.changes.json` は作成しない | 差分内の保護対象は `tests/` 3件のみで、同一差分内の `issue-14-distribution.changes.json`（base一致・task scope）が全件宣言済み。check_changes.py は同一scope宣言間の重複パスを `duplicate path` で拒否するため、同じパスを再宣言すると検査が終了1になる。新規の保護対象変更がない限り有効な宣言を作れない | `harness/project/check_changes.py` L346-L362 で確認。実測でも `result=ok`・終了0 |
| smoke の一時プロジェクトは `%TEMP%` 直下の独立ルートに置いた | IMP-0006（親に package.json/okf.yml があると親探索で生成先が変わる失敗）の教訓 | 検証の再現性 |

## 受入条件の照合

| # | 条件 | 結果 | 証拠 |
| --- | --- | --- | --- |
| 1 | 空でない `scripts.okf` がある場合、生成AGENTS・執筆規約・変更履歴・初期化後案内が npm 経由に揃う | 充足 | `cli.py` L2710-2718 / `scaffold.mjs` L82-89 で `scripts.okf` が空でない文字列なら `OKF_COMMAND="npm run okf --"`。両テンプレートの全呼出し例と log.md コメント、両実装の「次の手順」3-4が同トークンを使用。smoke: `%TEMP%/okf-i19-2780322701/proj` で `npm run okf -- init` 後の生成物は `npm run okf --` 表記のみ（AGENTS 20箇所、CONVENTIONS 9箇所、両log.md各1箇所）、裸の `okf <cmd>`・未展開 `{{` なし（2026-09-27 訂正: この確認は列挙した生成ファイルに限定され、生成 `docs/_templates/*.md` は確認範囲外だった。`_templates/log.md`・`backlog-item.md` に裸の `okf` 呼出しが残っており、末尾の追記で修正・再検証した） |
| 2 | 生成案内でプロジェクトルートからCLIを実行し index・lint が成功。実行場所と新しいclone/worktreeの依存準備が分かる | 充足 | smokeで案内どおり `npm run okf -- index --write`（終了0、index 3件生成）・`npm run okf -- lint`（error 0 / warn 0、終了0）をプロジェクトルートで実行。生成 AGENTS.md「実行場所と呼出し」に「`okf.yml` があるプロジェクトルートで実行」「新しいclone・worktreeで最初に `npm ci`」を明記 |
| 3 | 導入・起動失敗はエラーを報告する案内。別場所のCLIや未導入パッケージへの切替手順を含まない | 充足 | 生成 AGENTS.md「実行場所と呼出し」に「失敗した場合はそのエラーを報告し、別の場所のCLIや未導入パッケージへ切り替えない」。フォールバック記述なし |
| 4 | npm設定なし・読めない・不正JSON・okfスクリプト不在で従来表記を維持。Python利用者へnpm移行を強制しない | 充足 | Python は `(OSError, ValueError)`、Node は `catch {}` で欠落・読取・JSON不正をすべて `okf` 表記へフォールバック。`{}`/`null`/`scripts:null`/`okf:" "`/不正JSON/ファイル非存在を `test_init.py` L81-86・`native.test.mjs` L102-110 が確認し、パッケージ非存在の init は他の既存テスト群が実行。移行強制なし |
| 5 | init は既存npm設定・lockfileを書き換えず、依存を自動インストールせず、既存文書を保持 | 充足 | init は package.json を読み取るだけで書き込まず、インストール処理なし。`test_init.py` L69-86 が package.json バイト一致、`native.test.mjs` L82-99 が package.json と lockfile のバイト一致を確認。既存ファイルは `--force` なしでスキップ（`test_init.py` L126-136） |
| 6 | 既存プロジェクトの移行手順に独自規約を保つ更新方法を記載。一括強制上書きせず、hook更新と区別 | 充足 | `docs/cli/node-runtime.md`「既存プロジェクトの案内を更新する」が独自規約の保持・部分編集・`init --force` 非推奨を記載し、「既存hookの更新」がhook単体のコピー手順として分離（別ワーカー所有ファイルだが不足なし） |
| 7 | 既存テスト群で設定あり・なし双方と設定保持を確認。日時正規化を除き両実装の生成一致 | 充足 | 上記Python/Nodeテスト + `compatibility.test.mjs`「npm-configured projects receive identical invocation instructions」が両実装の生成物一致を日時正規化込みで検証。本worktreeで3系統すべて成功（検証表参照） |
| 8 | 必須既存テスト・Node/互換テスト・文書検査を実施し対象版と限界を記録 | 充足 | 下記検証表。ローカル Windows のみで、CI・他OSは未検証 |

## 摩擦観測とretroゲート

| 項目 | 記録 |
| --- | --- |
| 確認範囲 | 依頼（本タスク記述）・Issue #19/#14 本文・引継ぎコミット全差分・issue-14 worklog の検証記録・本worktreeでの必須検証とsmoke・所有範囲外ファイル（docs/cli/node-runtime.md、README.md）の内容照合 |
| 該当条件と根拠または非該当理由 | retrospective.md §2 のトリガーに該当する事象なし。要件欠落・取りこぼし・検証漏れ・誤報告・手戻り反復・権限/環境の大きな摩擦は観測されなかった。smoke配置は既存観測IMP-0006の対処案どおり独立ルートを選び、初回から成功（同じ症状の新規発生ではないため回数は加算しない） |
| 短い観測メモ | 開始直後、worktreeのHEADが引継ぎコミット `2c3050d` ではなく比較点 `9d72e0e`（ブランチ `shirashu687/issue-19`）にあった。対象コミットは `shirashu687/npm`・`shirashu687/npm-issue-18` から到達可能で、`git checkout -b shirashu687/npm-issue-19 2c3050d` で作業基盤を揃えた。環境差の軽微な摩擦であり要件修正・検証失敗を伴わないためトリガーとしない |
| 処理済み事象・台帳ID | なし |
| 未確認範囲と次の一手 | CI・他OS・別マシンでの検証は未実行（ローカル成功を読み替えない）。他ワーカー所有の統合工程で `log --write` の正式追記と Issue 更新が残る |
| full retrospective | 不要 |
| 人の判断待ち | なし |

## 検証

対象版: HEAD `2c3050df98422cbf258b7bd093468e338bc10afc`（ブランチ `shirashu687/npm-issue-19`）。Python は本worktreeに作成した `.venv` junction → `C:/Users/rinta/Documents/1_projects/okf-devkit/.venv`（Python 3.14.3）、`PYTHONPATH=C:/Users/rinta/orca/workspaces/okf-devkit/issue-19/src` を付与してworktreeのソースを確実に参照。Node v24系 / npm 11系（`npm ci` 終了0）。

| 識別子 | 適用 | 結果 | 対象版・範囲 | コマンド / 確認方法 | 期待条件 | 証拠 | 理由・限界 / 再試行 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| project-required | はい | 成功 | HEAD `2c3050d` | `.venv/Scripts/python.exe tests/run_all.py`（PYTHONPATH付き） | 終了0・失敗0・エラー0 | `実行 171 件 / 失敗 0 / エラー 0 / スキップ 0`、`OK` | なし |
| node-native | はい | 成功 | 同上 | `npm test` | 全テスト pass・終了0 | 13件 pass / 0 fail | なし |
| node-compat | はい | 成功 | 同上 | `OKF_TEST_PYTHON=<worktree>/.venv/Scripts/python.exe` と同じPYTHONPATHで `npm run test:compat` | 全テスト pass・終了0 | 8件 pass / 0 fail | なし |
| docs-index-write | はい | 成功 | 同上 | `python -m okf_devkit.cli index --write` | 終了0・索引が最新 | `index.md はすべて最新です`、終了0 | なし |
| docs-lint | はい | 成功 | 同上 | `python -m okf_devkit.cli lint` | error 0 / warn 0・終了0 | `lint: error 0 件 / warn 0 件`、終了0 | なし |
| docs-index-check | はい | 成功 | 同上 | `python -m okf_devkit.cli index --check` | 終了0 | `index.md はすべて最新です`、終了0 | なし |
| affected | はい | 成功 | base `9d72e0e` → HEAD | `python -m okf_devkit.cli affected --base 9d72e0e...` | 変更対象文書の列挙 | `docs/cli/node-runtime.md`、`docs/project/decisions/0001-node-runtime.md` が影響文書（引継ぎコミットで更新済み）、未カバーは README・ledger・journal で同コミットが更新 | なし |
| change-declarations | はい | 成功 | base `9d72e0e` → 作業ツリー | `python harness/project/check_changes.py --base 9d72e0e...` | 終了0 | `result=ok`、保護対象 `tests/` 3件は `issue-14-distribution.changes.json` で `declared` | 宣言の存在は承認や意味上の安全性の証明ではない |
| smoke-npm-init | はい | 成功 | 同上の `npm pack` 生成物 | `%TEMP%/okf-i19-2780322701`（独立ルート）で `npm install --save-dev <tgz>` → `npm pkg set scripts.okf=...` → `npm run okf -- init --layer "app=src/**"` → 生成案内どおり `index --write`・`lint` | 生成案内が `npm run okf --` に揃い index/lint が終了0 | init「次の手順」3-4が `npm run okf --`、生成物の裸 `okf <cmd>`・`{{` なし、`index --write` 終了0（index 3件）、`lint` error 0 / warn 0 終了0（2026-09-27 訂正: 裸 `okf` の確認対象は AGENTS.md・CONVENTIONS.md・各 log.md に限られ、`docs/_templates/` は含まれなかった。末尾の追記参照） | ローカルtgz経由。未公開変更のGitHub導入可否は対象外（Issue #20） |
| CI | いいえ | — | ローカル検証のみ | push/PRを行わないため未起動 | — | — | ローカル成功からCI成功を推定しない |

### 再試行履歴

- なし（全検証が初回成功。失敗・実行不能は発生していない）

## review

### 仕様軸

- 比較点: `9d72e0e5798883d81789582d8879f139865d37b5`
- 対象: HEAD `2c3050d` までのコミット済み差分 + 未追跡の本worklog
- 結果: 受入条件8項目を上表で一件ずつ実装・テスト・文書の現物と照合し、すべて充足を確認。修正必須の差分なし

### 標準軸

- 比較点: `9d72e0e5798883d81789582d8879f139865d37b5`
- 標準: AGENTS.md、requirements R1-R5、config の検証・宣言・worklog規約、docs/AGENTS.md（本worklogはOKFバンドル外の管理文書であり docs/ に置かない）
- 結果: 保護対象の新規変更なし（既存差分の宣言は引継ぎ側の宣言ファイルで充足・検査終了0）。外部送信・権限拡大・不可逆操作なし。記録に認証情報・個人を特定する情報・ログ全文を含めない。修正必須の指摘なし

## 残作業・妨げ・再開前提

### 残作業

- 他ワーカー/統合工程: 実在コミットを出典とする `log --write` 追記と Issue #19 チェック更新（本タスクでは投稿禁止）

### 妨げ

- なし

### 再開前提

- worktree `C:/Users/rinta/orca/workspaces/okf-devkit/issue-19`、ブランチ `shirashu687/npm-issue-19`、`.venv` junction と `node_modules`（npm ci 済み）が残っていること

## 次の一手

- 本worklogを含む変更を `shirashu687/npm-issue-19` へローカルコミットし、coordinator へ検証結果を報告する。

## 完了 / 中断要約

引継ぎコミット `2c3050d` を基盤に Issue #19 の受入条件8項目を照合し、実装・テスト・文書の不足はなく、追加のコード変更は不要と判断した。必須Pythonテスト171件・Node単独13件・互換8件が成功し、docs索引/lint/affected/変更宣言検査も終了0。独立一時プロジェクトでの `npm run okf --` 導入smokeも成功。独自changes.jsonは重複宣言になるため作成せず、既存宣言が保護対象を覆うことを検査で確認した。CI・他OSは未検証であり、ローカル結果を読み替えない。

## 追記: 2026-09-27 仕様軸レビュー指摘の修正（生成 `_templates` の裸 `okf` 呼出し）

### 指摘と判断

- 仕様軸レビューで、npm起動設定（`package.json` の `scripts.okf` が空でない文字列）のプロジェクトでも、生成 `docs/_templates/` 配下に裸の `okf …` 呼出し表記が残る指摘を受けた。前回の「生成物に裸 `okf` なし」に相当する確認は列挙ファイル（AGENTS.md・CONVENTIONS.md・各 log.md）に限定されており、`docs/_templates/*.md` は確認範囲外だった。検証漏れ・成功報告の範囲不適合として、上記2箇所の証拠欄へ範囲限定の訂正注記を追加した（元の記録は履歴として保持）。
- 原因: Python `cli.py` の `emit(f"{bundle_root}/_templates/{tmpl.name}", _scaffold_text(...))` と Node `node/scaffold.mjs` の `plan.push([..., scaffold(`templates/${file}`)])` がトークン展開を通さず、テンプレート側も `{{OKF_COMMAND}}` を使っていなかった。

### 今回の変更

- `src/okf_devkit/scaffold/templates/log.md`: `okf log`・`okf log --write` → `` `{{OKF_COMMAND}} …` `` に置換。
- `src/okf_devkit/scaffold/templates/backlog-item.md`: `okf affected` → `` `{{OKF_COMMAND}} affected` `` に置換。frontmatter の `generated.by: process:okf-cli` は呼出しではなく識別子のため対象外。
- `src/okf_devkit/cli.py`: `_templates` 生成を `expand(_scaffold_text(...))` に変更。
- `node/scaffold.mjs`: `_templates` 生成を `expand(scaffold(...))` に変更。
- `tests/test_init.py`: npm設定ありで `_templates` 全件に裸 `` `okf ``・未展開 `{{` がなく、`log.md`・`backlog-item.md` が `npm run okf --` を含むこと、および npm設定が使えない各ケースで `_templates` が従来 `` `okf `` 表記を維持することを追加検証。
- `tests/node/native.test.mjs`: 同趣旨の検証をNode単独テストへ追加。
- `tests/node/compatibility.test.mjs`: 変更なし。`snapshot(root)` が `docs/` を再帰収集するため `_templates` は既に両実装の生成比較対象に含まれており、追補は不要と判断した。

### 再検証（対象版: 前回コミット `10ef7792b37623659e76710598c23c8d84a64506` + 作業ツリーの今回変更）

| 識別子 | 適用 | 結果 | コマンド / 確認方法 | 期待条件 | 証拠・限界 |
| --- | --- | --- | --- | --- | --- |
| project-required | はい | 成功 | `PYTHONPATH=<worktree>/src .venv/Scripts/python.exe tests/run_all.py` | 終了0・失敗0 | `実行 171 件 / 失敗 0 / エラー 0 / スキップ 0`、`OK` |
| node-native | はい | 成功 | `npm test` | 全件pass・終了0 | 13件 pass / 0 fail |
| node-compat | はい | 成功 | `OKF_TEST_PYTHON=<worktree>/.venv/Scripts/python.exe PYTHONPATH=<worktree>/src npm run test:compat` | 全件pass・終了0 | 8件 pass / 0 fail |
| change-declarations | はい | 成功 | `.venv/Scripts/python.exe harness/project/check_changes.py --base 9d72e0e5798883d81789582d8879f139865d37b5` | 終了0 | `result=ok`。今回の保護対象の変更は `tests/test_init.py`・`tests/node/native.test.mjs` で、両パスとも既存 `issue-14-distribution.changes.json`（同一scope・同一base）が `declared` |
| smoke-templates-npm | はい | 成功 | `%LOCALAPPDATA%/Temp/okf-i19fix-1672026126` 配下の独立ルート（親に package.json/okf.yml なし）で `scripts.okf` 付き package.json を置き、Python/Node 両実装で init → 生成 `docs/_templates/*.md` を確認 | `npm run okf --` に展開・裸 `okf` 呼出しと未展開 `{{` が残らない | 両実装で `_templates/log.md`（`npm run okf -- log`・`-- log --write`）・`_templates/backlog-item.md`（`npm run okf -- affected`）を確認。裸 `` `okf ``・`{{` なし |
| CI | いいえ | 未実行 | push/PRを行わないため未起動 | — | ローカル成功からCI成功を推定しない |

### 変更宣言の判断

`issue-19-init-guidance.changes.json` は作成しない。今回変更した保護対象は `tests/test_init.py` と `tests/node/native.test.mjs` のみで、両パスは同一差分内の `issue-14-distribution.changes.json` が既に宣言済み。`check_changes.py` は同一scope宣言間のパス重複を `duplicate path` で拒否し、`changes` の空リストも invalid のため、宣言可能な非重複の保護対象パスは存在しない。検査は `result=ok`・終了0。

### 残存の類似指摘（今回の指摘範囲外）

`src/okf_devkit/scaffold/okf.yml.tmpl` のコメントにも裸の `okf` 呼出し表記（`` `okf init` ``・`` `okf new doc` ``・`` `okf log` ``・`` `okf affected` ``）が残り、生成 `okf.yml` にそのまま出る。レビュー指摘の範囲は `docs/_templates/` であり、同ファイルは `{name}` 形式の別展開経路を使うため今回は修正していない。同種の表記ずれであり、対応要否は統合工程で判断する。

### retroゲート（本追記分）

- 確認範囲: 依頼（レビュー指摘と修正手順）、前回の受入照合・検証記録、今回の差分・検証、ledger.md の現状。
- 該当条件: `retrospective.md` §2「検証漏れ、誤った成功報告、review漏れ」に該当 — 前回は生成物の確認範囲を列挙ファイルに限っていたのに範囲を限定せず記録し、`_templates` の裸 `okf` を見逃した。
- 処理: full retrospective の観測として `harness/ledger.md` に IMP-0008 を追記（分類 `automated checks`、重要度 中）。対処候補は「生成物の表記確認を列挙ファイルに限定せず生成ツリー全体を対象化する」で、今回のテスト追加が `_templates` 全件の対象化を済ませている。恒久ルール・採用の判断は行わない。
- 未確認範囲と次の一手: 上記 `okf.yml.tmpl` の残存表記と、CI・他OSでの検証は未実施。`docs/cli/node-runtime.md`・README の他ワーカー作成分への反映可否は統合工程で判断。
