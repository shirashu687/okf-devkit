---
type: Convention
title: docs ディレクトリの歩き方
description: このディレクトリが OKF v0.2 バンドルであることと、LLM が作業する際の手順を示す入口ドキュメント。
tags: [docs, okf, guide]
status: stable
layer: shared
generated:
  by: codex/gpt-6
  at: 2026-10-04T09:04:08Z
related:
  - /CONVENTIONS.md
  - /agents/issue-tracker.md
  - /agents/operate-okf.md
---

# docs ディレクトリの歩き方

> **このファイルは `docs/` で作業する前に必ず読むこと。** 詳細な書式は [CONVENTIONS.md](/CONVENTIONS.md) にある。

## 1. ここは何か

このリポジトリの `docs/` は OKF 0.2 のバンドル。利用先で OKF 0.3 を使う場合は、版の指定方法と検査オプションを確認する。[コマンド仕様](/cli/commands.md)

- 1 ファイルに 1 コンセプトを書き、パスを文書の ID とする。
- バンドル内の Markdown には YAML frontmatter と `type` を書く。予約ファイルの `index.md` と `log.md` は執筆規約の書式に従う。
- 本文と `related` ではバンドルルートからのパスを推奨する。たとえば `/cli/commands.md` は `docs/cli/commands.md` を指す。生成する目次のリンク形式は `okf.yml` の `index.link_style` で決まる。

## 2. 構成

| パス | 役割 | 編集方法 |
|---|---|---|
| `index.md`（各階層） | 目次。段階的開示の入口 | **自動生成。手で書かない**（マーカー外の前文のみ手書き可） |
| `log.md`（各層） | 変更履歴 | `okf log --write` で追記。手書き修正も可 |
| `CONVENTIONS.md` | 語彙・書式の唯一の基準 | 手書き |
| `AGENTS.md` | 本ファイル | 手書き |
| `project/` | 層をまたぐ知識（概要・用語集・ADR） | 手書き / LLM |
| `cli/` `render/` `scaffold/` | 層ごとの仕様・手順書 | 手書き / LLM |
| `_templates/` | テンプレート集。**バンドル対象外**（index にも lint にも出ない） | 手書き |
| `_site/`（リポジトリルート） | `okf render` の既定出力先。HTML と共有アセットを置く | Markdown を編集して再生成 |

## 3. 目的から操作を選ぶ

目的に合う操作を選び、コマンドの引数、書き込み先、終了コードを確認する。[AI の日常操作](/agents/operate-okf.md) · [コマンド仕様](/cli/commands.md)

- コード変更後: `affected --base <固定SHA>` の対象と未カバーを確認し、code_globs未設定・バンドル外も照合する。本文を更新し、`sync` のindex/log/lint/staleを個別に確認する。
- 新規文書: `new doc` で根拠コードを指定し、本文を補完して `index --write` → `lint`。型とテンプレートは執筆規約を参照する。
- 読み取り点検: `lint` / `index --check` / `stale` / `render --check`。syncは書き込むため使わない。
- 閲覧: `render`（既定 `_site/`）、必要時 `--open`。旧HTMLの整理は別の明示操作。
- 初回導入はインストールと初期化を別々に確認する。[導入ガイド](/agents/install-okf.md)
- 導入済みのリポジトリは設定を調べ、必要な差分を確認してから反映する。[更新ガイド](/agents/upgrade-existing-okf.md)
- backlog利用: 利用先規約を確認する。このrepoの新規課題は [GitHub Issues](/agents/issue-tracker.md) で管理し、docs/backlogへ起票しない。

`okf` は選んだCLIの実体を確認して使う。ローカルNode版は `node node_modules/okf-devkit/node/cli.mjs` 等を明示し、未導入のnpxで別パッケージを取得しない。
本文更新または更新不要の根拠、log追記の結果、未検証・要対応を区別する。generated.atだけを更新して完了にしない。syncのlog警告・未コミットスキップ、stale/gateのexit0を文書更新完了やCI成功と取り違えない。
課題の更新・closeは受け入れ条件と操作の許可を確認して行う。

## 4. 編集時のルール

- `index.md` の自動生成マーカー内は、`okf index --write` で更新する。
- `type` は執筆規約の語彙表から選ぶ。規約外の値は lint がエラーにする。[執筆規約](/CONVENTIONS.md)
- 文書の状態は `status`、backlog アイテムの進捗は `state` に書く。
- 1 ファイルが長くなったら分割し、`related` でつなぐ。
- 恒久ドキュメントは `docs/` に置く。

## 5. 詳細が必要なとき

[コマンド仕様](/cli/commands.md)、[終了hook](/agents/completion-hooks.md)、[生成済みHTMLの整理](/render/output-cleanup.md) を参照する。
生成HTMLの `_site/`、`.okf-render-manifest.json`、`.okf/render-backups/` はGit管理外にする。旧出力の整理は計画確認後の明示操作に限定し、手書き・編集済み・識別不能ファイルは保つ。
