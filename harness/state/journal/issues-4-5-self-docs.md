# 作業記録: Issues 4 / 5 self docs

## メタデータ

- 課題: #4 / #5。状態: 進行中。
- ブランチ: codex/self-docs-ci。開始 SHA: 9d72e0e5798883d81789582d8879f139865d37b5
- 作業場所: 独立 worktree okf-docs-ci。開始時変更なし。
- 作業者: Codex / GPT-6。

## 目的・範囲と判断

Issue #4 の4本文と #5 の self-check CI を追加する。既存 npm 未統合ブランチは読取のみで、そこにある配布・案内変更を取り込まない。merge/release とグローバル hook の変更は対象外。

コードを確認した結果 render --check は HTML 差分チェックではなくメモリ内生成検査。CI はクリーン checkout で直接実行でき、生成 HTML の Git 除外を維持する。stale は参考出力、lint は通常モードを採用する。

## 検証

| 検査 | 結果 | 証拠・対象 |
|---|---|---|
| index --write / --check | 成功 | 3目次更新、全目次最新 |
| lint | 成功 | error 0 / warn 0 |
| render --check | 成功 | 23ページ、書込0、削除0、warn0 |
| affected --paths cli.py ci.yml | 成功 | architecture/commands/scaffold reference の対応を表示 |
| tests/run_all.py | 成功 | 169件、失敗0、エラー0、スキップ0 |
| 二軸独立 review | 未実行 | 親へ依頼済み |
| task 宣言検査 | 成功 | workflow変更を宣言済み |
| PR 宣言検査 | 未実行 | commit後検査 |
| 最新 SHA CI | 未実行 | Draft PR作成後確認 |

既存指定 venv の Python を読取利用し、PYTHONPATH=worktree/src で対象実装を特定する。

## 摩擦観測と retro ゲート

開始時に手順と ledger を確認。評価中5 / 試行0 / 採用0、期限未定。CIと仕様・差分・検証・reviewを最後に照合する。通常のドキュメント追加と事実確認はトリガーなし。最終reviewとCIは未確認、次の一手は確認結果の追記。

## 次の一手

必須テストと二軸review完了後、宣言検査を通し Draft PR と最新 SHA CI を確認する。Issueはmerge前にはcloseしない。

## 再試行履歴

- ログ追記後の lint: warn1（sharedログ日付順）を検出し、最新日付を先頭へ移動して再検査する。初回の本文 lint warn0とは別対象版。
