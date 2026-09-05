# 作業記録: T-0004-workflow-and-completion-contract

## メタデータ

| 項目 | 値 |
| --- | --- |
| 課題ID / 作業名 | `T-0004-workflow-and-completion-contract` |
| 状態 | `完了` |
| 作業場所 | `C:/Users/rinta/Documents/1_projects/okf-devkit` |
| ブランチ | `codex/t0003-japanese-entry` |
| 開始日時 / 最終更新日時 | `2026-09-06` / `2026-09-06` |
| 開始SHA | `2ae7c4261bce9d31324c35d6eaeb244c67794c22` |
| 最終検証時HEAD（完了記録commit直前） | `b8e6e3d`（T-0005外部commitを含む） |
| 作業者 / 製品 / モデル | `Codex / Codex / current session` |
| 証拠の保存先 | `T-0004 commits 4a00b50, b0db5ff, a37649c, c68a0b3, b8e6e3d; declaration check output; verification output; concurrent T-0005 changes excluded; no secrets` |

## 目的・範囲

### 目的

小・通常・大の規模別フロー、4値の検証報告、作業記録、セッション引継ぎを `okf-devkit` に設置する。

### 対象

- `harness/core/procedures/verify-report.md`
- `harness/core/procedures/handover.md`
- `harness/core/templates/worklog.md`
- `harness/core/guide.md`
- `harness/project/config.md`

### 対象外

- `harness/core/procedures/retrospective.md`、改善台帳、CI/hook、配布CLI、Obsidian設定
- 上流スキル、lock、プロファイル、製品の生成テンプレート
- `docs/` のバックログ本文以外の仕様変更

### 完了条件

- 別リポジトリのsource ticket `C:/Users/rinta/Documents/1_projects/harness/docs/backlog/T-0004-workflow-and-completion-contract.md` の受け入れ⑦⑧⑨と追加の完了条件
- 仕様の §2.2、§2.3、§4、§8.1

## 開始時の状態

開始時に作業ツリーはcleanだった。開始SHAはT-0003の成果物を含む `2ae7c4261bce9d31324c35d6eaeb244c67794c22`。

### 開始時から存在する変更

- 変更済み: なし
- 未追跡: なし
- 確認方法: `git status --short --branch`

### 今回の変更

- commit `4a00b50`: 初回の手順、guide/config、worklog
- commit `b0db5ff`: `CONTEXT.md`、未追跡列挙の明記、journalパスのconfig参照化、source ticket参照の修正
- concurrent commit `456c8b5`: T-0005相当のpolicy/config/checker/test（T-0004対象外。変更せず保持）
- commit `c68a0b3`: 小作業の既存テスト必須、configの期待条件、CONTEXTの状態正本説明、review指摘の修正
- 追加宣言: `T-0004-workflow-and-completion-contract.changes.json`（比較点 `456c8b5d3b1004d94681a6d52d073215b5aaa412`）
- T-0004対象外の未コミット変更: `harness/project/check_changes.py`、`tests/test_harness_changes.py`（別セッション由来。変更せず保持）

## 判断と根拠

| 判断 | 根拠 | 影響 |
| --- | --- | --- |
| 検証・報告・引継ぎは自前手順を設置し、retro詳細手順は未設置のまま区別する | T-0004 §着手前提と範囲、HARNESS_SPEC §2.3 / §7.1 | guide/configの未設置表現を今回設置する役割だけ更新 |
| 検証結果は4値、適用外は別の適用欄で表す | HARNESS_SPEC §8.1、T-0004 §手順と記録の内容 | 第5値を作らず、worklogと報告手順を同じ契約にする |
| 開始SHA、既存変更、今回の変更を分け、未コミット・未追跡を二軸reviewへ渡す | HARNESS_SPEC §4.1、T-0004 §決定と根拠 | verify-report、handover、worklog、configに同じ接続を置く |

## 検証

| 識別子 | 適用 | 結果 | 対象版・範囲 | コマンド / 確認方法 | 期待条件 | 証拠 | 理由・限界 / 再試行 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| contract-static | はい | 成功 | `2ae7c426` + 作業ツリー | PowerShellの参照・scope・契約マーカーチェック | 相対リンクが実在し、コアに固有コマンドがなく、必須契約語がある | terminal output: `markdown-links: all relative targets exist`; `core-scope: no project-specific commands or package names`; `contract-markers: all present` | 初回確認後の文書状態 |
| project-required-t0004-boundary | はい | 成功 | target repository / `a37649c`（T-0005commit前） | `.venv/Scripts/python.exe tests/run_all.py`（T-0005のtestを除外） | T-0004変更を含む既存テストが全件成功 | terminal output: `Ran 144 tests`; `OK`; failures 0 / errors 0 / skipped 0 | T-0005の別commitが後から入ったため、対象境界を分離 |
| project-required-current-head | はい | 失敗 | target repository / `456c8b5`（T-0005作業中の観測） | `.venv/Scripts/python.exe tests/run_all.py` | 現在HEADの全テストが成功 | terminal output: `Ran 152 tests`; errors 3 in `test_harness_changes.py` | T-0005外部commitの作業中状態。T-0004変更の成功へ読み替えない。履歴として保持 |
| project-required-current-head-rerun | はい | 成功 | target repository / `c68a0b3` | `.venv/Scripts/python.exe tests/run_all.py` | 現在HEADの全テストが成功 | terminal output: `Ran 153 tests`; failures 0 / errors 0 / skipped 0 | 外部T-0005の完了後に再実行。前回失敗は削除しない |
| okf-index-write | はい | 成功 | target repository docs bundle | `.venv/Scripts/python.exe -m okf_devkit.cli index --write` | OKF索引が最新になる | terminal output: `index.md はすべて最新です。` | `harness/` はOKF外だが入口規約に従い実行 |
| okf-lint | はい | 成功 | target repository docs bundle | `.venv/Scripts/python.exe -m okf_devkit.cli lint` | error 0 / warn 0 | terminal output: `lint: error 0 件 / warn 0 件` | `harness/` はOKF外 |
| okf-index-check | はい | 成功 | target repository docs bundle | `.venv/Scripts/python.exe -m okf_devkit.cli index --check` | exit 0 | terminal output: `index.md はすべて最新です。` | — |
| ci-test | はい | 未実行 | `.github/workflows/ci.yml` | CI test job | Windows/Ubuntu × Python 3.11/3.13 | — | ローカル実行から推定しない |
| ci-smoke | はい | 未実行 | `.github/workflows/ci.yml` | CI smoke job | Ubuntu/Python 3.11の独立smoke | — | CI実行なし |
| change-declaration | はい | 成功 | `456c8b5...b8e6e3d` | `.venv/Scripts/python.exe harness/project/check_changes.py --base 456c8b5d3b1004d94681a6d52d073215b5aaa412 --head b8e6e3d` | 保護対象の宣言漏れなし | terminal output: `result=ok (declaration presence is not human approval or semantic review)` | `verify-report.md` と `config.md` は宣言済み。T-0005外部変更は比較対象外 |
| code-review-standards | はい | 成功 | `456c8b5...c68a0b3`（最終T-0004修正） | code-review Standards axis | 文書規約・入口・config・制約に適合し、判断上のsmellを区別する | final review: no findings after worklog/declaration updates | 初回実装列は `2ae7c426...a37649c` で別途review済み。`456c8b5`は除外 |
| code-review-spec | はい | 成功 | `456c8b5...c68a0b3`（最終T-0004修正） | code-review Spec axis | T-0004/HARNESS_SPECの完了条件を満たしscope creepがない | final review: no findings after worklog/declaration updates | 初回実装列は `2ae7c426...a37649c` で別途review済み。`456c8b5`は除外 |

### 演習

| 識別子 | 結果 | 証拠 |
| --- | --- | --- |
| small-flow | 成功 | 隔離PowerShell演習でguide/verify-reportの小作業ルートとworklog省略条件を確認 |
| normal-flow | 成功 | 隔離PowerShell演習で実装/TDD、二軸review、検証・報告、retroゲートの順を確認 |
| large-flow | 成功 | 隔離PowerShell演習でチケット単位のworklog/reviewと統合検証を確認 |
| report-four-state | 成功 | 隔離PowerShell演習で成功、非ゼロ終了、意図的未実行、存在しない実行環境を別行に記録し、失敗 → 成功の再試行履歴を保持。検査スクリプトの初回2回はアサーション文言の不一致で失敗し、修正後に再実行して成功 |
| review-working-tree | 成功 | 隔離Git演習で開始時の既存変更、コミット済み比較点からのtracked差分、未追跡補完を確認 |
| handover-resume | 成功 | 新規Codexサブセッションが入口 → config/制約 → worklogを読み、`git status --short --branch` とHEADを照合して同じworklogを更新。session/thread idを記録 |
| references-and-scope | 成功 | 相対リンク到達性、コア手順の固有コマンド不在、必須契約マーカーを同一PowerShell検査で確認 |

## review

### 仕様軸

- 比較点: `2ae7c4261bce9d31324c35d6eaeb244c67794c22`
- 対象: `harness/` の今回の変更、未追跡の新規文書、本worklog
- 結果: 静的契約検査、4値演習、作業ツリー演習を通過。初回reviewの指摘を修正し、T-0005外部commitを除外した最終修正reviewも成功

### 標準軸

- 比較点: `2ae7c4261bce9d31324c35d6eaeb244c67794c22`
- 標準: `AGENTS.md`、`harness/core/guide.md`、`harness/project/config.md`、`harness/core/policy/requirements.md`
- 結果: 初回reviewでworklog状態、source ticket参照、CONTEXTの説明、小作業/期待条件の不足を指摘。`b0db5ff`、`c68a0b3`、追加宣言で対応し、最終reviewは成功

## 残作業・妨げ・再開前提

### 残作業

- なし。CI test/smokeは未実行として残し、T-0005外部変更は別作業で扱う。

### 妨げ

- なし。

### 再開前提

- target repositoryの `codex/t0003-japanese-entry` ブランチと開始SHAを維持する。
- worklog、config、requirements、guideの順序を守る。
- CI結果はローカル結果から推定しない。
- `456c8b5` とそれに含まれるT-0005成果物は別作業として保持し、T-0004のreview・検証範囲から除外する。

## 次の一手

完了記録commit後に`git status --short --branch`とHEADを照合し、T-0004対象の変更がcommit済みであることを確認する。

## handover-resume exercise

- 読んだ入口: `AGENTS.md` → `harness/core/guide.md` → `harness/project/config.md` → `harness/core/policy/requirements.md` → 本worklog。
- 観測したブランチ/status: `git status --short --branch` の結果は `## codex/t0003-japanese-entry`。`harness/core/guide.md` と `harness/project/config.md` が変更済み、`harness/core/procedures/` と `harness/core/templates/` と `harness/state/` が未追跡で、開始時からの変更・今回の変更の記録と一致した。HEADは開始SHA `2ae7c4261bce9d31324c35d6eaeb244c67794c22` と一致した。
- 実行した次の一手と結果: 新規セッションとして指定順に入口とworklogを読み、`git status --short --branch` とHEADを確認した。handover-resume受け入れ演習の入口・状態照合は成功。
- worklogの次の状態: handover-resume演習は成功。残作業は固定比較点からの仕様軸・標準軸review、必要な修正の再検証、commitと完了記録。
- セッション識別子: `CODEX_SESSION_ID=01a0721e-f3e0-7703-9c8f-420992da0140`; `CODEX_THREAD_ID=01a0722a-63bd-7f60-a303-6bba8ca508bf`

## 完了 / 中断要約

完了。小・通常・大の入口、4値検証報告、作業記録、別セッション再開、未コミット/未追跡補完、二軸review、対象版固定、変更宣言を設置した。T-0004対象境界の既存テスト144件と現在HEADの153件、OKF検査、参照検査、宣言検査を記録した。CI test/smokeとfull retrospectiveは未実行で、retro詳細手順未設置および外部T-0005作業として理由を残した。

## full retrospective（retro）判定

- 判定: トリガーあり。仮想環境の権限差、別セッションの並行変更、検証スクリプトの再試行が発生した。
- 実施: 未実行。`harness/core/procedures/retrospective.md` はT-0004の範囲外で未設置。失敗・再試行・外部変更を本worklogへ記録し、詳細手順と改善台帳はT-0006で扱う。
- 残存リスク: CIのmatrix/smokeは未実行。T-0005の未コミット変更が別途存在するため、T-0004のcommit・宣言・検証範囲と混同しない。
