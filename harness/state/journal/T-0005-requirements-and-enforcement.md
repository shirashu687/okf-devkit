# 作業記録: T-0005-requirements-and-enforcement

## メタデータ

| 項目 | 値 |
| --- | --- |
| 課題ID / 作業名 | `T-0005-requirements-and-enforcement` |
| 状態 | `完了` |
| 作業場所 | `C:/Users/rinta/Documents/1_projects/okf-devkit` |
| ブランチ | `codex/t0003-japanese-entry` |
| 開始日時 / 最終更新日時 | `2026-09-06` / `2026-09-06` |
| 開始時観測SHA | `4a00b50`（T-0004成果物コミット、作業ツリーclean） |
| T-0005比較点 | `a37649cb01d73a5dc59801835b6e3e1e5eb5e3bd` |
| 最新HEAD（T-0005記録時） | `89e8c56c1c15767d8e0f30449edfd31bfb704eb7` |
| T-0005成果物コミット | `456c8b5d3b1004d94681a6d52d073215b5aaa412`, `8acec25fff76a6f20c4d9d9aa97abf03b2ab57a4` |
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
- 作業中に別作業のT-0004 review修正コミット `b0db5ff` と `a37649c` が同じブランチへ追加された。これらはT-0005実装の既存前提として取り込んだ。
- T-0005実装 `456c8b5` の後に、T-0004の `c68a0b3`、宣言 `b8e6e3d`、完了記録 `db057a5`、`21aef73`、`5267934`、`c6b91e7`、`4cb39dc`、`89e8c56` が同じブランチへ挿入された。T-0005の修正 `8acec25` はその途中にあり、T-0004のファイルは変更せず保持した。
- T-0004 worklogは現在「完了」であり、着手前提の実装・検証・引継ぎ記録が揃った。T-0004の完了コミットはT-0005の成果物・宣言・review対象から除外し、T-0005の証拠は `a37649c..456c8b5` と、修正コミット `8acec25` のファイル差分に分けて記録する。

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
| ci-failure-surface | はい | 成功 | 一時Gitリポジトリ | `.venv/Scripts/python.exe -m unittest tests.test_harness_changes -v` | 未宣言1、宣言後0、終了コードを保持 | terminal output: 11 tests `OK`; `test_protected_change_fails_then_declared_change_succeeds` | ローカル演習でありGitHub CI実行ではない |
| protected-policy | はい | 成功 | 一時Gitリポジトリ | 同上 | protected変更、削除、rename旧新（protected↔ordinaryを含む）を列挙し未宣言1/宣言0 | terminal output: `test_deleted_protected_path_requires_declaration`, `test_rename_between_protected_and_ordinary_paths_requires_both_names`, `test_rename_requires_old_and_new_protected_paths` | 意味上の弱体化判定はしない |
| upstream-drift | はい | 成功 | 一時Gitリポジトリ | 同上 | `.agents` / `.claude`両コピーとlockを分類 | terminal output: `test_upstream_copies_and_lock_are_each_reported` | 上流原文との同一性は保証しない |
| ordinary-change | はい | 成功 | 一時Gitリポジトリ | 同上 | 普通の変更・無変更を宣言なし0 | terminal output: `test_no_changes_and_ordinary_change_are_allowed` | ignore対象は対象外 |
| declaration-validation | はい | 成功 | 一時Gitリポジトリ | 同上 | JSON、base、worklog、path、reason、重複、glob、古い宣言、head内のtree型worklogを拒否 | terminal output: `test_head_declaration_worklog_must_be_a_blob`, `test_invalid_declarations_are_rejected`, `test_unchanged_old_declaration_is_not_reused` | 宣言は人の許可の証明ではない |
| working-tree | はい | 成功 | 一時Gitリポジトリ | 同上 | staged/unstaged/未追跡/空白・日本語名を検出し、head指定は作業ツリーを無視 | terminal output: `test_working_tree_covers_staged_unstaged_and_untracked_but_head_does_not` | — |
| unavailable-base | はい | 成功 | 一時Gitリポジトリ | 同上 | 不明SHA、shallow、競合をすべて2 | terminal output: `test_unavailable_base_head_shallow_and_conflict_are_not_success` | 全ゼロは同テストの不明比較点として拒否条件を含む |
| ci-wiring | はい | 成功 | `.github/workflows/ci.yml` | PowerShellのPR条件、base/head環境変数、fetch-depth、既存job、終了コード握り潰しの静的確認 | PRのみ実行、既存test/smoke維持 | terminal output: `ci-wiring-pr-and-env: success`, `ci-preserves-existing-jobs: success`, `ci-failure-surface: success` | 実CIは別結果 |
| scope-and-review | はい | 成功 | T-0005の分離差分 | `a37649c..456c8b5` と `b8e6e3d..8acec25` の二軸review、T-0004割込み境界、同時改変・権限・ruleset限界を確認 | 残存限界を記録 | 初回Spec reviewの指摘（rename、tree型worklog）を `8acec25` で修正。修正後は仕様軸/標準軸とも追加の未解決指摘なし（標準軸agentはタイムアウトのため手動reviewで補完） | `a37649c..c6b91e7` の一括検査はT-0004宣言のbase不一致・config重複で失敗。別タスクを同一PRへ統合する場合は共通baseへ調整が必要 |
| project-required | はい | 成功 | target repository HEAD `c6b91e7` | `.venv/Scripts/python.exe tests/run_all.py` | 既存テスト成功 | terminal output: `Ran 155 tests`; `OK`; failures 0 / errors 0 / skipped 0 | PATHの`python`は未検出、venv通常起動は失敗したため同じコマンドを昇格実行。T-0004完了後の全テストを含む |
| syntax | はい | 成功 | T-0005 Python files | `.venv/Scripts/python.exe -m py_compile harness/project/check_changes.py tests/test_harness_changes.py` | 構文エラー0 | exit 0 | — |
| ci-test | はい | 未実行 | GitHub Actions | workflow `test` | Windows/Ubuntu × Python 3.11/3.13 | — | 実CI未実行。ローカルから推定しない |
| ci-smoke | はい | 未実行 | GitHub Actions | workflow `smoke` | Ubuntu/Python 3.11 smoke | — | 実CI未実行。ローカルから推定しない |

### 環境上の再試行

PATH上の `python` は存在せず、指定された既存venvは通常権限ではプロセス起動に失敗した。同じ `.venv/Scripts/python.exe` コマンドを昇格実行して結果を取得した。初回静的probeは期待文言の誤りで失敗したが、実文言に合わせて再実行し成功した。いずれも昇格実行の成功をGitHub CI成功へ置き換えない。

## 仕様・標準review

### 仕様軸

- 比較点: `a37649cb01d73a5dc59801835b6e3e1e5eb5e3bd`（初回）および `b8e6e3d9662d090e74d2a6b26b9500f3dc17b85b`（修正commit）
- 仕様: source ticket T-0005 と `HARNESS_SPEC.md` §4.2 / §8.2 / §8.3
- 対象: T-0005の `456c8b5` と `8acec25` の差分。T-0004の割込みcommitは除外
- 結果: 成功。初回Spec reviewはrenameの旧新分類とtree型worklogを指摘し、`8acec25`で修正。修正後は手動の仕様照合で追加の未解決指摘なし。scope creepなし

### 標準軸

- 比較点: `a37649cb01d73a5dc59801835b6e3e1e5eb5e3bd`（初回）および `b8e6e3d9662d090e74d2a6b26b9500f3dc17b85b`（修正commit）
- 標準: `AGENTS.md`、`harness/core/guide.md`、`harness/project/config.md`、`harness/core/policy/requirements.md`、既存tests/CIの規約
- 結果: 成功。対象AGENTS/config/requirements、既存tests/CI規約を照合し、hard violationなし。baseline smellも重大な追加指摘なし。標準軸agentが時間内に結果を返さなかったため、固定差分を手動で再確認した

## 残作業・妨げ・再開前提

### 残作業

- T-0005の実装・専用演習・既存テスト・分離差分review・成果物commitは完了した。
- GitHub Actionsの実CI test/smokeは未実行のまま残す。
- T-0004とT-0005を同じPR差分として扱う場合、宣言の比較baseを共通化し、config重複を人が確認してから統合する。今回その調整やGitHub設定変更は行わない。

### 妨げ

- T-0005作業中に別作業のT-0004コミットが同じブランチへ挿入されたため、T-0005の二つの成果物commitを分離してreview・検査した。結合した比較の失敗は隠さず記録し、T-0005固有の成功へ読み替えていない。
- GitHub Actionsの実行、GitHub settings/rulesetの変更、製品権限の確認・変更は本作業の権限・範囲外であり、未実行として扱う。

### 再開前提

- target repositoryの現在ブランチ、worklog、宣言、最新HEADを現物照合する。
- `requirements.md` → `config.md` → 本worklog → T-0005差分の順に読み、開始比較点を検査へ渡す。
- 既存T-0004 worklogの状態を本タスクの成功へ転記しない。

## 次の一手

T-0005のsource ticketへ成果物commit `456c8b5` と `8acec25` をevidenceとして記録し、完了状態へ更新する。combined PRの宣言base調整はT-0005の範囲外として人が判断する。

## 完了 / 中断要約

T-0005実装・検証・分離差分review・成果物commitは完了。実CI test/smokeは未実行。別タスクT-0004とのcombined PRでは宣言base統合が必要な残存リスクを記録した。
