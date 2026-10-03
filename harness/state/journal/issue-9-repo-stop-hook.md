# Issue #9: リポジトリ Stop hook

- 状態: review中
- 作業場所: task/issue9、ブランチ: codex/issue-9-repo-stop-hook
- 開始SHA: 9d72e0e5798883d81789582d8879f139865d37b5
- 開始時の変更: なし（独立worktree）。npm未統合ブランチは変更していない。
- 目的: Issue #9 の repo Claude Code Stop hook を設定する。グローバル設定、Codex固有設定、公開、mergeは範囲外。

## 判断

既存 enabledPlugins キーを維持し README 記載と同じ Stop hook を追加した。
repo の古い Python専用 hook は共有 scaffold の現行2ファイルと一致させた。
Node/Pythonを探索し、失敗時に1を返す既存仕様をそのまま利用する。
`affected --base` は更新対象0、README未カバー。node-runtimeに repo側設定の説明を明示補足した。

## 検証

対象は開始SHA + 今回のhook/config/README/node-runtime差分。以下はすべて成功。

- 既存Python venvで `tests/run_all.py`: 169件、失敗0、エラー0、スキップ0。
- `npm ci --ignore-scripts`、`npm test`: 11件成功。
- `OKF_TEST_PYTHON`を既存venvに指定し `npm run test:compat`: 7件成功。
- OKF index --write / lint / index --check: error 0、warn 0、索引最新。
- repo hook PowerShell 5.1 / Git付属sh: 各2回ともstdout `{}`、exit 0。
  PowerShell 2回の合計実測1.425秒。繰り返し後もHTML/assetsはgit statusに現れない。
- 壊れた一時repoに対する両ラッパー: exit 1、stdout空、decisionなし。

Claude Codeの実イベント呼出しは未実行。設定・ラッパーの実行契約を検証し、
ログイン済みエージェントセッションでの自動呼出しを観測したとは報告しない。

## review

仕様軸 / 標準軸: 独立review待ち。

## retroゲート

開始時にledgerの試行中0/採用済み0を確認。既知の別workspace/既存venv前提で
手順を実行し、要件欠落・反復・予期しない失敗などの新規トリガーなし。
shared log追記後のlintでL8 warn1を検出。新しい日付を先頭に移し再検証した。
この再試行は成功履歴へ読み替えず保持する。full retrospectiveを実施し、症状/原因仮説/分類/対処候補/確認方法をledger IMP-0010に観測1件として記録した。
恒久採用・試行は未開始。review完了後に差分・検証・依頼を最終照合する。

## 次の一手

独立二軸reviewを完了し、push/Draft PRと最新SHAのCIを確認する。
