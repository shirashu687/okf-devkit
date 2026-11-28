# OKF 0.3 対応後の文書点検

| 項目 | 値 |
| --- | --- |
| 状態 | 完了 |
| リポジトリ | `shirashu687/okf-devkit` |
| 作業ブランチ | `codex/audit-docs-after-okf03` |
| 開始 SHA | `981d71e88006b6e6323ff2c128f2718106531bd5` |
| 作業日 | 2026-11-28（JST） |
| 対象の要件 | Node.js 24 を最低版にする検討の起票、現行文書と配布雛形の点検と推敲 |

開始時の作業ツリーはクリーン。作業は別 worktree で行い、元の作業ツリーのブランチと未追跡の作業記録を保った。

## 判断と根拠

| 確認箇所 | 観測と変更 |
| --- | --- |
| Node.js の期限と最低版 | Node.js 22 は 2027-04-30、24 は 2028-04-30 がサポートの終了予定日。最低版の切り替えは時期と移行手順を [Issue #96](https://github.com/shirashu687/okf-devkit/issues/96) に記録した。一次資料は [Node.js の公式日程](https://github.com/nodejs/Release#release-schedule) |
| 公開版と開発版 | README と導入ガイドの v0.1.0 の取得例を維持し、OKF 0.3 や診断コマンドを試すには対応する完全 SHA が必要であることを追記。根拠はタグ `12cdb44c2876b50bd7337a5ea20f7744a27d7802` の CLI と現在の parser |
| 仕様版と検査 | このリポジトリの版は `docs/index.md` の 0.2。CLI は `config.py` と `commands/lint.py` で版を判定し、0.3 のプロジェクト規約を `--project` で検査する。運用手順、移行用の依頼文、配布雛形の例をそろえた |
| HTML の出力先 | `commands/render.py` の `args.output or "_site"` を根拠に、執筆規約の案内を修正。従来の隣接配置は `--output docs` で選べる |
| Node.js の YAML と配布検査 | `src/node/core.mjs` の `parseYaml` と `.github/workflows/ci.yml` を照合し、YAML の版と `test:package` のマトリクス条件を明記した |
| 外部操作 | Issue #96 を起票。作業ブランチを push して main 向けのレビュー用 PR を作成する。配布版を選ぶ作業とタグ・Release の操作は別工程 |

## yomiyasu の確認

[doukin-docs の yomiyasu 3.1.0](https://github.com/chuka57/doukin-docs/blob/1b91286132080aec377ff68cd8ea8ab271472734/.agents/skills/yomiyasu/SKILL.md) で、既存文書 11 ファイルと配布する雛形 2 ファイルを確認した。原文の lint、差分と資料の照合、最終稿のハッシュ照合を実行した。初期化と更新の事前条件を文で分け、現在の実装説明から分割履歴の記録へリンクした。残った指摘のうち、識別子、コマンドの引数、専門用語、コード例は役割を確認して保持した。

| ファイル | 照合した最終稿の SHA-256 接頭辞 |
| --- | --- |
+| `README.md` | `1bd48e4ada76` |
| `docs/AGENTS.md` | `614ba6580c37` |
| `docs/CONVENTIONS.md` | `3a6ab1c13624` |
| `docs/agents/operate-okf.md` | `38f5b66d51b8` |
| `docs/agents/install-okf.md` | `a7ce4952a472` |
| `docs/agents/upgrade-existing-okf.md` | `df299d897b1e` |
| `docs/cli/commands.md` | `232b999d2534` |
| `docs/cli/node-runtime.md` | `eaf8353f7e93` |
| `docs/cli/architecture.md` | `fa6c1497b0cf` |
| `docs/scaffold/reference.md` | `6316187b9e09` |
| `docs/render/backlog-progress.md` | `92eaac84d22e` |
| `src/okf_devkit/scaffold/AGENTS.md.tmpl` | `448c0470996e` |
| `src/okf_devkit/scaffold/CONVENTIONS.md.tmpl` | `0f18066914e3` |

## 検証

| 適用対象 | 結果 | 確認内容 |
| --- | --- | --- |
| `tests/run_all.py` | 成功 | 273 件、失敗 0、エラー 0、スキップ 5 |
| Node.js 24 | 成功 | `npm test` 30 件成功、Windows 固有 2 件スキップ。Python 版との比較 22 件成功 |
| 配布検査 | 成功 | `npm run test:release` 14 件、`npm run test:package` 3 件 |
| このリポジトリの OKF バンドル | 成功 | `index --write` は更新なし。両 CLI で `lint --strict` のエラー・警告 0、`index --check` は最新、`render --check` は 36 ページを検査して警告 0 |
| 一時リポジトリでの例の検証 | 成功 | 両 CLI で版表示、`init --agent none --runner`、`doctor`、`upgrade --check`、0.2 から 0.3 への宣言変更、0.3 の規約検査、既定の HTML 出力先を確認 |
| 差分と保護対象 | 成功 | 開始 SHA からの空白エラーなし。タスク比較では全パスが通常変更 |

一時リポジトリの初回検査は、フィクスチャで存在しない `docs/project/` に文書を作ろうとして失敗した。`init` が作った `docs/app/` を使って再試行し、両 CLI で成功した。

## レビュー

- 仕様面は CLI の実装、既存リリース、実行結果を開始 SHA からの差分と照合した。バンドルの版の宣言とプロジェクト規約の検査条件を確認した。
- 標準面はリポジトリの指示、文書の執筆規約、保護対象の検査を確認した。13 ファイルの本文・雛形とこの作業記録が対象。
- 振り返り手順 §2 と改善台帳を照合した。フィクスチャのパスは再試行で解決し、必須検証の欠落や報告との不一致は残っていない。full retrospective は不要と判断した。
- ローカルの検証対象は Linux 上の Python 3.12 と Node.js 24。OS とランタイムの行列は PR の GitHub Actions を参照する。
