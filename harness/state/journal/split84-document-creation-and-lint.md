# 文書作成と雛形の検査を改善する

- 対象は PR #84 の差分のうち #68、#69、#70、#71、#72。比較元は `d945fc60fd75b8bc71deb5ad79fd1b342799f90b`。
- 分割元の HEAD は `dd7f1945039adf6381d5f678acecd67b681851db`。作業ブランチは `codex/split84-document-creation-and-lint`。
- 開始時の元作業ツリーには以前の未追跡トリアージ記録があったため、分割には専用 worktree を使用した。

## 検証とレビュー

- ローカル Python 既存テストは成功。実行 273 件 / 失敗 0 件 / エラー 0 件 / スキップ 5 件
- `npm ci --ignore-scripts`、Node 単独と Node / Python 互換テストは成功。Node 32 件、互換 18 件。
- index の生成・確認、strict lint、render check、affected、空白検査を実行した。
- 分割元の仕様・標準レビューを参照し、変更箇所とテストをこの比較元から照合した。公開前のため GitHub CI は未実行。

## 独立レビューと修正

- 仕様では、Markdown のインライン記法を含む配布雛形の記入例を検出し、コード内と YAML コメントにある同じ文字列を除外した。既存バンドルへの Project Overview 雛形の配置先も明記した。
- リポジトリ規約では半角カナ題名の助言とパッケージスクリプト経由の値欠落を両 CLI で揃えた。Python では索引の文字コード異常も Markdown 作成後の復旧案内を通るようにした。
