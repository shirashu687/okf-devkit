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

`docs/` は **OKF (Open Knowledge Format) v0.2 バンドル**である。

- 1ファイル = 1コンセプト。**ファイルパスがそのドキュメントの ID**
- すべての `.md` は **YAML frontmatter を持ち、`type` が必須**（`index.md` / `log.md` を除く）
- 本文と `related` のリンクは**バンドルルート起点の絶対パス**（例: `/project/glossary.md` = `docs/project/glossary.md`）を推奨する。自動生成 `index.md` のリンク形式だけは `okf.yml` の `index.link_style` に従う
- 仕様: <https://github.com/GoogleCloudPlatform/open-knowledge-format>

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
| `_assets/` / `*.html` | `okf render` の閲覧用生成物。**バンドル対象外・Git管理外** | 手で編集しない |

## 3. 目的から操作を選ぶ

日常の短い入口は [AIの日常操作](/agents/operate-okf.md)、各コマンドの入出力・副作用・終了状態は [コマンド仕様](/cli/commands.md) を正本とする。

- コード変更後: `affected --base <固定SHA>` の対象と未カバーを確認し、code_globs未設定・バンドル外も照合する。本文を更新し、`sync` のindex/log/lint/staleを個別に確認する。
- 新規文書: `new doc` で根拠コードを指定し、本文を補完して `index --write` → `lint`。型とテンプレートは執筆規約を参照する。
- 読み取り点検: `lint` / `index --check` / `stale` / `render --check`。syncは書き込むため使わない。
- 閲覧: `render`（既定 `_site/`）、必要時 `--open`。旧HTMLの整理は別の明示操作。
- 初回導入・更新: [導入ガイド](/agents/install-okf.md)。installとinitを分け、既存編集を保つ。
- backlog利用: 利用先規約を確認する。このrepoの新規課題は [GitHub Issues](/agents/issue-tracker.md) で管理し、docs/backlogへ起票しない。

`okf` は選んだCLIの実体を確認して使う。ローカルNode版は `node node_modules/okf-devkit/node/cli.mjs` 等を明示し、未導入のnpxで別パッケージを取得しない。
本文更新または更新不要の根拠、log追記の結果、未検証・要対応を区別する。generated.atだけを更新して完了にしない。syncのlog警告・未コミットスキップ、stale/gateのexit0を文書更新完了やCI成功と取り違えない。
課題の更新・closeは受け入れ条件と操作の許可を確認して行う。

## 4. やってはいけないこと

- ❌ `index.md` を手で書く（自動生成物。`<!-- okf:auto:start -->` 〜 `<!-- okf:auto:end -->` の中身は上書きされる）
- ❌ `type` を [CONVENTIONS.md](/CONVENTIONS.md) の語彙表にない値で書く（lint が error にする）
- ❌ `status`（ドキュメントの状態）と `state`（backlog の進捗）を混同する。**別物**
- ❌ 巨大な1ファイルに追記し続ける。分割して `related` で繋ぐ
- ❌ `docs/` の外に恒久ドキュメントを置く

## 5. 詳細が必要なとき

[コマンド仕様](/cli/commands.md)、[終了hook](/agents/completion-hooks.md)、[生成済みHTMLの整理](/render/output-cleanup.md) を参照する。
生成HTMLの `_site/`、`.okf-render-manifest.json`、`.okf/render-backups/` はGit管理外にする。旧出力の整理は計画確認後の明示操作に限定し、手書き・編集済み・識別不能ファイルは保つ。
