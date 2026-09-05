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
| 通常・大の作業記録 | [worklog.md](../core/templates/worklog.md) を `harness/state/journal/<task-id-or-slug>.md` に複製。小作業は省略可、中断時は必須 |
| 課題の作成・更新 | [課題管理規約](../../docs/agents/issue-tracker.md) と [backlog索引](../../docs/backlog/index.md) |
| 受付課題の分類 | [triageラベル](../../docs/agents/triage-labels.md) |
| ドメイン語・設計判断 | [配置規約](../../docs/agents/domain.md)、[CONTEXT.md](../../CONTEXT.md)、[Decision Record索引](../../docs/project/decisions/index.md)。ADR本文は必要になったときに作る |
| OKF文書の編集 | [docs入口](../../docs/AGENTS.md) と [執筆規約](../../docs/CONVENTIONS.md) |
| CLIの機能・利用方法 | [README.md](../../README.md) |

## 検証の実行場所とコマンド

作業ディレクトリはリポジトリルート。Pythonは既存の `.venv` を使う。下表はWindowsの実配置で、Python要件・依存は [pyproject.toml](../../pyproject.toml) に従う。仮想環境が起動できない場合は環境の制約を記録し、別Pythonで成功したことに置き換えない。

| 検証・実行条件 | コマンド・参照 |
| --- | --- |
| 変更後の既存テスト | `.venv/Scripts/python.exe tests/run_all.py` |
| OKF文書更新後の索引生成 | `.venv/Scripts/python.exe -m okf_devkit.cli index --write` |
| OKF文書更新後の規約検査 | `.venv/Scripts/python.exe -m okf_devkit.cli lint` |
| OKF文書更新後の索引確認 | `.venv/Scripts/python.exe -m okf_devkit.cli index --check` |
| コード変更時の影響文書確認 | `.venv/Scripts/python.exe -m okf_devkit.cli affected --base <固定した比較点>`。結果の扱いはdocs入口に従う |
| CIのテスト | [ci.yml](../../.github/workflows/ci.yml) の `test`。Windows/UbuntuとPython 3.11/3.13で `python tests/run_all.py` |
| CIの独立smoke | 同じworkflowの `smoke`。Ubuntu/Python 3.11で一時リポジトリのinit・index・lint・render・logとhook応答を検証 |

テスト、OKF検査、CI smokeは別の結果として扱う。ローカルテスト成功からCI smoke成功を推定しない。単独の型検査やPython lintコマンドは既存の必須コマンドとして定義されていない。上表の `lint` はOKF文書の検査を指す。

## 作業記録と引継ぎ

`harness/state/journal/` は進行中または引継ぎ対象のworklog置き場である。ファイル名は課題IDがあればそのID、なければ短いslugを使い、同じ作業について1枚だけ作る。テンプレートは共通項目だけを持ち、プロジェクト固有のコマンドや完了条件は作業ごとに記入する。

通常・大の作業では作業開始時にworklogを作り、作業場所、ブランチ、開始SHA、開始時から存在する変更、今回の変更を区別して記録する。中断する場合は小作業でも作成し、最新のHEAD・作業ツリー・検証結果・妨げ・前提・具体的な次の一手を更新する。完了後の保管は仕様の記録寿命に従い、ここでは自動移動しない。

## 上流スキルとの接続

- 上流 `implement` は実装の流れを提供する。このガイドの区分、ローカル制約、必須検証、worklog、利用者の権限を優先する。
- 上流 `code-review` を使う場合は、開始時に解決した比較点を渡す。上流手順がコミット済み差分だけを対象にする場合、`git diff <開始SHA>` と未追跡の対象ファイルを自前で確認し、作業ツリー全体を仕様軸・標準軸の両方でreviewする。
- 上流 `handoff` を明示的に使う場合、その一時文書はworklogへの参照と次セッションの用途だけを持つ。状態の正本を一時文書へ移さず、毎回のhandoff実行を必須にしない。
- `harness/core/procedures/retrospective.md` は未設置である。retroのトリガーがある場合は、仕様と制約を参照して未実施の理由、必要な次の一手、残存リスクを記録する。

## OKFと製品の接続

- [okf.yml](../../okf.yml) の `bundle_root` は `docs`。`harness/` とルート入口はバンドル外の通常Markdownで、OKF index・lint・staleの検査対象には含まれない。これらの参照と内容は変更時に別途確認する。
- `harness/` から既存文書へは通常の相対Markdownリンクで到達する。`docs/` の本文をコピーしたり、コアの利用にOKF CLIを必須としたりしない。バンドル内のリンク・frontmatter・生成indexは執筆規約に従う。
- 上流スキルのコピーは `.agents/skills/` と `.claude/skills/`。ガイドは共通内容への参照として前者をリンクする。製品ごとの実効導入元と更新方式は採用プロファイルに従う。
- [Claudeプロジェクト設定](../../.claude/settings.json) は上流プラグインの重複利用を抑える設定であり、外部送信やファイル改変を強制的に止める設定ではない。
- 検証報告・引継ぎの自前手順は設置済みで、上記の役割対応表から参照する。retroの詳細手順だけはまだ設置していない。ガイドにある上流スキルの利用案内と、未設置のretro手順を混同しない。
