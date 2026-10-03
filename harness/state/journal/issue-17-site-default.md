# Issue #17 render default _site

- 開始/baseSHA: 44f7777166c575e14d32166efadc386f656b58ad。task/issue17、branch codex/issue17-site-default。開始clean。
- 依存: Draft PR #22 (--open)のheadからstackし、PR baseはcodex/issue11-render-open。mainからの全変更をこのPR範囲と誤認しない。統合時PR baseが変わる場合は宣言をそのbase/headに再確認する。
- 目的: 両CLIのrender既定をproject root/_siteへ変更。--checkは生成しない、--hook/wrapperは_siteへ生成。
- 対象外: render.output config新設、旧HTML自動削除、renderer libraryの既定変更、ユーザーのグローバルhook・.gitignore変更、merge/公開。
- 設計: CLIで明示--outputを優先し未指定だけ_siteへ解決。ライブラリ関数の隣接既定は保持。--output docs（独自bundle_rootならそのpath）で旧動作を選べる。既存生成物は残し、生成マーカー確認の移行案内をREADMEに記述。
- initは.gitignoreの_site/追加案内を両実装で出力し、既存ユーザーの.gitignoreを変更しない。CI smokeにcheck dry-runとwrapperの新配置確認を追加、既存CIテスト維持。
- 連携: #21/#16担当へ通知。node/renderer cmdRender出力解決のみでnavigation/source/template関連diffと別hunk。
- affected文書、README、docs/配布AGENTSの新既定/互換案内を更新。
- 保護変更: tests/test_render.py / tests/node/native.test.mjs / tests/node/compatibility.test.mjs / .github/workflows/ci.yml。既存libraryテストを保持しCLI既定/明示旧配置とhook/checkの境界を追加。
- 開始retro: 評価中/試行中期限・採用済み確認、今回へ自動適用する項目なし。
- 検証/独立review: 実行中。
