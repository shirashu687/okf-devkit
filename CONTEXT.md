# okf-devkit のコンテキスト

## プロジェクト

okf-devkit は、ソースコードと OKF v0.2 ドキュメントの対応を保つ Python CLI である。実装は src/okf_devkit/、標準テストは tests/、利用者向け説明は README.md にある。

## 正本と用語

- Markdown と Git の履歴がドキュメントの正本である。
- docs/ は OKF バンドルで、docs/CONVENTIONS.md が frontmatter、リンク、backlog の書式を定める。
- docs/backlog/ の state は課題の進捗であり、tags の triage ラベルとは別である。
- 上流スキルは .agents/skills/ と .claude/skills/ にインストーラーがコピーした直接依存で、自前実装とは別に更新する。

## ドメイン文書の配置

このリポジトリは single-context で扱う。新たな用語や後戻りしにくい判断は、既存の CONTEXT.md を更新するか、必要になった時点で docs/project/decisions/ に Decision Record を追加する。空の用語集や ADR は先に作らない。

## ハーネスの作業契約

- `harness/core/procedures/verify-report.md` は、対象版を固定して必須検証を `成功` / `失敗` / `未実行` / `実行不能` の4値で記録し、仕様軸と標準軸のreviewを分ける共通手順である。
- `harness/core/templates/worklog.md` は、通常・大の作業と中断時に使う状態記録のテンプレートである。実際の状態正本はconfigで定めたjournal内のworklogで、配置、コマンド、制約は `harness/project/config.md` が定める。
- `harness/core/procedures/handover.md` は、入口・config/制約・worklog・参照先の順に現物を照合して再開する手順である。上流handoffの一時文書はworklogの代替にしない。
- `harness/core/procedures/retrospective.md` は、作業開始・再開時の期限確認と、完了・中断時のretroゲートから `harness/ledger.md` の観測・候補・試行・採否・撤去記録へ接続する。トリガーのない回は通常報告で終了し、専用自動検知や定時起動があるとは扱わない。
