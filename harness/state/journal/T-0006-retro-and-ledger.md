# 作業記録: T-0006-retro-and-ledger

## メタデータ

| 項目 | 値 |
| --- | --- |
| 課題ID / 作業名 | `T-0006-retro-and-ledger` |
| 状態 | `進行中` |
| 作業場所 | `C:/Users/rinta/Documents/1_projects/okf-devkit` |
| ブランチ | `codex/t0003-japanese-entry` |
| 開始日時 / 最終更新日時 | `2026-09-06` / `2026-09-06` |
| 開始SHA | `cfdbffe1a01e99432aa9d527c12192fb5a9e3669` |
| 最新HEAD | `cfdbffe1a01e99432aa9d527c12192fb5a9e3669` |
| 作業者 / 製品 / モデル | `Codex` / `Codex` / `GPT-5（正確なdeployment名は実行環境に未露出）` |
| 証拠の保存先 | `target repository worklog、terminal output、隔離演習の要約。秘密情報なし` |

## 目的・範囲

### 目的

摩擦を依頼・差分・検証・review・引継ぎの照合で検知し、トリガーがある回だけfull retrospectiveを行い、改善候補を上限つきの台帳へ接続する。

### 対象

- `harness/core/procedures/retrospective.md`
- `harness/ledger.md`
- `harness/core/procedures/verify-report.md`
- `harness/core/templates/worklog.md`
- `harness/core/guide.md`
- `harness/project/config.md`
- `CONTEXT.md`
- 本worklogと対応する `.changes.json`
- 設計側 `T-0006-retro-and-ledger.md` の検証記録・完了状態・evidence（必須証拠が揃った場合のみ）

### 対象外

- 専用自動検知コード、台帳validator、CI/hook、定時起動
- 製品権限、外部設定、外部送信、不可逆操作
- 上流スキル本文、`.agents/skills/`、`.claude/skills/`、`skills-lock.json`、採用プロファイル
- 配布機構、Obsidian設定、後続タスク本文、採用済み改善の実装
- T-0004/T-0005の過去worklog・宣言の書換え、演習結果の本番台帳への混入

### 完了条件

- 設計側 source ticket `C:/Users/rinta/Documents/1_projects/harness/docs/backlog/T-0006-retro-and-ledger.md` の受け入れ⑪⑫と追加の完了条件
- `HARNESS_SPEC.md` §2.2、§4.2、§6.4、§7、§8.1、§8.2

## 開始時の状態

対象リポジトリを現物確認し、開始時はcleanだった。開始SHAは `cfdbffe1a01e99432aa9d527c12192fb5a9e3669`、ブランチは `codex/t0003-japanese-entry`。設計側source repositoryのHEADは `dd2b38a991d29d964da6ddfc6fb2149da4e29b14` で、`HARNESS_SPEC.md`、T-0006、T-0007に利用者側の既存未コミット変更があったため保持し、本タスクの設計更新以外は変更しない。

### 開始時から存在する変更

- 対象リポジトリの変更済み: なし
- 対象リポジトリの未追跡: なし
- 確認方法: `git status --short --branch`、`git diff --stat`、`git diff --cached --stat`、`git ls-files --others --exclude-standard`

### 今回の変更

- 変更済み: `CONTEXT.md`、`harness/core/guide.md`、`harness/core/procedures/verify-report.md`、`harness/core/templates/worklog.md`、`harness/project/config.md`
- 未追跡: `harness/core/procedures/retrospective.md`、`harness/ledger.md`、本worklog、`.changes.json`

### 作業中に検出した並行変更

開始時は存在しなかったが、隔離演習とreviewの間に別作業T-0007の変更が同じ作業ツリーへ追加された。次のパスはT-0006の変更ではなく、削除・上書き・コミット・T-0006 reviewの対象にしない。

- `.gitignore`
- `README.md`
- `docs/AGENTS.md`
- `docs/CONVENTIONS.md`
- `docs/agents/index.md`
- `docs/index.md`
- `docs/project/index.md`
- `okf.yml`
- `src/okf_devkit/cli.py`
- `src/okf_devkit/defaults.yml`
- `src/okf_devkit/renderer.py`
- `tests/helpers.py`
- `tests/test_index.py`
- `tests/test_render.py`
- `harness/state/journal/T-0007-obsidian-okf.md`

`okf.yml`、`tests/helpers.py`、`tests/test_index.py`、`tests/test_render.py` は変更検査上の保護対象でもある。混在した作業ツリー全体をT-0006の宣言成功とみなさず、T-0006の成果物だけを明示的にコミットし、完了境界では `--head <T-0006成果物commit>` の2コミット検査で宣言を確認する。並行変更は同じブランチ上で保持し、T-0007側の担当が別途扱う。

## 判断と根拠

| 判断 | 根拠 | 影響 |
| --- | --- | --- |
| retroは依頼・差分・検証・review・引継ぎの照合でAIが判定し、トリガーなしの回は通常報告で終える | source T-0006「決定と根拠」、`HARNESS_SPEC.md` §7.1 | `retrospective.md`、`verify-report.md`、guide、worklogを接続 |
| 改善候補は台帳へ置き、試行前の具体的差分・効果・期限・巻戻し条件なしに採用へ進めない | `HARNESS_SPEC.md` §7.2 / §7.3.1 | 台帳の状態遷移、上限、人の判断待ちを文書化 |
| T-0004一次記録から、検査プローブの期待文言不一致と再試行を一件の実観測として登録し、仮想の試行・効果・承認は登録しない | T-0004 worklogの `report-four-state`、source T-0006「台帳の書式」 | `IMP-0001` は観測状態・回数1のまま保持 |
| 専用自動検知・validator・定時起動は追加しない | source T-0006「着手前提と範囲」、利用者指定 | 意味判定の運用上の限界を手順・config・CONTEXTへ明記 |

## 摩擦観測とretroゲート

開始時に依頼、完了条件、T-0004/T-0005成果物、対象差分、既存検証記録、review/引継ぎ記録の所在を照合した。T-0004の一次記録に、仕様 §7.1 のトリガーに該当する検証プローブの再試行があり、実観測として `IMP-0001` に登録した。実装中にも古い未設置分岐の残存（`IMP-0002`）と、指定venvの通常権限起動不能から昇格再試行へ進んだ環境差（`IMP-0003`）を観測し、別症状として登録した。T-0004の他の要約（並行変更）は、同じ症状の3回とは数えていない。

| 項目 | 記録 |
| --- | --- |
| 確認範囲 | source `HARNESS_SPEC.md` §7、T-0006、対象AGENTS/docs入口/CONTEXT/config/requirements、T-0004/T-0005 worklog・成果物・宣言、対象開始diff |
| 該当条件と根拠または非該当理由 | 該当。T-0004 `report-four-state` に検査スクリプトの期待文言不一致による初回2回の失敗と修正後再実行が記録されている。これは通常の意図したTDD redだけではなく、検証プローブの期待条件不一致である。 |
| 短い観測メモ | T-0004作業記録に期待文言不一致が2回発生し、修正後に成功した観測がある。T-0006の隔離演習の入力・出力は台帳へ移していない。 |
| 処理済み事象・台帳ID | `IMP-0001` として観測を登録。今回の作業中に未処理の別事象があれば完了時に追加照合する。 |
| 未確認範囲と次の一手 | 過去の全セッション、実際の改善効果、採用承認、同症状の独立発生回数は未確認。次回同形式の検証で対象版・期待条件・再試行を比較する。 |
| full retrospective | 実施。`IMP-0001`〜`IMP-0003`の事実・根拠・仮説・分類・未開始の対処案を整理し、演習結果と実観測を分離して記録した。 |
| 人の判断待ち | `IMP-0001`〜`IMP-0003`はいずれも観測。試行条件が未定のため開始しておらず、採用承認・改善効果はない。 |

## 検証

実装中のため、下表は実行後に対象版と証拠を更新する。結果欄は `成功` / `失敗` / `未実行` / `実行不能` の4値だけを使う。

| 識別子 | 適用 | 結果 | 対象版・範囲 | コマンド / 確認方法 | 期待条件 | 証拠 | 理由・限界 / 再試行 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| retro-trigger-positive | はい | 成功 | `cfdbffe1...` + 作業ツリー / `%TEMP%`隔離コピー | `retrospective.md`の手順を、T-0004 `report-four-state`記録へ適用 | 摩擦と根拠を挙げ、full retroと実観測IDへ到達。回数を捏造しない | terminal output: `retro-trigger-positive=success`; `target-version=cfdbffe...+working-tree` | Codex current session。演習入力は本番台帳へ追加していない |
| retro-trigger-negative | はい | 成功 | `cfdbffe1...` + `%TEMP%`隔離コピー | 摩擦のない文言修正ケースを手順で照合 | 非該当理由を残し、追加retro文書・台帳行を作らない | terminal output: `retro-trigger-negative=success` | — |
| retro-dialogue-boundary | はい | 成功 | `cfdbffe1...` + `%TEMP%`隔離ケース8件 | 通常対話・計画分担・意図したred・要件欠落等を照合 | 5件を非該当、3件を該当として区別する | terminal output: `retro-dialogue-boundary=success; 5 non-trigger and 3 trigger` | — |
| retro-evidence-gap | はい | 成功 | `cfdbffe1...` + `%TEMP%`隔離ケース | 差分/review根拠が欠けたケースを照合 | 取得可能な情報を確認し、確認不能と具体的次の一手を残す | terminal output: `retro-evidence-gap=success` | 摩擦なしとは断定していない |
| ledger-dedup | はい | 成功 | `%TEMP%`隔離台帳コピー | 再読、独立発生、別症状、閉じた項目の再発をインメモリ照合 | 再読は加算せず、独立発生を同IDへ加算し履歴を保持する | terminal output: `ledger-dedup=success` | — |
| ledger-capacity | はい | 成功 | `%TEMP%`隔離台帳コピー | 評価10件、試行3件、採用済み2件、新規観測を照合 | 黙って捨てず、統合/却下理由を残し、4件目の試行を開始しない | terminal output: `ledger-capacity=success` | 採用済みは評価中枠を消費しない |
| ledger-transition | はい | 成功 | `%TEMP%`隔離台帳コピー | 観測→候補→試行→採用→廃止と3つの却下分岐を照合 | 理由、根拠、反映結果、人の判断待ちを保持する | terminal output: `ledger-transition=success` | — |
| promotion-gate | はい | 成功 | `%TEMP%`隔離台帳コピー | 回数3・回数未満高影響ケースと採用資料を照合 | 試行なしの採用不可、期限試行は全必須資料つき | terminal output: `promotion-gate=success` | 採用承認・効果は演習データであり実績ではない |
| trial-expiry | はい | 成功 | `%TEMP%`隔離台帳コピー | 期限超過・無回答・巻戻し競合を照合 | 自動採用せず、事前の終了処理、競合時の停止を確認する | terminal output: `trial-expiry=success` | 定時起動を仮定していない |
| safety-and-authority | はい | 成功 | `%TEMP%`隔離ケース | 安全欠陥と権限拡大要求を架空入力で照合 | 既存権限内の封じ込めと、権限拡大/必須検証緩和の禁止を区別する | terminal output: `safety-and-authority=success` | 実環境設定は変更していない |
| references-and-scope | はい | 成功 | `cfdbffe1...` + 作業ツリー | Markdown相対リンク、入口→config→手順→台帳、core scope、古い未設置文言を静的確認 | 85リンク到達、core scope成功、stale文言なし | terminal output: `markdown-links=85`; `markdown-links=success`; `core-scope=success`; `stale-retro-wording=success` | 初回確認で古い分岐1件を検出し修正後に再実行 |
| project-required | はい | 成功 | `cfdbffe1...` + T-0006作業ツリー（T-0007追加前） / `.venv` | `.venv/Scripts/python.exe tests/run_all.py` | 既存テスト155件、終了コード0、失敗0、エラー0 | terminal output: `Ran 155 tests`; `OK`; `実行 155 件 / 失敗 0 件 / エラー 0 件 / スキップ 0 件`; `exit=0` | 通常権限の初回起動は実行不能。許可された同一コマンドの昇格再試行で成功し、両方を履歴保持。T-0007の未コミットコード/test変更が後から混在したため、現在の混在ツリー全体の結果へ拡張しない |
| change-declaration-t006-scope | はい | 成功 | `cfdbffe1...`からT-0006のみの作業ツリー（T-0007追加前） | `.venv/Scripts/python.exe harness/project/check_changes.py --base cfdbffe1a01e99432aa9d527c12192fb5a9e3669` | T-0006保護対象変更の宣言漏れなし | terminal output: `result=ok (declaration presence is not human approval or semantic review)`; `exit=0` | その後に並行T-0007の保護対象変更が追加されたため、現在の混在ツリーへ成功を拡張しない |
| change-declaration-mixed-worktree | はい | 失敗 | `cfdbffe1...`から現在の混在作業ツリー | 同じ`check_changes.py --base` | 全変更の宣言漏れなし | terminal output: `result=invalid`; undeclared `okf.yml`, `tests/helpers.py`, `tests/test_index.py`, `tests/test_render.py` | T-0007並行変更が原因。T-0006の成果物不足とは扱わず、head固定検査へ分離する |
| change-declaration-head | はい | 未実行 | T-0006成果物commitの`cfdbffe1...<T-0006_COMMIT>` | `.venv/Scripts/python.exe harness/project/check_changes.py --base cfdbffe1a01e99432aa9d527c12192fb5a9e3669 --head <T-0006_COMMIT>` | T-0006差分の宣言漏れなし | — | T-0006成果物commit後に実行 |
| code-review-spec | はい | 成功 | `cfdbffe1...`からT-0006対象（未コミット/未追跡を含む。T-0007パスを除外） | 並列review agentによるsource T-0006 / `HARNESS_SPEC.md` §7仕様軸review | 初回指摘（AI出力、重要度、並行変更の帰属）を修正後、要件不足・scope creep・誤実装の残存指摘なし | review agent `01a0743d-aa10-7a80-8290-241ad1fd9a04` の再review: previous findings fixed / remaining completion evidence only | 成果物commitとhead固定宣言検査を完了境界で追加確認する |
| code-review-standards | はい | 成功 | `cfdbffe1...`からT-0006対象（未コミット/未追跡を含む。T-0007パスを除外） | 並列review agentによるAGENTS/config/requirements/docs規約の標準軸review | documented-standard violationなし。入口ごとのretro要約重複は低確信のbaseline smellとして残し、中央手順への参照で許容 | review agent `01a0743d-ab4e-7700-b13d-cfddc6497cef` の再review: no remaining documented violations | T-0007の並行変更と共有configのObsidian hunksはT-0006対象から除外 |
| ci-test | はい | 未実行 | GitHub Actions | workflow `test` | Windows/Ubuntu × Python 3.11/3.13 | — | 実CIは実行しない。ローカルから推定しない |
| ci-smoke | はい | 未実行 | GitHub Actions | workflow `smoke` | Ubuntu/Python 3.11 smoke | — | 実CIは実行しない。ローカルから推定しない |

### 演習の入出力要約

製品は `Codex`、モデルは `GPT-5（正確なdeployment名は実行環境に未露出）`。対象版は `cfdbffe1a01e99432aa9d527c12192fb5a9e3669 + working-tree`、演習は `%TEMP%` に作った台帳・手順の隔離コピーとインメモリ状態で行い、終了後にコピーを削除した。以下の `AI出力` はこのセッションが手順を入力へ適用して生成した判定であり、期待結果との照合結果も併記する。演習の入力・出力は本番台帳へ保存していない。

1. `retro-trigger-positive` — 入力: T-0004作業記録の検査プローブ再試行。AI出力: 「検証プローブの期待条件不一致は§7.1のトリガー。未処理事象だけfull retroへ進み、`IMP-0001`を観測・回数1で登録する。採用・効果は未確定。」期待: 摩擦と根拠から台帳へ到達し、回数を捏造しない。照合: 一致。
2. `retro-trigger-negative` — 入力: 摩擦のない小さな文言修正。AI出力: 「トリガーなし。非該当理由をworklogへ残し、通常報告で終了。retro文書・台帳行は追加しない。」期待: 追加retroなし。照合: 一致。
3. `retro-dialogue-boundary` — 入力: 選択肢決定、説明要求、通常の要望追加、予定分担、意図したred、要件欠落、回答済み質問の反復、引継ぎ欠落。AI出力: 「前5件は非該当、後3件は依頼・現物との不適合/反復/情報欠落として該当。」期待: 5対3の境界。照合: 一致。
4. `retro-evidence-gap` — 入力: 差分とreview記録が欠けた作業。AI出力: 「取得可能な記録を確認し、残りは確認不能。摩擦なしともretro実施済みとも断定せず、差分/reviewを再取得する次の一手を残す。」期待: 根拠不足を隠さない。照合: 一致。
5. `ledger-dedup` — 入力: 同じ事象の再読、独立した同症状、別症状、終了項目の再発。AI出力: 「再読は加算せず、独立発生は既存IDへ加算、別症状は別ID、終了項目の再発は元IDの履歴へ追記。」期待: IDと履歴を保持。照合: 一致。
6. `ledger-capacity` — 入力: 評価中10件、試行3件、採用済み2件、新規観測。AI出力: 「採用済みは枠外。新規は重複統合または根拠つき却下として履歴化し、4件目の試行は開始しない。」期待: 黙って捨てず、上限を越えない。照合: 一致。
7. `ledger-transition` — 入力: 観測→候補→試行→採用→廃止と、3状態からの却下。AI出力: 「各遷移に理由・根拠・反映結果を残す。採用/廃止は必要な人の判断なしに確定しない。」期待: 全分岐と判断待ち。照合: 一致。
8. `promotion-gate` — 入力: 累計3回だが試行なし、回数未満だが高影響・比較可能。AI出力: 「前者は採用不可。後者は具体的差分、変更前後、期待効果、比較、期限、巻戻し条件つきの期限試行候補にする。」期待: 回数だけで採用しない。照合: 一致。
9. `trial-expiry` — 入力: 期限超過、回答なし、他変更と巻戻し競合。AI出力: 「自動採用しない。事前の終了処理を行い、競合時は停止して判断を求める。定時起動は仮定しない。」期待: 期限・無回答・競合の安全な扱い。照合: 一致。
10. `safety-and-authority` — 入力: 安全上の欠陥と、改善名目の権限拡大/必須検証緩和。AI出力: 「安全欠陥は既存権限内で停止・封じ込めを優先する。権限拡大・外部送信・必須検証緩和は実行しない。」期待: 安全例外と権限境界の分離。照合: 一致。
11. `references-and-scope` — 入力: targetの入口、config、手順、台帳とcore文書。AI出力: 「85相対リンクが到達、core手順にプロジェクト固有コマンドなし、古いretro未設置文言を1件検出して修正後に再確認、専用自動化なし。」期待: 到達性・scope・状態文言が成立。照合: 一致。

### 再試行履歴

- `references-and-scope` — 2026-09-06: 失敗（古い「retro未設置」分岐を検出） → 成功（`verify-report.md`を現行手順参照へ修正し、85リンク・scope・stale文言を再確認）。
- `project-required` — 2026-09-06: 実行不能（通常権限で`.venv\Scripts\python.exe`を起動できない） → 成功（許可された同一コマンドの昇格再試行、155件成功）。初回の実行不能を消していない。
- 過去のT-0004/T-0005の再試行は本worklogの検証結果へ転記せず、`IMP-0001`の根拠参照として扱う。

## review

### 仕様軸

- 比較点: `cfdbffe1a01e99432aa9d527c12192fb5a9e3669`
- 対象: 今回のtracked差分、未追跡の新規文書、本worklog、source T-0006、`HARNESS_SPEC.md` §7。T-0007の並行パスと共有configのObsidian/OKF hunksは対象外として帰属を分けた。
- 結果: 成功。初回reviewの「演習のAI出力/モデル情報不足」「重要度の未明示」「並行変更の帰属」指摘を修正し、再reviewで残存する仕様指摘なし。成果物commitとhead固定宣言検査は完了境界で確認する。

### 標準軸

- 比較点: `cfdbffe1a01e99432aa9d527c12192fb5a9e3669`
- 標準: target `AGENTS.md`、`docs/AGENTS.md`、`docs/CONVENTIONS.md`、`harness/core/guide.md`、`harness/project/config.md`、`harness/core/policy/requirements.md`、既存手順・worklog・変更検査契約
- 結果: 成功。演習データと台帳の分離、worklogのretro状態値、共有configのT-0007 hunks帰属、宣言境界を確認した。documented-standard violationなし。入口ごとの短いretro要約の重複は低確信のbaseline smellとして記録し、別の正本を作らない参照接続として許容した。

## 残作業・妨げ・再開前提

### 残作業

- 仕様軸・標準軸reviewの結果を反映し、指摘があれば修正後に影響検証を再実行する。
- 成果物コミット後、source T-0006の検証表、evidence、完了条件、state/done_at、結果を更新する。

### 妨げ

- なし。対象リポジトリの開始時差分はclean。

### 再開前提

- target repositoryのブランチと開始SHAを現物照合する。
- `requirements.md` → `config.md` → 本worklog → `retrospective.md` / `ledger.md` の順で読み、過去T-0004/T-0005の成功を本タスクへ転記しない。
- 実CI、採用承認、改善効果、製品間比較は未実行なら未実行として残す。
- T-0007の並行変更をステージせず、共有 `config.md` のT-0006 hunksだけを成果物commitへ含める。

## 次の一手

レビュー結果を反映して対象版を再確認し、必要な修正がなければT-0006の成果物パスだけをコミットしてからsource T-0006の検証表・evidence・完了状態を更新する。並行T-0007変更はステージしない。

## 完了 / 中断要約

進行中。retro手順、台帳、既存フロー接続、実観測 `IMP-0001`〜`IMP-0003` を設置した。隔離11演習、参照/scope確認、既存テスト、T-0006範囲の変更宣言検査は成功。仕様/標準reviewの指摘修正、T-0006成果物commit、設計側T-0006完了更新は残作業であり、CI test/smokeは未実行として扱う。並行T-0007変更は保持してT-0006の対象外とする。
