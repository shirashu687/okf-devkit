# ready-for-agent 18件の実装

- 状態は進行中。作業場所は `/workspace/okf-devkit`、ブランチは `codex/ready-agent-adjustments`。
- 比較点は GitHub `main` の `7d5b1d8cd015f3b823ce19526dfb23a82e0ce34b`。開始時の唯一の未追跡ファイルは前回の `issue-triage-61-83.md`。
- 対象は #63〜#77 と #80〜#82。各 Issue のトリアージコメントを受け入れ条件とし、別の設計判断が必要な Issue は範囲外とする。
- Node / Python のコマンド、共有 scaffold、配布手順を揃え、既存テストと両実装の比較で検証する。GitHub への操作は作業ブランチの公開と PR 作成。

## 作業範囲

- 初期化、雛形、文書作成と索引更新、引数解析を対象に互換性を確認する。
- 読み取り専用の導入診断と scaffold 差分確認を追加する。
- glob、下書きの検査、Git 履歴時の案内、公開済み配布物の手順を更新する。
