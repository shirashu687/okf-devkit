# 変更履歴 — shared

<!-- `okf log --write` が git 履歴からここに追記する。書式は /CONVENTIONS.md §7 を参照。 -->

## 2026-10-04
- **Update** 初回配布のREADMEと導入案内を検証済み未公開Draftの状態へ合わせ、未公開PyPI例を固定ソース導入へ修正し、公開後の3asset取得・照合とlocal/global選択を明記した。既存配布物は変更しない。 (`e234d78`, `a2720ed`)
- **Creation** v0.1.0の日本語公開予定ノートとPreRelease準備手順を整え、既存Draft検証・別承認公開・同一配布物の境界を明記した。タグ・Release公開は未実行。 (`c4b453f`)
- **Update** AIの日常操作ガイドを既存コマンド仕様の入口として整備し、helpと生成案内のPython/Node回帰を検証した。 (`33b2311`)
- **Creation** GitHub の固定版 tgz 配布・Draft Release workflow、AI 導入更新復旧ガイドと配布担当者向け手順を追加。公開操作は未実行（Issue #34、`a043c6c2`）。
- **Creation** repo共通のadvisory終了アダプターとCopilot/Codex設定を追加し、Claudeも同じ処理へ接続。strict手動生成を保持し、対応表・信頼・二重生成と実イベント未検証の範囲を明記した（Issue #9、`4f2663a`）。

## 2026-10-03
- **Update** CI に自リポジトリの lint・index・render 検査と stale レポートを追加。 (#5, `036d60a`)

- **Update** — リポジトリの Claude Code Stop hook を設定し、共有 scaffold の Node/Python 対応ラッパーに同期した（Issue #9、`b57b9aa`）。
- **Update** fix: point Python package metadata to its repository。 (`3f51be9`)

## 2026-09-07
- **Update** ハーネス導入PRにmainの3層構成と既存Backlog 9件を統合。生成索引の相対リンク、新規T番号、既存B番号を両立した。競合解消と検証の詳細はリポジトリの `harness/state/journal/PR-0002-main-merge.md` を参照。 (`fd74b80`, `85d4b0e`, [PR #2](https://github.com/shirashu687/okf-devkit/pull/2))
