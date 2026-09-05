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
