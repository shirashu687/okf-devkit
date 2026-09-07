# 作業記録: T-0008-pilot-two-products

## メタデータ

| 項目 | 値 |
| --- | --- |
| 課題ID / 作業名 | `T-0008-pilot-two-products` |
| 状態 | `部分完了`（Codex分とHTML生成は完了。ブラウザ表示はURLポリシーで実行不能。Claude Codeは保留） |
| 作業場所 | `C:/Users/rinta/Documents/1_projects/okf-devkit`（評価記録の正本） |
| ブランチ | `codex/t0003-japanese-entry` |
| 開始日時 / 最終更新日時 | `2026-09-06 Asia/Tokyo` / `2026-09-06 Asia/Tokyo` |
| 開始SHA | `1a646369621dcdf7c918c04493963784ff95a5cb` |
| 最新HEAD | `1a646369621dcdf7c918c04493963784ff95a5cb` |
| 作業者 / 製品 / モデル | `Codex coordinator` / `Codex` / `GPT-5（この実行環境ではdeployment名非公開）` |
| 証拠の保存先 | 本worklog、隔離試行ディレクトリ、サブエージェントのtask結果要約、最終HTML（秘密情報・会話全文・巨大ログは保存しない） |

## 目的・範囲

### 目的

`T-0008` のCodex/luna実施分として、根拠のある代表作業をC1/C2/C3と基準比較B1で実行し、同じ完了契約・検証・reviewを照合したうえで、実施範囲と限界を自己完結HTMLへまとめる。

### 対象

- 本リポジトリの `HARNESS_SPEC.md` と設計側backlogのT-0008。
- 実作業repo `okf-devkit` の入口、制約、既存テスト、CLI・renderer・docs接続。
- C1/C2/B1の分離実装、C3前半・後半の分離文脈再開、独立確認、評価worklog、HTMLレポート。

### 対象外

- Claude Codeの復旧・認証変更・契約変更。
- 本流への実装統合、改善策の恒久採用、上流更新、権限変更、専用評価CLI、後続タスク詳細化・配布。
- 架空の不具合・不要な機能の作成、実行不能・未実行・不適合の成功扱い。

### 完了条件

- 設計側 `docs/backlog/T-0008-pilot-two-products.md` の実施範囲・B1/C3・HTML要件。
- `HARNESS_SPEC.md` §3（⑮〜⑰）、§4、§8.1、§8.3、§10.1。
- 実作業repo `harness/project/config.md`、`harness/core/procedures/verify-report.md`、`handover.md`、`retrospective.md` の契約。

## 開始時の状態

開始SHAだけでは対象版を特定できない。開始時点の現物を確認し、既存変更と今回の評価記録・隔離成果物を分ける。

### 開始時から存在する変更

- `okf-devkit`: 変更なし。`git status --short --branch` は `## codex/t0003-japanese-entry`、HEADは `1a646369621dcdf7c918c04493963784ff95a5cb`。
- `harness` 設計repo: 利用者由来の `HARNESS_SPEC.md`、T-0007、T-0008、backlog index の未コミット差分を確認。これらは保持し、本作業の設計repo更新には使わない。
- 確認方法: 対象repoごとの `git rev-parse HEAD`、`git status --short --branch`、`git diff --stat`、未追跡一覧。

### 今回の変更

- 本worklogと最終HTMLを `okf-devkit/harness/state/journal/` に追加する。
- 実装・テスト・review用の成果物は対象SHAから分離された隔離場所へ保持し、本流へ統合しない。

## 判断と根拠

| 判断 | 根拠 | 影響 |
| --- | --- | --- |
| C1/C2/C3/B1は候補を一括詳細化せず、各着手直前に一件だけ固定する | source T-0008「一件ずつ選ぶための記録と選定条件」 | worklogへ選定理由・対象外・完了条件を順次追記する |
| 実装担当は新規文脈の `gpt-5.6-luna` とし、確認担当は別task・別モデルで分離する | source T-0008「人の関与を最小にする実行体制」「B1の比較条件」 | 実モデル・task ID・隔離場所を試行ごとに記録し、独立デスクトップ実績とは表現しない |
| A/Bは実装前に同じ開始SHA・同じ依頼・同じ検証・同じreview条件を固定し、Bから外す接続差分だけを保存する | source T-0008「B1の比較条件」 | 結果を見て条件を緩めず、条件不一致は比較不能とする |
| C3後半には前半の会話を渡さず、worklogと現物を照合してから次の一手を実行する | source T-0008「C3の中断・再開」、`harness/core/procedures/handover.md` | 同一セッション継続や引継ぎ文だけを成功としない |
| `okf-devkit` の既存 `.venv` を使い、起動不能と許可された再試行を別結果として記録する | target `harness/project/config.md` / `requirements.md`、既存 `IMP-0003` | 実行不能を成功に読み替えず、環境差を既存台帳と照合する |
| Claude Codeは利用不能のまま保留し、Codex分の結果とT-0008全体完了を分ける | source T-0008の利用者合意と完了条件 | source backlogを完了扱いにしない |

## 候補・比較条件・実行体制

### C1（着手直前に固定）

| 項目 | 固定内容 |
| --- | --- |
| 作業名 / 区分 | `sync --gate` のclean worktree早期終了を修正する小さな不具合修正 |
| 対象版 | `1a646369621dcdf7c918c04493963784ff95a5cb`。実装担当の隔離worktreeはこのSHAから開始する |
| 実在根拠 | READMEの `sync --gate` 説明は残存lint errorをstderrへ出してexit 2とする。`harness/core/policy/requirements.md` と `HARNESS_SPEC.md` §4.2 / §8.1 は失敗を成功へ読み替えない。現行 `cmd_sync` は `--gate` かつclean時に検証せず0を返す |
| 再現入力 / 実際 | cleanな一時Git repoに、index整合済みだが語彙外 `type: Nope` の文書をcommitし、`okf lint` は非0、`okf sync --gate --session-id c1-repro` は0になった（2026-09-06、対象venv、出力要約と一時fixtureは廃棄済み） |
| 変更する振る舞い | `sync --gate` のclean worktreeでも、gateが対象とする文書検証を実行し、lint errorがあればexit 2（同一error集合の既存2回目契約は維持）にする |
| 対象外 | `sync` の通常モード、gateの回数・TTL、lint rule自体、CI、権限、外部送信、他のsync失敗処理 |
| 変更予定領域 | `src/okf_devkit/cli.py` と対応する `tests/test_gate.py`（必要最小限のREADME/文書更新は実装担当の根拠判断で許可するが、保護対象変更は宣言とreviewを要する） |
| 小とした理由 | 原因と期待結果が単一関数の早期returnに局所化し、公開CLIの既存契約を保つ回帰テストを1件追加できる。可逆で、データ形式・権限・外部状態を変えない |
| 完了条件 | (1) cleanな既存error repoでgateが検証を省略しない、(2) lint errorは初回exit 2、既存の同一error集合2回目exit 0を維持、(3) cleanな正常repoは0、(4) 対応テストと必須全件テスト成功、(5) 開始SHAから仕様軸/標準軸reviewで残存指摘なし |
| 検証方法 | `tests/test_gate.py` の回帰テスト、`.venv/Scripts/python.exe tests/run_all.py`、開始SHAから `harness/project/check_changes.py --base <SHA>`、実差分の仕様/標準review |
| 見送った有力候補 | `sync` がlog書込みエラーを握る問題は再現したが、C1のgate早期returnとは別の通常/中断作業として後続C3候補に保留。`affected` JSON化は必要性の根拠を追加照合してからC2候補にする |

#### C1の実施・独立確認・集計

| 項目 | 記録 |
| --- | --- |
| 実装担当 | `gpt-5.6-luna`、Codex appの新規projectless task `01a0755c-7db5-7c23-a375-bd6194a8a676`。開始・終了SHAはともに `1a646369621dcdf7c918c04493963784ff95a5cb`、隔離場所は `C:/@git_repogitories/ab0f/t0008-runs/c1-luna`、未コミット差分のまま本流へ統合していない |
| 実装結果 | `src/okf_devkit/cli.py` のclean時早期returnを除去し、`tests/test_gate.py` にvalid clean / committed errorの回帰を追加。focused 16件、必須全件164件はいずれも失敗0・エラー0。 |
| 独立確認担当 | `gpt-5.6-sol`、別の新規projectless task `01a0755f-bbb0-71d2-99df-269605a54a5d`。実装担当の会話・他試行・本worklogを渡さず、同じ隔離コピーを別taskから確認した。独立確認中に利用上限で最終応答は返らなかったが、実物には確認担当が行った修正と検証記録が残る |
| 独立確認で見つかった事項 | 初回テストfixtureが生成config未追跡のためclean状態を直接証明していなかったこと、protectedな `tests/test_gate.py` の変更宣言が無かったこと、削除後の `gate_state_dir` コメントが古かったことを検出 |
| 独立確認での修正 | valid/error fixtureをcommitしてclean状態を固定、旧早期returnを一時復元するprobeで回帰検出力を確認、コメントを更新し、`sync-gate-clean-validation-review.md` と同名 `.changes.json` を追加。probeの一時変更は除去済み |
| coordinatorによる引継ぎ検証 | 同じC1隔離コピーで `tests/run_all.py`、`check_changes.py --base 1a646...`、`affected --base 1a646...`、`git diff --check` を再実行。全件テストは成功（164件）、変更検査は `result=ok`、affectedも終了0。CI test/smokeは未実行 |
| C1判定 | 成功（実装・局所回帰・必須ローカル検証・保護対象申告・仕様/標準reviewの指摘修正を確認）。独立taskの利用上限による最終報告欠落は限界として残し、独立taskが返した最終報告とは表現しない |

### C2（着手直前に固定）

| 項目 | 固定内容 |
| --- | --- |
| 作業名 / 区分 | `affected --format json` を追加する通常規模の機能追加。C2-Aと比較対象B1で同じ実装を試す |
| 対象版 | `1a646369621dcdf7c918c04493963784ff95a5cb`。A/Bとも同じSHAから別cloneを作る |
| 実在根拠 | `AGENTS.md` / `docs/AGENTS.md` / `docs/CONVENTIONS.md` はコード変更後に `okf affected --base <固定点>` を実行し、その出力を次の文書更新へ接続する。現行 `compute_affected()` は既にmappingとuncoveredを構造化して返すが、`cmd_affected()` はtext行だけを出力する。一方 `status` と `stale` は既に `--format json` を提供しており、同じ自動化導線に機械可読な選択肢がないことを確認した |
| 着手前の現行実測 | 対象venvで `okf affected --paths src/okf_devkit/cli.py` を実行すると、mappingが無い場合も「更新すべきドキュメントは見つかりませんでした」「未カバー」の人間向け行だけを返し、JSONではない（終了0）。内部のmapping/uncoveredをJSONで取得するCLI契約は未存在 |
| 追加する振る舞い | `affected --format text|json` を提供する。既定textは現行出力を維持し、jsonは少なくとも `mapping` と `uncovered` を安定したJSONオブジェクトで返す。`--paths` / `--base`、layer skip、終了コード0の既存契約を変えない |
| 対象外 | 文書の内容・索引・lint規則・mappingアルゴリズム、JSON schemaの外部標準化、CI/権限/外部送信、本流統合・恒久採用 |
| 変更予定領域 | `src/okf_devkit/cli.py`、対応する `tests/test_git.py` または専用CLIテスト、利用者向けREADME/入口記述。保護対象のテスト変更は変更宣言とreviewを必須にする |
| 通常とした理由 | 既存の内部データを外部へ明示する公開CLI契約の追加で、text後方互換・引数解析・JSON構造・既存回帰・文書接続を確認する複数工程がある。不要な新規解析や別データ源は作らない |
| 完了条件 | (1) text既存出力が維持される、(2) JSONがmapping/uncoveredを機械可読で返す、(3) no pathsを含む境界と `--base` / `--paths` を回帰検証する、(4) 必須全件テスト・必要な文書検査・変更検査が成功、(5) 仕様軸/標準軸reviewで残存指摘なし |
| 見送る条件 | 実在根拠が不足、A/B接続差分が同一条件を保てない、必須検証が実行不能、または実装が既存text契約を壊す場合は未実行/実行不能/不適合として成功扱いしない |

#### C2-A / B1の比較条件（実装前に固定）

| 条件 | C2-A（自前接続あり） | B1（接続切断） |
| --- | --- | --- |
| 実装担当 | 新規文脈の `gpt-5.6-luna` | 新規文脈の `gpt-5.6-luna` |
| 製品・開始点 | `okf-devkit`、同じ `1a646...`、別isolated clone | 同じ |
| 共有する依頼 | C2の作業名、現行コードを尊重する範囲、対象外、完了条件、必須テスト、固定SHA、protected変更申告、review要求 | 同じ文面・同じ要求 |
| Aだけに接続するもの | target入口からconfig/policy/guide/procedure/worklog/retroの読む順、`harness/state/journal`への記録形式、実行前後の状態照合の案内 | なし。Bはtarget `AGENTS.md`・必要な上流/プロジェクト制約・コードとテストだけから自分で作業経路を組み立てる |
| Bから除くもの | — | A固有の作業手順、worklog/retroの作成案内、Aの結果・会話・解答・評価結果 |
| 検証・review | 同じコマンド契約、同じ開始SHA比較、同じ独立確認条件 | 同じ |
| 判定 | 条件差分以外の差が確認できれば比較可能。差が混入した場合はB1を不適合/比較不能として扱う | 同じ |

接続切断差分の実体は、A/Bへ渡す依頼ファイルを `C:/@git_repogitories/ab0f/t0008-runs/c2-conditions/` に保存し、実装前の独立確認担当へだけ提示する。A/B実装担当には相手側の依頼・結果・会話を提示しない。依頼本文と差分は、後から結果に合わせて変更しない。

#### C2実装前の独立確認

| 項目 | 記録 |
| --- | --- |
| 確認担当 | `gpt-5.6-sol`、新規projectless task `01a07574-38f2-7911-9a33-b343a420960d` |
| 対象 | A/B clone、条件固定ファイル、A/B依頼、target入口・関連コード・テスト・README・docs |
| 結果 | 成功。両cloneはclean、同じtree `61e3a08d86b896159713793886255d4fcb6cc2d2`、HEAD/branch条件一致。関連ファイルのSHA-256一致、依頼の `## 依頼` と `## 完了条件` は同一。候補は現行の `compute_affected()` / `cmd_affected()` / `status` / `stale` と入口文書に根拠があり、不要な架空機能ではないと確認 |
| 接続差分の確認 | Aのみが入口→policy/guide/config/procedure→worklog/変更宣言/retroと検証順を明示。Bはその接続を除き、現行repoから自分で経路を定める。同一の製品要件・完了契約・モデル・SHA・検証期待以外の意図しない差分なし |
| 実装前判定 | 安全にA/B実装を開始できる。確認担当はcloneを変更せず、merge/pushもしていない |

#### C2-A / B1の実装・独立review・比較

| 項目 | C2-A | B1 |
| --- | --- | --- |
| 実装task / model | `01a07579-14f8-7ed1-82fd-06a4416b3260` / `gpt-5.6-luna` | `01a07579-2d45-7703-aae6-c71acbbb1d24` / `gpt-5.6-luna` |
| clone / branch | `C:/@git_repogitories/ab0f/t0008-runs/c2-a-luna` / `codex/t0008-c2` | `C:/@git_repogitories/ab0f/t0008-runs/b1-luna` / `codex/t0008-b1` |
| 開始・終了SHA | `1a646...` → `1a646...`、未コミット | `1a646...` → `1a646...`、未コミット |
| 実装 | `cli.py` にparserとJSON出力、`test_affected.py` 5件、README、worklog/宣言を追加。text既定経路と解析源は維持 | 同じ機能を実装。`test_affected.py` 6件、README、worklog/宣言を追加。B自身がrepoからworklog/retro経路を選択し、隔離ledgerにも観測を記録 |
| 実装担当の検証 | cloneの指定venvは実行不能。fallback Python 3.14.3でfocused 5件、全168件、parser、fixed-base affected、change-check、diff checkが成功。初回fallback全suiteはfixture 2件失敗後、担当自身が修正して再実行成功 | cloneの指定venv/PATH Pythonは実行不能。初回focused 6件中2件、full 169件中2件がGit fixture初期化漏れで失敗。製品コードの問題とは未断定のまま独立reviewへ引き渡し |
| 独立review task / model | `01a07588-a884-7671-aba7-3980b0431a00` / `gpt-5.6-sol` がA/B両方を現物review | 同じ。実装担当の会話を使わず、固定SHA・差分・worklog・実行結果を現物から確認 |
| review修正 | 追加修正なし。最終focused 5/5、full 168/168 | `setup_bundle()` に `self.git_init()` を追加する最小修正。初回2件失敗をworklogに保持し、修正後focused 6/6、full 169/169 |
| 最終検証 | shared project venv（Python 3.14.3、clone `src`をPYTHONPATH）でfixed-base JSON、layer skip、既定textと`--format text`の同値、JSON反復安定性、change-check、diff checkが成功。clone-local venvとCI matrixは未実行 | 同じ最終結果。coordinatorの一度の追加probeはvenvパス入力を誤記したが、直後に正しいパスで再実行して成功。誤記結果は成功証拠に数えていない |
| A/B比較結果 | 明示されたroute/worklog接続があり、初回fixture問題を実装担当が自己修正。worklog/宣言は対象差分内 | route接続を自力で組み立て、worklog/宣言と隔離ledger観測を作成。初回fixture問題を独立reviewで検出・修正。ledger差分は隔離成果物であり、本流採用・恒久ルール化ではない |
| 判定 | 成功 | 成功（独立review修正後）。初回失敗・実行不能を成功へ読み替えていない |

独立reviewの実モデルは `gpt-5.6-sol` として記録する。実装担当はA/Bとも `gpt-5.6-luna` であり、reviewerやcoordinatorの実行をlunaの実績に混ぜない。A/Bの差分比較は、同一の要件・開始SHA・モデル・検証契約と、Aにだけ明示した接続差分を前提にし、実装結果・テスト数・修正量の違いは観測結果として扱う。

開始時点ではC3の詳細を固定しない。C1の独立確認と成果物状態を照合した後、C2を一件だけ具体化し、実装前の独立確認を終えた。

### C3（着手直前に固定）

| 項目 | 固定内容 |
| --- | --- |
| 作業名 / 区分 | 通常 `sync` が `cmd_log` の書込みエラーをstderrへ「スキップ」と表示しながら終了0で握る問題の修正。C3前半で赤い回帰テストとhandoff状態を作り、C3後半でfresh contextから再開する |
| 対象版 | `1a646369621dcdf7c918c04493963784ff95a5cb`。front cloneはこのSHAから開始し、backend cloneはfrontの中断commitだけを起点にする |
| 実在根拠 | 現行 `cmd_sync` は `cmd_log` の `OkfError` をcatchして警告を出すが、通常syncの戻り値計算へlog失敗を反映しない。`harness/core/policy/requirements.md`、`HARNESS_SPEC.md` §4.2 / §8.1、CLIの運用契約は検証不能な失敗を成功へ読み替えない |
| 再現入力 / 実際 | 開始前に一時Git repoで `log.baseline` 未設定かつ既存 `docs/log.md` にhashless legacy entryを置き、通常 `sync` を実行した。logは `[okf log] スキップしました` とエラーを出したが、`sync_rc=0` になった（dirty worktreeの警告も出力）。一時fixtureは廃棄済みで、出力要約を本worklogに保持する |
| 変更する振る舞い | 通常 `sync` でlog書込みが失敗した場合は非0（通常CLIの運用エラーとして1）を返し、stderrの診断を維持する。index/lint/staleの既存処理、`sync --gate` のC1契約、log自体のbaseline規則は必要以上に変更しない |
| 対象外 | logのbaseline設計・legacy移行、lint rule、gate回数/TTL、CI、権限、外部送信、本流統合・恒久採用 |
| 変更予定領域 | `src/okf_devkit/cli.py` と対応する既存test（必要最小限）。protectedなtests変更は中断時点・完了時点とも変更宣言を要する |
| 完了条件 | (1) 再現入力の通常syncが非0、(2) logの診断が残る、(3) log成功かつ他工程成功の通常syncは0、(4)既存gate/同期テストと必須全件テスト成功、(5)開始SHAから仕様軸/標準軸reviewで残存指摘なし、(6)前半の赤い状態と後半の再開証拠を別taskで確認 |
| 中断条件 | front担当はproduction fixを入れず、focused regressionが失敗する状態、最新HEAD、working tree、変更宣言、worklog、具体的な次の一手を残して隔離branchへcommitする。backend担当はfrontの会話を受け取らず、worklogと現物だけで再開する |

#### C3実行・再開条件

| 工程 | 固定内容 |
| --- | --- |
| front | 新規 `gpt-5.6-luna` task。`codex/t0008-c3-front` cloneで再現・赤テスト・handoff worklogのみを作り、production fixなしでcommitして停止する |
| backend | front commitから別clone/branchを作り、新規 `gpt-5.6-luna` taskを起動。渡すのはclone path、固定SHA、front worklog pathだけ。front taskの会話・解答・評価結果は渡さない |
| 独立確認 | backend完了後に別新規 `gpt-5.6-sol` taskでfront/backendの実物、差分、再開証拠、仕様/標準、検証をreviewし、必要ならclone内で最小修正する |
| 判定 | frontの赤状態は中断として成功扱いしない。backendの修正・検証・reviewが揃った場合だけC3を成功、実行不能/未実行/不適合はその値で記録する |

実行方式: 現在の進行管理taskが正本worklogを更新し、Codex appの新規taskを隔離worktreeで起動する。実装担当は `gpt-5.6-luna`、独立確認担当は実モデルを結果から取得して明記する。サブエージェントの新規文脈は独立デスクトップセッションの実績とは数えない。B1とC3後半へ相手の解答・会話・評価結果を渡さない。

#### C3 front中断・backend再開・独立review・集計

| 工程 | 実施内容と結果 |
| --- | --- |
| frontの起動 | 新規 `gpt-5.6-luna` task `01a0759a-10b2-7410-a153-d93db618cb2f` を `C:/@git_repogitories/ab0f/t0008-runs/c3-front-luna`、branch `codex/t0008-c3-front` で開始。開始SHAは `1a646369621dcdf7c918c04493963784ff95a5cb`。`tests/test_log.py` に保護回帰テスト、worklog、変更宣言だけを追加し、production fixは入れず `785a9d0dbe6bc687b2c7d7b711b2f3311b1c2998` へcommitした。 |
| frontの状態 | clone-local `.venv` とPythonがなく、front task自身のfocused testは `実行不能`。これは赤結果へ読み替えていない。coordinatorが許可された共有project venvへcloneの `src;tests` を `PYTHONPATH` として渡し、同じfocused testを実行したところ1件中1件失敗、終了1、戻り値 `0 == 0` となり、修正前の赤を現物確認した。 |
| backendの再開 | frontの会話・解答・評価結果を渡さず、worklogとhandoff現物だけを指定して、新規 `gpt-5.6-luna` task `01a075a4-fe8f-75e1-b999-8552de443867` を `C:/@git_repogitories/ab0f/t0008-runs/c3-back-luna`、branch `codex/t0008-c3-back` で開始。再開時handoff状態SHAは `8b58f08b76efcd1fba8572c04077838a546f6100`。focused redを再確認後、`cmd_sync` の通常分岐へ `log_rc=1` を加え、`tests/test_index.py` の成功log fixtureへ `git_init()` を追加した。gate分岐・log baseline・依存・CIは変更していない。 |
| backendの実装・検証 | 修正前focused失敗、修正後focused 1/1成功、`tests.test_log tests.test_gate` 30/30成功、full `tests/run_all.py` 164件・失敗0・error0・skip0、fixed-base change checker成功、affected成功、diff check成功。shared project venvはPython 3.14.3、clone-local venvは実行不能、CI test/smokeは未実行。実装commitは `cfd8bfeea91be95c88400301604dc902c21abdae`。 |
| 独立確認 | 新規 `gpt-5.6-sol` task `01a075af-a436-7c03-bab0-4a30c13d27a5` がfront/backendの差分、固定SHA、fresh再開、仕様軸/標準軸、検証結果を現物から確認。backend worklogがfrontの履歴とbackend現行状態を曖昧に混在させ、handoff状態SHAを誤っていた点をdocs-onlyで修正し、production/test/declarationの意味は変更していない。最終HEADは `db45a55bbe33be0c6fdefbf036681c1f939a7747`、最終worktreeはclean。 |
| C3判定 | 成功。frontの中断・clone-local実行不能・修正前失敗はそれぞれその値で保持し、成功と数えていない。backendのfresh再開、production修正、回帰/全件/変更検査、独立reviewまで確認できたため、C3としてのみ成功と判定する。本流へのmerge/push・恒久採用は行っていない。 |

C3のbackend修正は対象版からの隔離成果物であり、target `codex/t0003-japanese-entry` のHEADには統合していない。C3後半は前半taskの会話を参照せず、指定されたworklogとhandoff現物から再開した。サブエージェントの実行は独立デスクトップセッションの実績ではない。

## 摩擦観測とretroゲート

開始時に `harness/ledger.md` の評価中3/10、試行中0/3、採用済み0、期限・見直し未定を確認した。既存 `IMP-0001`〜`IMP-0003` は本作業へ自動適用せず、同じ症状を実際に観測した場合だけ根拠を照合する。現時点の新規観測は、指定 `.venv` の通常権限起動が実行不能だったこと（既存 `IMP-0003` と同一適用範囲の可能性があるため重複登録しない）である。

| 項目 | 記録 |
| --- | --- |
| 確認範囲 | source依頼、HARNESS_SPEC関連節、両repo入口・規約・config・policy、target HEAD/diff、既存worklog/台帳、C1/C2/B1/C3の実差分・独立指摘・再検証、HTML生成と静的自己完結性を確認済み。ブラウザ表示はURLポリシーで実行不能 |
| 該当条件と根拠または非該当理由 | C1では完了前reviewがclean fixture不足とprotected変更申告漏れを検出した。C2ではA/Bの新規Git fixtureで初回focused/full失敗が発生し、独立reviewがBの修正を行った。C3ではfrontのclone-local実行不能、handoff後の修正前赤、backend worklogの状態混在が観測され、前二者は結果を保持し、後者は独立reviewでdocs-only修正した。独立確認taskの利用上限によるC1最終応答欠落は製品不具合ではなく、評価実行の限界として記録する |
| 短い観測メモ | `.venv\Scripts\python.exe` の通常権限起動は実行不能。隔離cloneにもvenvが無かったため、許可された対象限定のproject venv＋clone `PYTHONPATH` で再検証した。C1/C2/C3とも実装担当と独立確認担当のtaskを分離できたが、これは独立デスクトップセッションの実績ではない |
| 処理済み事象・台帳ID | 既存 `IMP-0003` を照合。C1のfixture不足・申告漏れ、C2 B1のfixture不備、C3 backend worklogの状態混在は各試行内で処理済み。C2 B1のfixture不備は隔離ledgerの `IMP-0004` 観測として記録されたが、対象repo本流のledgerへは反映せず、恒久ルール・採用・権限変更を行っていない |
| 未確認範囲と次の一手 | ブラウザ表示のみ実行不能。Codex内ブラウザで `file:///C:/Users/rinta/Documents/1_projects/okf-devkit/harness/state/journal/T-0008-pilot-two-products.html` を開こうとしたがURLポリシーに拒否された。回避経路は使わず、HTMLを部分結果として提出する |
| full retrospective | 実施済み。反復した摩擦は試行内で修正・記録し、既存 `IMP-0003` と隔離 `IMP-0004` を照合した。新規の恒久改善策・台帳採用・権限変更は行わず、残る限界（clone-local venv、CI、Claude Code）は評価記録へ明記する |
| 人の判断待ち | なし。権限・認証など自動で解消できない必須操作が出た場合だけ依存部分を分離して記録する |

## 検証

開始時のベースライン。実装後の試行別検証は、各試行の対象版・終了状態・証拠を追記する。結果は `成功` / `失敗` / `未実行` / `実行不能` の4値だけを使う。

| 識別子 | 適用 | 結果 | 対象版・範囲 | コマンド / 確認方法 | 期待条件 | 証拠 | 理由・限界 / 再試行 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| baseline-tests | はい | 実行不能 | target `1a646369…`、clean worktree | `.venv/Scripts/python.exe tests/run_all.py` | 既存テストが終了0、失敗0、エラー0 | 通常権限でプロセス起動不能（出力は要約のみ） | 既存 `IMP-0003` と照合し、対象限定の許可された同一コマンドで再試行する。成功へ読み替えない |
| baseline-cli | はい | 実行不能 | target `1a646369…` | `.venv/Scripts/python.exe -m okf_devkit.cli --help` | CLIが起動しhelpを表示 | 同じ実行前提で起動不能 | 実装作業開始前に許可された再試行または隔離環境の実在venvで確認する |
| baseline-ci-test | はい | 未実行 | GitHub Actions | CI workflow `test` | matrix全件成功 | — | 外部CI実行は範囲外。ローカル成功から推定しない |
| baseline-ci-smoke | はい | 未実行 | GitHub Actions | CI workflow `smoke` | 独立smoke全件成功 | — | 外部CI実行は範囲外。ローカル成功から推定しない |

### 再試行履歴

- `baseline-tests` / `baseline-cli` — 開始時の `実行不能`（通常権限の既存venv起動拒否）を最終値として保持する。後続のC1/C2/B1/C3でshared project venvを使った隔離cloneの検証は、baselineを成功へ上書きしない。

### 試行別検証集計

| 試行 / 識別子 | 結果 | 実行方式・証拠 | 限界 |
| --- | --- | --- | --- |
| C1 / gate focused | 成功 | `gpt-5.6-luna`実装＋`gpt-5.6-sol`独立review。最終focused 16件、旧guard復元probeでerror初回2/再実行0、valid clean成功 | 独立review taskは利用上限で最終応答を返せず、確認担当の修正ファイルとcoordinator再検証で補完。CI未実行 |
| C1 / required full | 成功 | `tests/run_all.py` 最終164件、失敗0・error0。`check_changes --base 1a646...` exit0、`affected --base 1a646...` exit0、diff check成功 | clone-local指定venvではなく許可されたproject venvで実行 |
| C2-A / focused/full | 成功 | `gpt-5.6-luna`。fallback Python 3.14.3でfocused 5/5、full 168/168。初回fixture 2件失敗を実装担当が修正後に再実行 | 指定venvとCI 3.11/3.13 matrixは未実行 |
| B1 / focused/full | 成功 | `gpt-5.6-luna`。初回focused 2/6失敗・full 2/169失敗を保持。`gpt-5.6-sol`独立reviewがGit初期化を修正後、focused 6/6、full 169/169 | 初回失敗を成功と数えず、clone-local指定venvは実行不能。隔離ledgerのIMP-0004は観測のみ |
| C2-A/B1 / CLI・比較 | 成功 | 両cloneでfixed-base JSON exit0、layer skip空object、既定textと`--format text`同値、JSON反復安定性、parser、change declaration、diff check成功。要件・SHA・モデル・接続差分は実装前独立確認済み | coordinatorの一度のvenvパス誤記probeは失敗証拠にせず、正しいパスで再実行した結果だけを採用 |
| C3 / front focused | 失敗 | `gpt-5.6-luna` frontはclone-local環境では実行不能だったため赤を主張せず、coordinatorがhandoff現物をshared project venvで実行して1/1失敗、終了1を確認。production未変更の赤状態 | front task自身のclone-local実行不能と、coordinatorによるhandoff後の実測を別結果として保持 |
| C3 / backend focused・relevant | 成功 | fresh backendで修正前focused 1/1失敗、修正後focused 1/1成功、`tests.test_log tests.test_gate` 30/30成功。skip診断と非0、成功経路0を確認 | shared project venv Python 3.14.3。clone-local venvは実行不能 |
| C3 / backend required full | 成功 | `tests/run_all.py` 164件、失敗0・error0・skip0、終了0。fixed-base change checker再試行成功、affected exit0、diff check exit0 | CI matrixは未実行。初回full失敗と初回checker失敗はworklogへ保持し、修正後だけを最終成功値とした |
| C3 / independent review | 成功 | `gpt-5.6-sol` がfront/backendのfresh再開・差分・仕様/標準・証拠を確認し、backend worklogのSHA/履歴混在だけをdocs-only修正。最終HEAD `db45a55…`、worktree clean | review修正後のproduction/test/declaration意味は不変 |
| final HTML / static self-contained check | 成功 | 指定worklogを正本としてHTMLを生成。CSSはinline、外部CDN・外部scriptなし、タイトル・主要見出し・結論・限界を含むことを静的確認 | ブラウザでの視覚確認は別行の実行不能 |
| final HTML / browser display | 実行不能 | Codex内ブラウザでローカル `file:///` URLを表示しようとしたが、browser URL policyにより拒否された | policy回避のローカルHTTP、別ブラウザ、raw CDP等は行っていない。HTMLは部分結果として提出 |
| C1/C2/B1/C3 / CI | 未実行 | GitHub Actions test/smoke | ローカル成功から推定しない |

## review

試行ごとに開始SHAを固定比較点として仕様軸・標準軸reviewを実施する。未コミット・未追跡の対象変更を除外せず、実装担当と独立確認担当のtaskを分ける。

### 仕様軸

- 比較点: `1a646369621dcdf7c918c04493963784ff95a5cb`（試行ごとに分離worktreeの開始SHAを追記）
- 対象: C1/C2/B1/C3の採用依頼、完了条件、実差分、検証、C3引継ぎ状態
- 結果: C1/C2/B1/C3を実施済み。C1のclean fixture・保護対象申告漏れ、C2 B1のGit fixture初期化漏れ、C3 backend worklogのhandoff状態混在を独立reviewで検出し、対象clone内で必要な修正後に再検証した。C3 frontの中断・実行不能・修正前失敗は成功と数えていない。残存リスクは指定venv/CI matrix未実行、Claude Code未実行。

### 標準軸

- 比較点: 同上。target `AGENTS.md`、`docs/AGENTS.md`、`docs/CONVENTIONS.md`、config、policy、procedures、既存テストを基準にする。
- 結果: C1/C2/B1/C3は開始SHAからの全tracked/untracked差分、入口規約、保護対象宣言、text/JSON/終了コード契約、worklog、fresh再開状態、reviewを照合済み。C2 B1の隔離ledger観測は恒久採用へ接続していない。最終HTMLのブラウザ表示はURLポリシーにより実行不能。

## 残作業・妨げ・再開前提

### 残作業

- なし（HTMLは生成済み。ブラウザ表示確認はURLポリシーにより実行不能として確定記録し、回避作業は行わない）。

### 妨げ

- 通常権限では指定venvが起動不能。実装・検証を止めず、許可された対象限定の再試行が必要な検証だけ分離する。
- Claude Codeは利用不能。復旧作業は行わない。

### 再開前提

- `requirements.md` → `config.md` → 本worklog → 必要な手順・対象差分の順に読み、HEAD・branch・作業ツリーを現物照合する。
- 各隔離worktreeの開始SHA・実モデル・実行ID・残差分を記録し、相手側の解答や会話を別担当へ渡さない。
- 本流統合、恒久採用、source backlogのdone更新は行わない。

## 次の一手

本worklogを正本として生成したHTMLを部分結果として提出する。ブラウザ表示はURLポリシーで実行不能のため追加の回避作業はせず、本流統合・恒久採用・Claude Code復旧も行わない。

## 完了 / 中断要約

部分完了。開始時の対象版・既存差分・入口・制約・既存台帳を照合し、C1/C2/B1/C3を隔離実装・独立review・修正・集計まで実施し、正本worklogから自己完結HTMLを生成した。ブラウザ表示はCodex内ブラウザのURLポリシーで実行不能だったため、回避せずそのまま記録した。Claude Codeは利用不能のため保留し、T-0008全体は未完了である。未実行・実行不能・不適合を成功としない。

## 2026-09-06 Codex側評価の追補

利用者からClaude Codeが利用不能のまま進められる範囲の作業を依頼された。既存成果の証拠固定と評価を行い、製品間の確認は未実施として残す。

### 証拠固定

以下は既存試行の内容を変えずにローカルコミットしたもの。本流への実装統合・pushは行っていない。各worklogの未コミットという記載は試行終了時の履歴であり、この追補が証拠固定後の所在を示す。

| 試行 | 隔離cloneの最終コミット |
| --- | --- |
| C1 | 64805ec1ebd2af5eb501e24a91db255beb9f9264 |
| C2-A | c6bbffb16ef04cda24161f8bff8344675adaebca |
| B1 | 7526448075f5f2a3991ce9b88586bed292d71342 |
| C3後半 | db45a55bbe33be0c6fdefbf036681c1f939a7747 |

A/Bの固定依頼3ファイルは同じjournalのT-0008-conditions/へ原本とバイト一致する形で保存する。集計worklogと既存HTMLも評価資料としてローカルコミットする。HTMLは元試行時点の説明資料で、この追補の評価を反映していない。

### 評価指標の集計と欠測

件数は既存の集計・試行worklogから識別できる事象の下限。記録がないものを0件と断定せず、独立確認AIの修正と人の修正を分ける。

| 指標 | C1 | C2-A | B1 | C3 |
| --- | --- | --- | --- | --- |
| 最終ローカル全件検証（既存記録） | 164件成功 | 168件成功 | 169件成功 | 後半164件成功 |
| 独立確認で修正した事象 | 3件: clean fixture不足、保護対象宣言漏れ、古いコメント | 追加修正なしとの記録 | 1件: Git fixture初期化漏れ | 1件: handoff SHAと履歴の混在 |
| 実装中のテスト手戻り | 未集計 | fixture不備で2テスト失敗、自己修正 | fixture不備で2テスト失敗、独立確認で修正 | 初回fullとchecker失敗、修正後成功。意図した赤は手戻りに数えない |
| 人の修正回数・時間 | 記録から確定不能 | 同左 | 同左 | 同左 |
| 探索・質問の反復回数 | 記録から確定不能 | 同左 | 経路を自力構成したが回数不明 | 会話を渡さず再開したが反復回数不明 |
| 検証の誤報・漏れ | clean状態を直接証明しないfixtureを1件検出 | fixture由来の2テスト失敗は製品不具合と区別 | 同左 | 環境実行不能と修正前失敗を区別。誤報の総数は不明 |
| スキル未発動・誤発動・重複の各件数 | 専用の起動記録がなく確定不能 | 同左 | 同左 | 同左 |
| 所要・トークン | 比較可能な計測なし | 同左 | 同左 | 同左 |

文脈負担の事後計測: 保存した依頼全文はAが1,728文字/33行、Bが1,293文字/31行（PowerShellの文字列Length、改行で分割した行数）。差は435文字であり、パスや対象外記述も含むため手順案内だけの負担やトークン差ではない。双方のAGENTSは同じハーネスへ接続したままで、Bもworklog/retroへ到達している。スキル一覧省略警告の有無、実際の総読込量、不要読込量は保存記録から確定できない。

### A/Bの再評価

以前の「比較可能」は依頼要件・開始SHA・モデルを揃えた限定比較として保持する。ただし、ハーネス全体の有無による効果検証には使わない。

- Bから外したものは依頼文の明示案内であり、repo内のハーネスと入口接続自体は同じまま残っている。
- Aの実装担当にはfallback Pythonが使え、Bの実装担当にはPATH上のPythonが無いとの記録がある。最終reviewは共有venvだが、自己修正とreview修正の違いには利用可能ツールの差が混入している。
- 各条件1回で、反復回数・時間・読込量の比較可能な値も不足している。

結論: この一組を根拠に「品質を落とさず手戻りまたは探索負担が改善した」とする判断は不採用。最終ローカルテストと独立確認の結果は品質の限定的証拠として残すが、SPECの受け入れ⑯は未実証である。ハーネス自体を撤去・不採用にする判断ではない。⑰はClaude Code待ち。

### 第0.4版への改訂候補（未採用）

1. 比較の開始SHA・モデル・依頼だけでなく、実装担当の実行可能なPython・検証コマンドも開始前に照合する。今回の環境差の影響を次回試行で切り分ける候補。
2. 明示案内の有無とハーネス部品の有無を別の比較として設計し、何を外したかを入口の実差分で固定する候補。
3. 起動事象・探索反復・人の修正は試行中に短い件数記録を残す候補。今回の欠測を後から0で埋めない。独立確認AIの手戻りと人の手戻りを別に数える。
4. handoff時点のSHAと再開後HEADを分けて照合する記入例の候補。既存契約で足りるかを先に確認し、新たな必須項目を即時追加しない。

いずれも次の試行で評価する候補であり、今回だけで共通規定や台帳の恒久採用へ昇格させない。採用する共通規定を書く場合はHARNESS_SPEC.mdを正本とする。

### 追補後の検証

- 成功: 既存project venvで tests/run_all.py を実行。163件、失敗0、error0、skip0、終了0。対象は本流の評価資料追記であり、隔離cloneの実装テストを再実行した結果ではない。
- 成功: A/B条件3ファイルの原本と保存先のSHA-256一致。
- 未実行: Claude Code、CI matrix、部品なし比較の再試行。
