# Issue #50 ライセンス表示

- 作業場所 /workspace/okf-issue50、開始SHA 21829cc40e7ed3300ed9ca282b391125424a49bf、開始時の変更なし。PR #51を分割。Issueでは独立セッションが方針を投稿済み。
- 著作権者だけ `shirashu687` に変更し、年とMIT本文を維持。別セッションでnpm tarballとPython wheel内のLICENSE一致を確認済み。
- npm packは既定cacheに書けず初回失敗。`npm_config_cache=/tmp/okf-license-npm-cache npm pack --ignore-scripts` で再試行しアーカイブ内のLICENSEと一致。既存Pythonテストは下記へ記録する。
- repo内のbranch push・PR作成は分割依頼に含まれる。既存配布物の差替えやリリースは行わない。
- 既存Pythonテスト: 261件、失敗0・エラー0・skip4（Linux）。diffを確認しMIT本文は不変。今回の分割に新たなretroトリガーなし。
