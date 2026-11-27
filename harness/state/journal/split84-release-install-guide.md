# 公開済み tgz の導入手順を整える

- 対象は PR #84 の差分のうち #75、#82。比較元は `7d5b1d8cd015f3b823ce19526dfb23a82e0ce34b`。
- 分割元の HEAD は `dd7f1945039adf6381d5f678acecd67b681851db`。作業ブランチは `codex/split84-release-install-guide`。
- 開始時の元作業ツリーには以前の未追跡トリアージ記録があったため、分割には専用 worktree を使用した。

## 検証とレビュー

- ローカル Python 既存テストは成功。実行 273 件 / 失敗 0 件 / エラー 0 件 / スキップ 5 件
- index の生成・確認、strict lint、render check、affected、空白検査を実行した。
- 分割元の仕様・標準レビューを参照し、変更箇所とテストをこの比較元から照合した。公開前のため GitHub CI は未実行。
