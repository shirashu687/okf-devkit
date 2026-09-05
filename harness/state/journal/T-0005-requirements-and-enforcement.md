# 作業記録: T-0005-requirements-and-enforcement

## メタデータ

| 項目 | 値 |
| --- | --- |
| 課題ID / 作業名 | `T-0005-requirements-and-enforcement` |
| 状態 | `進行中` |
| 作業場所 | `C:/Users/rinta/Documents/1_projects/okf-devkit` |
| ブランチ | `codex/t0003-japanese-entry` |
| 開始日時 / 最終更新日時 | `2026-09-06` / `2026-09-06` |
| 開始時観測SHA | `4a00b50`（T-0004成果物コミット、作業ツリーclean） |
| T-0005比較点 | `a37649cb01d73a5dc59801835b6e3e1e5eb5e3bd` |
| 最新HEAD | `a37649cb01d73a5dc59801835b6e3e1e5eb5e3bd` |
| 作業者 / 製品 / モデル | `Codex / Codex / current session` |
| 証拠の保存先 | `target repository commit and verification output; no secrets` |

## 目的・範囲

必須制約を実在する差分検査・宣言・既存CIへ接続し、検査できない範囲を明示する。正本は別リポジトリの `C:/Users/rinta/Documents/1_projects/harness/HARNESS_SPEC.md` と source ticket `T-0005-requirements-and-enforcement.md` である。

### 対象

- `harness/core/policy/requirements.md`
- `harness/project/config.md`
- `harness/project/check_changes.py`
- `tests/test_harness_changes.py`
- `.github/workflows/ci.yml`
- 本worklogと対応する `.changes.json`

### 対象外

- GitHub settings / ruleset / branch protectionの変更
- 製品・実行環境の権限変更、外部送信、専用秘密情報スキャナ
- 上流スキル本文、`.agents/skills/`、`.claude/skills/`、`skills-lock.json`、採用プロファイルの変更
- 公開CLI・配布テンプレートへの変更
- 後続タスクの詳細化、T-0004 worklogの書換え

## 着手前の照合と既存変更

- T-0004の実装成果物（手順、template、guide/config、worklog）は `4a00b50` に存在し、開始時の作業ツリーはcleanだった。
- 作業中に別作業のT-0004 review修正コミット `b0db5ff` と `a37649c` が同じブランチへ追加された。これらはT-0005実装の既存前提として取り込み、T-0005の宣言対象には含めない。T-0004 worklogは現物の状態どおり「進行中」であり、本タスクでは完了へ変更しない。
- その後のT-0005未コミット変更は、保護対象のworkflow、policy、config、検査スクリプト、テストである。worklogと宣言は通常のjournalファイルとして追加する。

## 実装の判断と根拠

| 判断 | 根拠 | 影響 |
| --- | --- | --- |
| 検査は対象専用のPythonスクリプトに留め、公開CLIへ組み込まない | T-0005 §着手前提と成果物、HARNESS_SPEC §2.2 | GitのNUL区切りと標準ライブラリで実装し、配布面を増やさない |
| `--head` なしは作業ツリー、ありは2コミットだけを検査する | T-0005「変更検査の契約」「CIへの接続」 | staged/unstaged/未追跡、rename、空白/日本語名を扱い、CIの合成mergeをheadにしない |
| 宣言は同じ比較差分内で変更されたものだけ読む | T-0005「正当な変更の宣言と確認」 | 古い宣言を新しい変更へ再利用せず、base・worklog・path・reasonを検証する |
| 0/1/2は検査状態であり、承認や意味上の安全を表さない | HARNESS_SPEC §8.1、T-0005「変更検査の契約」 | 出力・制約表・config・worklogで人のreviewと限界を明記する |
| PRの既存test jobだけへstepを追加し、push時は実行しない | T-0005「CIへの接続と失敗の報告」 | 既存test/smokeと失敗終了コードを維持し、GitHub settingsを変更しない |

## 検証

結果は `成功` / `失敗` / `未実行` / `実行不能` の4値だけで記録する。ローカル演習をGitHub CI実行とは呼ばない。

| 識別子 | 適用 | 結果 | 対象版・範囲 | コマンド / 確認方法 | 期待条件 | 証拠 | 理由・限界 / 再試行 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| requirements-map | はい | 成功 | T-0005変更 | PowerShellの5制約・4値・参照・限界の静的確認 | 5制約すべてに対応がある | terminal output: `requirements-map-constraints: success`, `requirements-map-four-states: success` | 初回probeは文言の期待値を誤って失敗したが、実文言に合わせて再実行し成功 |
| ci-failure-surface | はい | 成功 | 一時Gitリポジトリ | `.venv/Scripts/python.exe -m unittest tests.test_harness_changes -v` | 未宣言1、宣言後0、終了コードを保持 | terminal output: 8 tests `OK`; `test_protected_change_fails_then_declared_change_succeeds` | ローカル演習でありGitHub CI実行ではない |
| protected-policy | はい | 成功 | 一時Gitリポジトリ | 同上 | protected変更、rename旧新を列挙し未宣言1/宣言0 | terminal output: `test_protected_change_fails_then_declared_change_succeeds`, `test_rename_requires_old_and_new_protected_paths` | 意味上の弱体化判定はしない |
| upstream-drift | はい | 成功 | 一時Gitリポジトリ | 同上 | `.agents` / `.claude`両コピーとlockを分類 | terminal output: `test_upstream_copies_and_lock_are_each_reported` | 上流原文との同一性は保証しない |
| ordinary-change | はい | 成功 | 一時Gitリポジトリ | 同上 | 普通の変更・無変更を宣言なし0 | terminal output: `test_no_changes_and_ordinary_change_are_allowed` | ignore対象は対象外 |
| declaration-validation | はい | 成功 | 一時Gitリポジトリ | 同上 | JSON、base、worklog、path、reason、重複、glob、古い宣言を拒否 | terminal output: `test_invalid_declarations_are_rejected`, `test_unchanged_old_declaration_is_not_reused` | 宣言は人の許可の証明ではない |
| working-tree | はい | 成功 | 一時Gitリポジトリ | 同上 | staged/unstaged/未追跡/空白・日本語名を検出し、head指定は作業ツリーを無視 | terminal output: `test_working_tree_covers_staged_unstaged_and_untracked_but_head_does_not` | — |
| unavailable-base | はい | 成功 | 一時Gitリポジトリ | 同上 | 不明SHA、shallow、競合をすべて2 | terminal output: `test_unavailable_base_head_shallow_and_conflict_are_not_success` | 全ゼロは同テストの不明比較点として拒否条件を含む |
| ci-wiring | はい | 成功 | `.github/workflows/ci.yml` | PowerShellのPR条件、base/head環境変数、fetch-depth、既存job、終了コード握り潰しの静的確認 | PRのみ実行、既存test/smoke維持 | terminal output: `ci-wiring-pr-and-env: success`, `ci-preserves-existing-jobs: success`, `ci-failure-surface: success` | 実CIは別結果 |
| scope-and-review | はい | 未実行 | T-0005差分 | 仕様軸/標準軸review、同時改変・権限・ruleset限界を確認 | 残存限界を記録 | — | code-review完了後に更新 |
| project-required | はい | 成功 | target repository worktree | `.venv/Scripts/python.exe tests/run_all.py` | 既存テスト成功 | terminal output: `Ran 152 tests`; `OK`; failures 0 / errors 0 / skipped 0 | PATHの`python`は未検出、venv通常起動は失敗したため同じコマンドを昇格実行 |
| syntax | はい | 成功 | T-0005 Python files | `.venv/Scripts/python.exe -m py_compile harness/project/check_changes.py tests/test_harness_changes.py` | 構文エラー0 | exit 0 | — |
| ci-test | はい | 未実行 | GitHub Actions | workflow `test` | Windows/Ubuntu × Python 3.11/3.13 | — | 実CI未実行。ローカルから推定しない |
| ci-smoke | はい | 未実行 | GitHub Actions | workflow `smoke` | Ubuntu/Python 3.11 smoke | — | 実CI未実行。ローカルから推定しない |

### 環境上の再試行

PATH上の `python` は存在せず、指定された既存venvは通常権限ではプロセス起動に失敗した。同じ `.venv/Scripts/python.exe` コマンドを昇格実行して結果を取得する。昇格実行の成功をGitHub CI成功へ置き換えない。

## 仕様・標準review

### 仕様軸

- 比較点: `a37649cb01d73a5dc59801835b6e3e1e5eb5e3bd`
- 仕様: source ticket T-0005 と `HARNESS_SPEC.md` §4.2 / §8.2 / §8.3
- 対象: 比較点からのT-0005変更、未コミット・未追跡を含む
- 結果: 未実施

### 標準軸

- 比較点: `a37649cb01d73a5dc59801835b6e3e1e5eb5e3bd`
- 標準: `AGENTS.md`、`harness/core/guide.md`、`harness/project/config.md`、`harness/core/policy/requirements.md`、既存tests/CIの規約
- 結果: 未実施

## 残作業・妨げ・再開前提

### 残作業

- 変更検査の全演習、対象既存テスト、静的なCI配線・参照確認を実行して記録する。
- 開始比較点から仕様/標準の二軸reviewを行い、指摘があれば修正後に影響検証を再実行する。
- T-0005成果物をcommitし、そのSHAを本worklogとsource ticketのevidenceへ記録する。
- 成果物commitと必須証拠が揃った場合だけsource ticketを完了へ更新する。

### 妨げ

- T-0005作業中に別作業のコミットが同じブランチへ追加された。最新比較点へ固定し、既存T-0004変更とT-0005差分を分離して確認する。
- GitHub Actionsの実行、GitHub settings/rulesetの変更、製品権限の確認・変更は本作業の権限・範囲外であり、未実行として扱う。

### 再開前提

- target repositoryの現在ブランチ、worklog、宣言、最新HEADを現物照合する。
- `requirements.md` → `config.md` → 本worklog → T-0005差分の順に読み、開始比較点を検査へ渡す。
- 既存T-0004 worklogの状態を本タスクの成功へ転記しない。

## 次の一手

最新HEADと作業ツリーを再確認し、`.venv/Scripts/python.exe tests/run_all.py`、T-0005一時Git演習、二軸reviewを実行する。

## 完了 / 中断要約

実装・検証中。成果物commit、二軸review、worklog/source ticketの証拠更新が終わるまで完了としない。
