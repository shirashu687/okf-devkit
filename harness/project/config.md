# okf-devkit のプロジェクト設定

作業場所・検証コマンド・既存文書への対応を確認するときに読む。共通の用途案内は [ガイド](../core/guide.md)、守る制約は [制約表](../core/policy/requirements.md) にある。

## 文書の役割対応

| 役割・読む条件 | 実配置・状態 |
| --- | --- |
| 作業開始時の入口 | [AGENTS.md](../../AGENTS.md) が指示の正本。[CLAUDE.md](../../CLAUDE.md) は同じ入口への接続 |
| 作業に合うスキルを選ぶ | [日本語ガイド](../core/guide.md) |
| 変更・検証・記録・外部操作の前 | [必須制約と現状の限界](../core/policy/requirements.md) |
| 上流スキルの導入・更新・撤去 | [採用プロファイル](skill-profile.md)。導入状態は [skills-lock.json](../../skills-lock.json)、通知は [THIRD_PARTY_NOTICES.md](../../THIRD_PARTY_NOTICES.md) |
| 検証の選択・結果・完了報告 | [verify-report.md](../core/procedures/verify-report.md)。結果は成功 / 失敗 / 未実行 / 実行不能の4値 |
| 中断・別セッションからの再開 | [handover.md](../core/procedures/handover.md)。状態の正本は同じworklog |
| retroゲート・改善候補・台帳更新 | [retrospective.md](../core/procedures/retrospective.md) と [ledger.md](../ledger.md)。トリガーがある回だけfull retroを行う |
| 通常・大の作業記録 | [worklog.md](../core/templates/worklog.md) を `harness/state/journal/<task-id-or-slug>.md` に複製。小作業は省略可、中断時は必須 |
| 保護対象・上流管理ファイルの変更検査 | [check_changes.py](check_changes.py)。開始SHAから作業ツリーまたはbase/headの2コミットを検査 |
| 正当な変更の機械可読な宣言 | `harness/state/journal/<task-id-or-slug>.changes.json`。目的・確認の正本は対応するworklog |
| 課題の作成・更新 | [課題管理規約](../../docs/agents/issue-tracker.md) と [backlog索引](../../docs/backlog/index.md) |
| 受付課題の分類 | [triageラベル](../../docs/agents/triage-labels.md) |
| ドメイン語・設計判断 | [配置規約](../../docs/agents/domain.md)、[CONTEXT.md](../../CONTEXT.md)、[Decision Record索引](../../docs/project/decisions/index.md)。ADR本文は必要になったときに作る |
| OKF文書の編集 | [docs入口](../../docs/AGENTS.md) と [執筆規約](../../docs/CONVENTIONS.md) |
| CLIの機能・利用方法 | [README.md](../../README.md) |

## 検証の実行場所とコマンド

作業ディレクトリはリポジトリルート。Pythonは既存の `.venv` を使う。下表はWindowsの実配置で、Python要件・依存は [pyproject.toml](../../pyproject.toml) に従う。仮想環境が起動できない場合は環境の制約を記録し、別Pythonで成功したことに置き換えない。

| 検証・実行条件 | コマンド・参照 |
| --- | --- |
| 変更後の必須既存テスト | `.venv/Scripts/python.exe tests/run_all.py` |
| OKF文書更新後の索引生成 | `.venv/Scripts/python.exe -m okf_devkit.cli index --write` |
| OKF文書更新後の規約検査 | `.venv/Scripts/python.exe -m okf_devkit.cli lint` |
| OKF文書更新後の索引確認 | `.venv/Scripts/python.exe -m okf_devkit.cli index --check` |
| コード変更時の影響文書確認 | `.venv/Scripts/python.exe -m okf_devkit.cli affected --base <固定した比較点>`。結果の扱いはdocs入口に従う |
| CIのテスト | [ci.yml](../../.github/workflows/ci.yml) の `test`。Windows/UbuntuとPython 3.11/3.13で `python tests/run_all.py` |
| CIの独立smoke | 同じworkflowの `smoke`。Ubuntu/Python 3.11で一時リポジトリのinit・index・lint・render・logとhook応答を検証 |

## 変更検査と宣言

対象ルートで次を実行する。`--base` は必須で、Gitコミットへ解決できる比較点を渡す。省略形のrefを渡しても検査は完全SHAを出力するが、宣言の `base` はその完全SHAと一致させる。

```text
.venv/Scripts/python.exe harness/project/check_changes.py --base <BASE_SHA>
.venv/Scripts/python.exe harness/project/check_changes.py --base <BASE_SHA> --head <HEAD_SHA>
```

`--head` なしは staged / unstaged / 未追跡の非ignore対象を含む現在の作業ツリー、`--head` ありは指定した2コミット間だけを検査する。CIでは必ずPRイベントの `github.event.pull_request.base.sha` と `github.event.pull_request.head.sha` を環境変数経由で渡す。シェル文へGitHub式や外部文字列を直接展開せず、両SHAが解決できない場合・全ゼロの場合・履歴がshallowの場合・競合中の場合は成功へ置き換えない。

初期の分類対象は検査スクリプトが正とし、次の一覧はレビュー用の対応表である。

| 分類 | 対象 |
| --- | --- |
| 保護対象 | `AGENTS.md`、`CLAUDE.md`、`harness/core/policy/**`、`harness/core/procedures/verify-report.md`、`harness/project/config.md`、`harness/project/check_changes.py`、`.github/workflows/**`、`tests/**`、`pyproject.toml`、`okf.yml`、`.claude/settings*.json`、`.codex/**` |
| 上流管理 | `.agents/skills/**`、`.claude/skills/**`、`skills-lock.json`、`THIRD_PARTY_NOTICES.md`、`harness/project/skill-profile.md` |

変更が保護対象または上流管理に該当する場合、同じ比較差分内で追加・変更した `harness/state/journal/<task-id-or-slug>.changes.json` に対象パスを列挙する。宣言は次の条件を満たす必要がある。

- `version: 1`、比較元の完全SHA、実在するリポジトリ相対Markdown worklog、空でない `changes` を持つ。
- `path` は実際の差分にある保護対象または上流管理ファイルだけを、glob・絶対パス・`..`なしで列挙する。renameは旧名と新名の両方を列挙する。
- 宣言ファイル自体が比較差分内で追加・変更された場合だけ読み取る。比較元に残っている古い宣言を、新しい変更の許可へ再利用しない。
- 終了コードは `0`（宣言漏れなし）、`1`（未宣言または不正な宣言）、`2`（比較不能）である。出力はパス・分類・宣言状態・診断だけで、変更ファイルの本文を含めない。

宣言は利用者の許可の証明ではない。review担当は、依頼、開始SHAからの正確なdiff、理由、検証結果を照合し、検査・CI・制約の同時変更による迂回可能性も記録する。上流変更がある場合は出所・対象・理由を `skill-profile.md` の更新手順と照合する。

テスト、OKF検査、CI smokeは別の結果として扱う。ローカルテスト成功からCI smoke成功を推定しない。単独の型検査やPython lintコマンドは既存の必須コマンドとして定義されていない。上表の `lint` はOKF文書の検査を指す。

既存テストは作業区分にかかわらず必須であり、終了コード0、失敗0、エラー0を期待する。実行不能なら代替確認と限界を4値で記録し、成功へ読み替えない。OKF文書を変更した場合は、索引生成が終了コード0で最新状態になり、lintがerror 0 / warn 0、索引確認が終了コード0であることを期待する。CI testはworkflowの全matrix、CI smokeは独立smokeの全手順が成功することを期待し、ローカル結果から推定しない。

## 作業記録と引継ぎ

`harness/state/journal/` は進行中または引継ぎ対象のworklog置き場である。ファイル名は課題IDがあればそのID、なければ短いslugを使い、同じ作業について1枚だけ作る。テンプレートは共通項目だけを持ち、プロジェクト固有のコマンドや完了条件は作業ごとに記入する。作業開始・再開時は [retrospective.md](../core/procedures/retrospective.md) に従って `harness/ledger.md` の試行期限・採用済みの見直し日を確認し、完了・中断時は同じworklogへretroゲートの確認範囲、根拠、処理済みID、未確認範囲、次の一手を残す。

## Retroと改善台帳

full retrospectiveの実行条件、トリガーなし・根拠不足・トリガーありの分岐、重複・上限・試行・採用・却下・廃止の記録方法は [retrospective.md](../core/procedures/retrospective.md) を正本とする。改善観測の正本は [harness/ledger.md](../ledger.md) であり、演習データや会話全文を台帳へ移さない。

- 開始・再開時に、評価中10件・試行3件の上限、期限超過、採用済みの見直し日、巻戻し競合を確認する。
- トリガーなしの回は通常の完了・中断報告で終了し、新しいretro文書や空の台帳行を作らない。
- トリガーありの回は未処理の事象だけfull retroへ送り、台帳IDをworklogから参照する。人の採用承認なしに恒久ルールへ反映しない。
- 定時起動、専用の意味検知、台帳validatorは設置していない。無稼働中の期限処理や、AIの検知の完全性を保証しない。

通常・大の作業では作業開始時にworklogを作り、作業場所、ブランチ、開始SHA、開始時から存在する変更、今回の変更を区別して記録する。中断する場合は小作業でも作成し、最新のHEAD・作業ツリー・検証結果・妨げ・前提・具体的な次の一手を更新する。完了後の保管は仕様の記録寿命に従い、ここでは自動移動しない。

## 上流スキルとの接続

- 上流 `implement` は実装の流れを提供する。このガイドの区分、ローカル制約、必須検証、worklog、利用者の権限を優先する。
- 上流 `code-review` を使う場合は、開始時に解決した比較点を渡す。上流手順がコミット済み差分だけを対象にする場合、`git diff <開始SHA>` と未追跡の対象ファイルを自前で確認し、作業ツリー全体を仕様軸・標準軸の両方でreviewする。
- 上流 `handoff` を明示的に使う場合、その一時文書はworklogへの参照と次セッションの用途だけを持つ。状態の正本を一時文書へ移さず、毎回のhandoff実行を必須にしない。
- [harness/core/procedures/retrospective.md](../core/procedures/retrospective.md) にfull retrospective（retro）のトリガー、台帳更新、期限確認、試行・採否の手順を置く。実行条件に該当しない回は通常報告で終え、根拠不足や実行不能はその範囲と次の一手を記録する。

## OKFと製品の接続

- [okf.yml](../../okf.yml) の `bundle_root` は `docs`。`harness/` とルート入口はバンドル外の通常Markdownで、OKF index・lint・staleの検査対象には含まれない。これらの参照と内容は変更時に別途確認する。
- `harness/` から既存文書へは通常の相対Markdownリンクで到達する。`docs/` の本文をコピーしたり、コアの利用にOKF CLIを必須としたりしない。バンドル内のリンク・frontmatter・生成indexは執筆規約に従う。
- 上流スキルのコピーは `.agents/skills/` と `.claude/skills/`。ガイドは共通内容への参照として前者をリンクする。製品ごとの実効導入元と更新方式は採用プロファイルに従う。
- [Claudeプロジェクト設定](../../.claude/settings.json) は上流プラグインの重複利用を抑える設定であり、外部送信やファイル改変を強制的に止める設定ではない。
- 検証報告・引継ぎ・full retrospective（retro）の自前手順は設置済みで、上記の役割対応表から参照する。ガイドにある上流スキルの利用案内と、自前のretro手順・改善台帳を混同しない。

## 外部設定・権限の観測と再確認

GitHub設定や製品権限はこのタスクで変更しない。T-0005の詳細化時点（2026-09-06）の読み取り観測は、従来型のmain branch protectionが未設定、activeなdefault ruleset `21655324` が存在し、creation / update / deletion / non-fast-forwardとCopilot reviewを対象にし、bypass actorは空、required status checksは未設定、である。これは当時の観測であり、現在の強制や将来のマージ拒否を保証しない。ユーザー全体の実効権限は未確認である。

再確認は設定変更を伴わない読み取りだけで行い、時刻・対象SHA・取得手段・結果をworklogへ記録する。GitHub CLIが認証済みの場合は、リモートから得た `OWNER/REPO` に対して次のAPIを照会し、応答本文やトークンをworklogへ転記しない。利用できない場合はGitHubのRepository settingsで同じ項目を目視確認し、未確認と記録する。

```text
gh api repos/OWNER/REPO/branches/main/protection
gh api repos/OWNER/REPO/rulesets
```

確認するのはrulesetの状態、対象、bypass actor、required status checks、branch protectionの存在だけである。設定を追加・更新してCI失敗をマージ拒否へ変える作業、製品権限の付与、外部送信の許可は本タスクの範囲外である。CIの検知とマージ拒否を同一視しない。
