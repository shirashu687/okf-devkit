# ready-for-agent 18件の実装

- 実装とローカル検証は完了。作業場所は `/workspace/okf-devkit`、ブランチは `codex/ready-agent-adjustments`。
- 比較点は GitHub `main` の `7d5b1d8cd015f3b823ce19526dfb23a82e0ce34b`。開始時の唯一の未追跡ファイルは前回の `issue-triage-61-83.md`。
- 対象は #63〜#77 と #80〜#82。各 Issue のトリアージコメントを受け入れ条件とし、別の設計判断が必要な Issue は範囲外とする。
- Node / Python のコマンド、共有 scaffold、配布手順を揃え、既存テストと両実装の比較で検証する。GitHub への操作は作業ブランチの公開と PR 作成。

## 作業範囲

- 初期化、雛形、文書作成と索引更新、引数解析を対象に互換性を確認する。
- 読み取り専用の導入診断と scaffold 差分確認を追加する。
- glob、下書きの検査、Git 履歴時の案内、公開済み配布物の手順を更新する。

## レビュー

- 仕様軸は GPT-6.2 Astra が比較点から初回コミット `9ecbada` までを確認した。不正設定時の診断継続、区切り以降の共通引数、層名と Git 履歴の案内、起動表記、開発版の HTTPS 取得経路を是正した。
- 標準軸は別レビューで ADR、文書規約、ハーネスと同じ差分を照合した。実際の CLI 入口、カスタムログ位置、Markdown のコード例判定、照合済み tgz を使う手順、対応実装への `code_globs` を修正した。
- `affected` の出力を照合し、利用時の操作・設定を説明する文書を更新した。コマンド本体や生成物の確認に関する既存の読取専用・保持契約は両 CLI の比較で検証した。

## 検証

対象は `9ecbada` にレビュー対応を含めた PR のコード・文書。Linux、既存の `.venv`、Node.js 24 を使用した。

| 項目 | 結果 | 証拠 |
| --- | --- | --- |
| Python 既存テスト | 成功 | `.venv/bin/python tests/run_all.py`。273件、失敗0、スキップ5 |
| Node 既存テスト | 成功 | `npm ci --ignore-scripts` 後の `npm test`。32件、失敗0、スキップ2 |
| Node / Python 互換テスト | 成功 | `OKF_TEST_PYTHON=$PWD/.venv/bin/python npm run test:compat`。18件 |
| Release ガードと梱包 | 成功 | `npm run test:release` 14件、`npm run test:package` 3件 |
| OKF と変更検査 | 成功 | index 生成・確認、strict lint エラー・警告0、render check 35ページ、affected、変更宣言、diff check |
| 公開済み配布物 | 成功 | tgz と manifest の SHA-256 を確認し、npm 11.9、pnpm 11.25、Yarn 1.22 と Yarn 4.9 で導入・再導入・init・index・lint を実行 |
| 開発版とスクリプト実行 | 成功 | SSH を無効にして HTTPS で固定 SHA を取得し、pack と npm 導入を確認。現在の CLI では npm / pnpm が渡す区切りと、生成された npm の案内からの index / lint を確認 |
| GitHub CI 初回 | 失敗 | Windows の Python 3.11 / 3.13 が Claude の PowerShell 版を Bash で起動する既存テストに失敗。Linux、文書、スモークは成功 |
| Windows 上の実エージェント終了イベント | 未実行 | 各製品の構成とスクリプトをレビューした。実イベントには対象製品と Windows 実機が必要 |

## 再試行と残存範囲

- 初回の生成文書 fixture が新しい L15 の指摘を受けた。記入済み文書を使う既存検査と、未記入を検出する新しい検査を確認した。本文の Markdown 判定を追加した後の Python 依存なしテストの失敗は、パーサを遅延ロードして互換性を回復した。
- Yarn 4 の最初の導入は通信設定で失敗した。一時環境で既存のプロキシを Yarn に伝え、固定 URL と照合済みローカル tgz の両方を確認した。
- Windows の hook テストを生成された shell に合わせた。Windows の PowerShell で3製品の成功、レンダラーの失敗、ラッパーの欠落を実行する検証へ更新した。
- `--version` は実行中の版を表示する。SHA / tgz の来歴の自動特定は後続の範囲。初期化の OS と hook 設定を共有する OS が異なる場合は製品のシェル指定を確認する。
- 検証失敗とレビュー指摘を開始版からの差分、各再試行、Issue の受け入れ条件に照合した。再発し得る依存なし実行の欠落は既存テストで検知できており、今回の修正で解消した。台帳に追加する共通ルールは設定していない。
