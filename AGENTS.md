# okf-devkit エージェント入口

このリポジトリは okf-devkit の Python パッケージと、コードに追随する OKF ドキュメントを管理する。ここをプロジェクト指示の正本とし、Claude Code からも同じ内容を読む。

## 作業の入口

- 変更・検証・記録・外部操作の前に [制約と現状の限界](harness/core/policy/requirements.md) を読む。利用者の依頼とプロジェクト制約を上流スキルの手順より優先する。
- 作業に合う進め方やスキルを選ぶときは [日本語ガイド](harness/core/guide.md) を読む。目的・変更箇所・期待結果が明確な小作業は、直接変更して必須検証と短い報告で終える。
- 作業対象の場所・検証コマンド・実行前提は [プロジェクト設定](harness/project/config.md) で確認する。Pythonは既存の `.venv` を使う。
- 上流スキルの導入・更新・撤去は [採用プロファイル](harness/project/skill-profile.md) に従う。導入状態は [skills-lock.json](skills-lock.json) を正本とする。

## Agent skills

### Issue tracker

新規課題は [GitHub Issues](https://github.com/shirashu687/okf-devkit/issues) で管理する。作成・更新前に [課題管理規約](docs/agents/issue-tracker.md) を読む。`docs/backlog/`、外部tracker、PR、`.scratch/` は受付・管理先にしない。

### Triage labels

課題の分類時は [triageラベル](docs/agents/triage-labels.md) を読み、Issue にカテゴリ1つと状態ラベル1つを付ける。

### Domain docs

ドメイン語・設計判断を扱うときは [CONTEXT.md](CONTEXT.md) と関連ADRを読む。single-contextの配置規約は [ドメイン文書案内](docs/agents/domain.md) にある。

## OKFの日常操作

コード変更後の文書更新、新規文書、読み取り点検、閲覧を選ぶときは [日常操作ガイド](docs/agents/operate-okf.md) を読む。これは開発者向けharnessや初回導入手順を置き換えず、詳細な引数・副作用の正本は [コマンド仕様](docs/cli/commands.md) とする。

## 文書と検証

- 変更後は、READMEの誤字修正など小さな文書変更も含め、[プロジェクト設定の既存テスト](harness/project/config.md#検証の実行場所とコマンド) を実行する。小作業の省略対象は計画・仕様化などの工程であり、この検証は省略しない。
- `docs/` の作業前に [docs入口](docs/AGENTS.md) を読む。OKF更新後はプロジェクト設定の索引生成・lint・索引確認も行う。
- `harness/` とルート入口・`CONTEXT.md` はOKFバンドル外の管理文書とする。docs入口の配置規則はOKF文書に適用し、これらを `docs/` に複製しない。検査範囲はプロジェクト設定の「OKFと製品の接続」で確認する。
