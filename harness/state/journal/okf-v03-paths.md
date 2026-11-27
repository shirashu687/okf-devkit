# OKF v0.3 のリンク解決と脚注

- 開始点はバンドル対応ブランチの `a975dc9519c0000da8e20a184a61fbe28a49647e`。worktree `/tmp/okf-v03-paths`、`codex/okf-v03-paths`。作業開始時の差分はなし。
- [#90](https://github.com/shirashu687/okf-devkit/issues/90) の §4.2・§6・§12.1 に対応する。既存の HTML リンク・バックリンクにパスフィールドを接続し、GFM 脚注は Markdown-it の既存プラグインを使う。
- 仕様軸では、両形式、0.2 と未宣言のパスフィールドだけの再試行、将来版の比較、境界外とリンク切れ、後継の循環を確認した。標準軸では既存の描画・出力先の検査と、固定依存の manifest を使った。
- 対象操作は差分の commit、ブランチの push、PR 作成。両 CLI の新規 fixture と既存の変更宣言を確認した。
