# 作業記録: T-0007-obsidian-okf

## メタデータ

| 項目 | 値 |
| --- | --- |
| 課題ID / 作業名 | `T-0007-obsidian-okf` |
| 状態 | `進行中` |
| 作業場所 | `C:/Users/rinta/Documents/1_projects/okf-devkit` |
| ブランチ | `codex/t0003-japanese-entry` |
| 開始日時 / 最終更新日時 | `2026-09-06` / `2026-09-06` |
| 開始SHA | `cfdbffe1a01e99432aa9d527c12192fb5a9e3669` |
| 最新HEAD | `cfdbffe1a01e99432aa9d527c12192fb5a9e3669` |
| 作業者 / 製品 / モデル | `Codex` / `Codex` / `current session（モデル名は実行環境で未露出）` |
| 証拠の保存先 | `target repository worklog、terminal output、隔離テストの要約。秘密情報なし` |

## 目的・範囲

### 目的

同じMarkdown + Gitを正本としてObsidianで閲覧できるよう、OKFの索引リンク形式と対象文書の主要導線を整備する。

### 対象

- `src/okf_devkit/defaults.yml`、`src/okf_devkit/cli.py`
- `tests/test_index.py`、`tests/test_render.py`、関連設定テスト
- `okf.yml`、`docs/CONVENTIONS.md`、`README.md`、主要導線のMarkdown
- `docs/**/index.md` のCLI生成結果
- `.gitignore` の `/.obsidian/` 除外
- 本worklogと同名 `.changes.json`
- 設計側 `T-0007-obsidian-okf.md` の検証記録・完了状態・evidence（必須証拠が揃った場合のみ）

### 対象外

- 全既存ノートの一括移行、Wikiリンク変換、専用コピー、community plugin
- 自動同期・公開、上流スキル、製品権限・CIの変更、後続タスクの詳細化
- T-0006の成果物・worklog・宣言の書換え、T-0006の完了更新

### 完了条件

- `C:/Users/rinta/Documents/1_projects/harness/docs/backlog/T-0007-obsidian-okf.md` の完了条件
- `HARNESS_SPEC.md` §4.2、§6、§8.1
- 受け入れ⑬・⑭

## 開始時の状態

開始SHAだけでは対象版を特定できない。開始時に存在した利用者の変更と、今回の変更を区別する。

### 開始時から存在する変更

- 変更済み: `CONTEXT.md` — T-0006のretro/ledger接続
- 変更済み: `harness/core/guide.md` — T-0006のretro導線
- 変更済み: `harness/core/procedures/verify-report.md` — T-0006のretro接続
- 変更済み: `harness/core/templates/worklog.md` — T-0006のretro記録欄
- 変更済み: `harness/project/config.md` — T-0006の台帳・retro接続
- 未追跡: `harness/core/procedures/retrospective.md` — T-0006成果物
- 未追跡: `harness/ledger.md` — T-0006成果物
- 未追跡: `harness/state/journal/T-0006-retro-and-ledger.md` — T-0006 worklog
- 未追跡: `harness/state/journal/T-0006-retro-and-ledger.changes.json` — T-0006変更宣言
- 確認方法: `git status --short`、`git diff --stat`、`git ls-files --others --exclude-standard`（開始SHA時点）

### 今回の変更

- 変更済み: なし（worklog作成後に追記する）
- 未追跡: なし（worklog作成後に追記する）

## 判断と根拠

| 判断 | 根拠 | 影響 |
| --- | --- | --- |
| 索引リンク設定は `index.link_style` とし、`bundle-absolute` / `relative` のみ許可する | 設計側T-0007の実装契約、`HARNESS_SPEC.md` §6.3 | CLI defaults、設定検証、通常/backlog索引 |
| 既定値は `bundle-absolute` のまま、対象 `okf.yml` だけ `relative` を明示する | 設計側T-0007の実装契約、既存golden | 既存利用者の出力互換性、対象生成index |
| `Doc.bundle_rel` とfrontmatter/relatedの意味は変更しない | 設計側T-0007の実装契約、docs規約 | 索引リンク生成だけに設定を閉じ込める |
| Obsidian実機未確認は静的検証の成功へ読み替えない | 設計側T-0007、`HARNESS_SPEC.md` §4.2 / §8.1 | worklogの実機項目と残存リスク |

## 摩擦観測とretroゲート

開始時にT-0006の `harness/ledger.md` を確認した。評価中1件、試行中0件、採用済み0件、期限・見直し日が未定の項目はなく、今回の作業で既存台帳の状態変更は行わない。

| 項目 | 記録 |
| --- | --- |
| 確認範囲 | 開始時点の依頼、T-0007実装契約、開始SHA、既存差分、T-0006台帳を確認済み。完了時に差分・検証・reviewを照合する |
| 該当条件と根拠または非該当理由 | 作業中に観測した事象を完了時にSPEC §7.1と照合する。開始時点では新規トリガーなし |
| 短い観測メモ | 対象 `.venv` は通常権限では起動拒否されたが、対象限定の昇格実行へ切り替えた。実装阻害ではないかを完了時に再確認する |
| 処理済み事象・台帳ID | 未定（完了時に未処理事象だけを判定） |
| 未確認範囲と次の一手 | Obsidian実機の利用可否・版・操作結果は未確認。実装と静的検証後に画面確認を試み、不能なら具体的操作と限界を残す |
| full retrospective | 未定 |
| 人の判断待ち | なし |

## 検証

結果欄は `成功` / `失敗` / `未実行` / `実行不能` の4値だけを使う。実装・検証後に対象版と証拠を記入する。

| 識別子 | 適用 | 結果 | 対象版・範囲 | コマンド / 確認方法 | 期待条件 | 証拠 | 理由・限界 / 再試行 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| index-default-compat | はい | 未実行 | 隔離テストの設定省略・明示 `bundle-absolute` | `tests/test_index.py` | 通常/backlogとも従来形式 | 未取得 | 実装後に実行 |
| index-relative | はい | 未実行 | 隔離テストの通常/backlog、多階層、特殊文字 | `tests/test_index.py` | 起点から実在先へ解決、POSIX区切り、状態を保持 | 未取得 | 実装後に実行 |
| index-invalid-config | はい | 未実行 | 隔離テストの不正 `index.link_style` | `tests/test_index.py` / CLI確認 | 明確なエラー、非0、索引非書込み | 未取得 | 実装後に実行 |
| index-regeneration | はい | 未実行 | 隔離テストの冪等性/check/marker | `tests/test_index.py` | 2回目差分なし、前後文保持、破損時全体停止 | 未取得 | 実装後に実行 |
| render-relative | はい | 未実行 | 隔離テストの隣接HTML・`_site` | `tests/test_render.py` | relative索引リンクがHTML先へ変換、Markdown非変更 | 未取得 | 実装後に実行 |
| obsidian-same-source | はい | 未実行 | 対象Vault実機 | ObsidianでVaultを開き検索・導線クリック | 同じMarkdownから主要文書へ到達 | 未取得 | 実機可否を確認 |
| obsidian-frontmatter | はい | 未実行 | 対象Vault実機 | ネストYAMLをソース表示しGit差分確認 | frontmatter保持、コピー・意図しない変更なし | 未取得 | 実機可否を確認 |
| markdown-navigation | はい | 未実行 | 対象Markdownと索引 | 主要リンクを静的に解決 | configから現行文書・索引・台帳へ到達 | 未取得 | T-0006台帳の現物状態を反映 |
| okf-index-lint-stale | はい | 未実行 | 対象作業ツリー | `okf index --write/lint/index --check/stale --format json` | index/lint成立、stale候補を混同しない | 未取得 | 実装後に実行 |
| private-settings-ignore | はい | 未実行 | 対象Git | `git check-ignore`、`git ls-files -- .obsidian` | `/.obsidian/`除外、tracked設定なし | 未取得 | 実装後に実行 |
| project-required | はい | 未実行 | 対象版 | `.venv/Scripts/python.exe tests/run_all.py` | 失敗0、エラー0 | 未取得 | 実装後に実行 |
| change-declaration | はい | 未実行 | 開始SHAから作業ツリー | `harness/project/check_changes.py --base <開始SHA>` | 未宣言なし | 未取得 | 実装後に実行 |
| code-review-spec | はい | 未実行 | 開始SHAから全差分 | 固定比較点の仕様軸review | 欠落・scope creep・誤実装なし | 未取得 | 実装後に実行 |
| code-review-standards | はい | 未実行 | 開始SHAから全差分 | 固定比較点の標準軸review | 規約違反なし | 未取得 | 実装後に実行 |
| ci-test | はい | 未実行 | GitHub Actions | `.github/workflows/ci.yml`の全matrix | CI test成功 | 未取得 | この環境では未実行なら未実行 |
| ci-smoke | はい | 未実行 | GitHub Actions | `.github/workflows/ci.yml`のsmoke | 独立smoke成功 | 未取得 | この環境では未実行なら未実行 |

### 再試行履歴

- 後で記入する。

## review

### 仕様軸

- 比較点: `cfdbffe1a01e99432aa9d527c12192fb5a9e3669`
- 対象: 開始SHAからのtracked差分、未追跡ファイル、今回の生成物。開始時のT-0006差分は別変更として識別する
- 結果: 実装後にcode-reviewスキルの仕様軸サブエージェントで確認する

### 標準軸

- 比較点: `cfdbffe1a01e99432aa9d527c12192fb5a9e3669`
- 標準: 両リポジトリの `AGENTS.md`、対象config/policy/docs規約、`HARNESS_SPEC.md`、既存テスト
- 結果: 実装後にcode-reviewスキルの標準軸サブエージェントで確認する

## 残作業・妨げ・再開前提

### 残作業

- 索引設定・テスト・対象文書導線を実装し、全検証とreview後に証拠を確定する。

### 妨げ

- Obsidian実機がこの環境で利用できるか未確認。

### 再開前提

- 開始SHA、既存T-0006差分、worklogを現物照合する。
- `requirements.md` → `config.md` → 本worklog → T-0007設計側task / SPEC / 対象差分の順で確認する。
- T-0006の未コミット差分を上書き・巻戻ししない。

## 次の一手

実装契約に沿った索引設定のテストを追加し、既存goldenと同一仕様の既定リンクを先に固定する。

## 完了 / 中断要約

進行中。開始SHAと既存T-0006差分を記録し、対象版の検証は未実行である。
