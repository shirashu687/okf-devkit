# okf-devkit エージェント入口

このリポジトリは okf-devkit の Python パッケージと、コードに追随する OKF ドキュメントを管理する。ここをプロジェクト指示の正本とし、Claude Code からも同じ内容を読む。

## 作業範囲

- 課題は docs/backlog/T-NNNN-<kebab>.md で管理する。作成・更新の規約は docs/agents/issue-tracker.md と docs/CONVENTIONS.md を読む。
- triage のカテゴリと状態ラベルは docs/agents/triage-labels.md に従う。GitHub Issues、PR、.scratch/ は使わない。
- ドメイン文書は single-context とし、CONTEXT.md と docs/project/decisions/ を読む。配置規約は docs/agents/domain.md にある。
- 上流スキルの採用名・参照閉包・更新方法は harness/project/skill-profile.md、導入状態は skills-lock.json を正本とする。

## Agent skills

### Issue tracker

ローカルの docs/backlog/ を課題管理先として使う。詳細は docs/agents/issue-tracker.md。

### Triage labels

tags にカテゴリ1つと状態ラベル1つを記録する。詳細は docs/agents/triage-labels.md。

### Domain docs

single-context の CONTEXT.md と docs/project/decisions/ を使う。詳細は docs/agents/domain.md。

## 必須確認

- Python は既存の .venv を使い、テストは .venv/Scripts/python.exe tests/run_all.py で実行する。
- OKF の更新後は .venv/Scripts/python.exe -m okf_devkit.cli index --write、lint、index --check を実行する。
- 外部への投稿、認証情報の記録、許可のない commit・push は行わない。上流スキルを更新するときは skill-profile.md の手順と対象範囲を確認する。
