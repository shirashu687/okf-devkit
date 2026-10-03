# Issue #11 render --open

- 開始SHA: 9d72e0e5798883d81789582d8879f139865d37b5
- 作業場所: task/issue11、branch codex/issue11-render-open。開始時clean。
- 対象: Python/Nodeの明示的--open、check/hook抑止、README、影響文書、回帰検証。
- 対象外: serve新規CLIは検討項目で完了条件外。HTTP配信が必要なMermaidの制限を説明し、既存出力配置を維持。
- npm未統合差分: cli.pyはinitのみ。renderと重複せずmainをbaseに使用。READMEはクイックスタートの局所更新。
- 保護変更: tests/test_render.pyとtests/node/native.test.mjsにブラウザ起動をstubする境界テスト追加。既存テスト・CI・権限は維持。
- 影響確認: affected出力のdocs/cli/node-runtime.mdとdocs/project/decisions/0001-node-runtime.mdを更新。
- 開始retro: 台帳評価中の上限・期限・採用済みを確認。評価中/試行中・採用済みの実行対象なし。
- 検証・独立レビュー: 実行中。
