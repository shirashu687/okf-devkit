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

## 検証記録

対象: 実装commit bde6d3eとlog追加working tree。既存venv `C:/Users/rinta/Documents/1_projects/okf-devkit/.venv/Scripts/python.exe` を使用しPYTHONPATHは本worktree/src、元repo/venv未変更。

| 検証 | 状態 | 実コマンド | 証拠 |
| --- | --- | --- | --- |
| Python全suite | 成功 | `<existing-venv-python> tests/run_all.py` | task/issue17-python-release.log、173件/失敗0/error0/skip0 |
| Node依存 | 成功 | `npm ci` | 依存8取得/audit問題0 |
| Node native | 成功 | `npm test` | task/issue17-node-release.log、14件/失敗0 |
| Python/Node互換 | 成功 | `OKF_TEST_PYTHON=<existing-venv-python> npm run test:compat` | task/issue17-compat-release.log、8件/失敗0 |
| affected | 成功 | `<existing-venv-python> -m okf_devkit.cli affected --base 44f7777` | Node手順/ADRを列挙、双方本文更新 |
| OKF index | 成功 | `<existing-venv-python> -m okf_devkit.cli index --write` / `index --check` | 全index最新 |
| OKF lint | 成功 | `<existing-venv-python> -m okf_devkit.cli lint` | error0/warn0 |
| task/PR宣言 | 成功 | `<existing-venv-python> harness/project/check_changes.py --base 44f7777` / `--scope pull-request --base 44f7777` | task/issue17-task-declaration.log / issue17-pr-declaration.log、3tests＋workflow declared、exit0 |
| 最新SHA CI | 未実行 | push/Draft PR後、headSHAと9job照合 | 現時点未実行を成功扱いしない |

## 独立レビュー

- 仕様軸: docs_ciがIssue #17とbase44f7777から全working/untrackedを独立照合、指摘0。CLI既定/明示旧配置/library保全/check/hook/open/ignore/移行案内一致。
- 標準軸: 親が同じbaseからfull diffを独立照合、製品規約違反/smellなし。既存境界保護とCI強化、task/PR宣言対象一致。
- 完了の最終項目: cli/render/scaffold logにUpdateと実commit bde6d3eを追加し、4値と対象版/実コマンド/証拠を記録。
- 別PR #24 の未統合新文書4件はこのbaseに未存在で旧既定の記述あり。親へ統合時の_site更新必要を通知。

## 摩擦観測とretroゲート

- 確認範囲: 依頼、Issue、base/依存、製品差分、検証、二軸独立review、完成ログ/次のCI確認手順。
- 判定: トリガーなし。合意済みのCLI既定変更と計画済みのcompletion記録で要件修正・予期しない失敗・探索反復なし。full retro/新台帳行は作らない。
- 処理済み事象/台帳ID: なし。
- 未確認: 最新SHA CI、#24含む将来統合時のドキュメント/宣言。次の一手はDraft PR base/head固定の9job確認。親が依存PR順序を維持。

- 最終log/記録追記後のrelease全検証: 173/14/8件success、lint error0/warn0、index最新。親は最終3logと4値記録も独立再確認し標準指摘0。
