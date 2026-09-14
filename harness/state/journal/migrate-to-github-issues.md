# 作業記録: migrate-to-github-issues

## メタデータ

| 項目 | 値 |
| --- | --- |
| 課題ID / 作業名 | `migrate-to-github-issues` |
| 状態 | `完了` |
| 作業場所 | `C:\Users\rinta\Documents\1_projects\okf-devkit` |
| ブランチ | `main` |
| 開始日時 / 最終更新日時 | `2026-09-15` / `2026-09-15` |
| 開始SHA | `c14025aea7e7f5e5c40bbe8ee25b37e00cf5d35c`（作業中に origin/main が4コミット進行し、最終比較点は `2139a799580a3da651bfcdc03d4fb44a4c9c3e2f`） |
| 最新HEAD | `f7c11de`（PR #13 マージコミット、origin/main） |
| 作業者 / 製品 / モデル | `devin` / `devin-cli` / `swe-2-max` |
| 証拠の保存先 | GitHub Issues #4〜#12（shirashu687/okf-devkit）、本worklog |

## 目的・範囲

### 目的

課題管理を `docs/backlog/` から GitHub Issues へ移管し、入口文書・規約・設定の記述を新しい管理先へ合わせる。

### 対象

- GitHub Issues への B-0001〜B-0009 の起票と triage ラベル4件の作成
- `docs/backlog/` の削除
- `AGENTS.md`、`docs/agents/issue-tracker.md`、`docs/agents/triage-labels.md`、`docs/AGENTS.md`、`docs/CONVENTIONS.md`、`CONTEXT.md`、`harness/project/config.md` の更新

### 対象外

- `okf` CLI の `new backlog` / `status` 機能自体（製品機能であり、配布 scaffold・defaults.yml・テストは変更しない）
- GitHub 側の設定変更（branch protection・ruleset・権限）
- コミット・push（利用者の指示があるまで行わない）

### 完了条件

- 利用者依頼: backlog の9件を GitHub Issue へ起票し、backlog 起票を指示する記述を調整する

## 開始時の状態

### 開始時から存在する変更

- なし / 確認方法: `git status --short`（空、HEAD `c14025a`）

### 今回の変更

- 変更済み: `AGENTS.md`、`CONTEXT.md`、`docs/AGENTS.md`、`docs/CONVENTIONS.md`、`docs/agents/{index,issue-tracker,triage-labels}.md`、`docs/index.md`、`harness/project/config.md` — 課題管理先を GitHub Issues へ更新
- 削除: `docs/backlog/`（B-0001〜B-0009 と生成 index）— GitHub Issue #4〜#12 へ移管
- 未追跡: 本worklog と `migrate-to-github-issues.changes.json`

## 判断と根拠

| 判断 | 根拠 | 影響 |
| --- | --- | --- |
| 旧 B ファイルは Issue 起票後に削除 | 利用者の選択 | `docs/backlog/` 丸ごと削除 |
| triage ラベル4件を GitHub に作成し、移管9件へ `needs-triage` を付与 | 利用者の選択 | リポジトリのラベル一覧が増える |
| frontmatter 属性は Issue 本文のメタ表へ記録 | 利用者の選択 | priority/layer の絞り込み用ラベルは作らない |
| `Backlog Item` 型・`okf new backlog` の書式規約は残す | defaults.yml の types/kind_rules が製品機能として同型を lint 対象にするため | CONVENTIONS.md の語彙表・§5・§8 の規則は維持し、運用先の記述のみ変更 |
| Issue 本文から `state: done` 記入のチェック項目と先頭H1を除外 | Issue 化でファイルの state 更新が消滅し、H1 は Issue タイトルと重複するため | 移管本文は実質的な内容を保持 |
| B-0007 は Issue #10 をクローズ | 作業中に取り込んだ origin/main（PR #3）で B-0007 が `state: done` 済みだったため | #10 の本文を最終版へ更新し、PR #3 を示すコメントでクローズ |
| 宣言の比較点を `2139a79` へ更新 | origin/main のマージ後、開始SHAからの差分は PR #3 由来の保護ファイルを含み本タスクの宣言対象でなくなるため | task/PR 両宣言の base が最終差分と一致 |

## 摩擦観測とretroゲート

| 項目 | 記録 |
| --- | --- |
| 確認範囲 | 依頼内容、入口文書、課題規約、triage ラベル表、執筆規約、config、CONTEXT、ledger、作成 Issue・ラベル、全差分、検証結果 |
| 該当条件と根拠または非該当理由 | 開始時に `harness/ledger.md` を確認: 評価中4件・試行0件、期限超過・見直し期限のある項目なし（マージ取込後は評価中5件・最終確認日2026-09-10、いずれも期限未定）。トリガーなし |
| 短い観測メモ | Git Bash の `/tmp` と Windows Python のパス解釈が食い違い、シェル経由の本文修正が一度だけ無効になった。実害なし（無変更の再アップロード）、Python 完結の修正スクリプトで解消。作業中に origin/main へ PR #3 がマージ済みと判明し、B-0007 完了・backlog modify/delete・config/CONVENTIONS 競合を解消した |
| 処理済み事象・台帳ID | なし |
| 未確認範囲と次の一手 | なし（PR #13 の CI 9ジョブは実結果で成功を確認） |
| full retrospective | 不要（トリガーなし） |
| 人の判断待ち | なし |

## 検証

| 識別子 | 適用 | 結果 | 対象版・範囲 | コマンド / 確認方法 | 期待条件 | 証拠 | 理由・限界 / 再試行 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| issues-created | はい | 成功 | GitHub shirashu687/okf-devkit | `gh label create` ×4、`gh issue create` ×9、`gh issue edit` ×18（本文確定と整形の2 pass） | ラベル4件作成、B-0001〜B-0009 相当の Issue に `needs-triage` | Issue #4〜#12（`gh issue list` で確認）、#10 は B-0007 完了のため本文を最終版へ更新しクローズ | 初回の本文修正は /tmp パス食い違いで未適用。実害なし・Python スクリプトで再適用済み |
| required-tests | はい | 成功 | マージ取込後のブランチ先端 `8672f04` | `.venv/Scripts/python.exe tests/run_all.py` | 終了コード0・失敗0・エラー0 | `Ran 169 tests OK`、集計 `実行 169 件 / 失敗 0 / エラー 0`（upstream取込で+1件） | — |
| okf-index | はい | 成功 | docs/ 更新後 | `.venv/Scripts/python.exe -m okf_devkit.cli index --write` | 終了コード0で最新状態 | `index.md を 2 件 更新`（docs/index.md、docs/agents/index.md） | — |
| okf-lint | はい | 成功 | docs/ 更新後 | `.venv/Scripts/python.exe -m okf_devkit.cli lint` | error 0 / warn 0 | `lint: error 0 件 / warn 0 件` | — |
| okf-index-check | はい | 成功 | docs/ 更新後 | `.venv/Scripts/python.exe -m okf_devkit.cli index --check` | 終了コード0 | `index.md はすべて最新です` | — |
| protected-declaration | はい | 成功 | `2139a79..8672f04`（PR差分） | `.venv/Scripts/python.exe harness/project/check_changes.py --scope pull-request --base 2139a79… --head HEAD` | 終了コード0 | `result=ok`、AGENTS.md と harness/project/config.md が `declaration=declared` | 開始SHA `c14025a` での task 検査も事前に exit 0。main 取込後は比較点を `2139a79` へ更新し宣言を追随 |
| ci-pr | はい | 成功 | PR #13 head `8672f04` | `gh pr checks 13 --watch` | Test 4環境・Node 4環境・smoke が全て pass | run 34864137623: Test(ubuntu/win × py3.11/3.13)、Node(ubuntu/win × 22/24)、End-to-end smoke 全て pass | — |

## review

### 仕様軸

- 比較点: `c14025aea7e7f5e5c40bbe8ee25b37e00cf5d35c`
- 対象: 作業ツリー全体（未追跡含む）
- 結果: 依頼どおり9件が Issue #4〜#12 へ移管され（#10 は B-0007 完了のためクローズ）、frontmatter 属性は本文メタ表に保持、Issue 間参照は `#N` へ解決済み。`docs/backlog/` は削除済み。入口・規約・config・CONTEXT の課題管理先記述は GitHub Issues を指し、PR #13 として origin/main へマージ済み（`f7c11de`）。残存リスク: 旧ファイルの本文は git 履歴依存（Issue 本文に要点は保持済み）。

### 標準軸

- 比較点: `c14025aea7e7f5e5c40bbe8ee25b37e00cf5d35c`
- 標準: AGENTS / config / policy / tests / conventions
- 結果: 保護対象2件（`AGENTS.md`、`harness/project/config.md`）は task / pull-request 両 scope の `.changes.json` で宣言し check_changes が exit 0。上流管理ファイル・tests・CI・okf.yml は本差分で未変更。lint error/warn 0（upstream 由来の related リンク切れ2件を修正済み）、index --check 0、既存テスト169件成功、PR CI 9ジョブ成功。`docs/log.md` は git 履歴起点のため `okf log` の自動追記対象外の変更であり手動追記は行わない。

## 残作業・妨げ・再開前提

### 残作業

- なし（PR #13 としてマージ済み）

### 妨げ

- なし

### 再開前提

- `gh` は github.com アカウント `shirashu687` で認証済み（`repo` スコープ）。対象リポジトリは `shirashu687/okf-devkit`。

## 次の一手

なし。必要に応じて各 Issue の triage（カテゴリ＋状態ラベルの付与）を進める。

## 完了 / 中断要約

課題管理を `docs/backlog/` から GitHub Issues へ移管し、PR #13 としてマージした（`f7c11de`）。B-0001〜B-0009 は Issue #4〜#12 へ移管（#10 は B-0007 が PR #3 で完了済みのためクローズ）、triage 用ラベル4件を新規作成。作業中に origin/main へ Node.js 実装（PR #3）がマージ済みと判明し、取り込み競合（backlog modify/delete・CONVENTIONS/config 内容）を解消した。検証は lint error 0/warn 0、index --check 0、テスト169件成功、check_changes PR-scope exit 0、PR CI 9ジョブ成功。retro トリガーなし。
