---
type: Convention
title: docs ディレクトリの歩き方
description: このディレクトリが OKF v0.2 バンドルであることと、LLM が作業する際の手順を示す入口ドキュメント。
tags: [docs, okf, guide]
status: stable
layer: shared
generated:
  by: process:okf-devkit
  at: 2026-09-05T05:14:59Z
related:
  - /CONVENTIONS.md
---

# docs ディレクトリの歩き方

> **このファイルは `docs/` で作業する前に必ず読むこと。** 詳細な書式は [CONVENTIONS.md](/CONVENTIONS.md) にある。

## 1. ここは何か

`docs/` は **OKF (Open Knowledge Format) v0.2 バンドル**である。

- 1ファイル = 1コンセプト。**ファイルパスがそのドキュメントの ID**
- すべての `.md` は **YAML frontmatter を持ち、`type` が必須**（`index.md` / `log.md` を除く）
- リンクは**バンドルルート起点の絶対パス**（例: `/project/glossary.md` = `docs/project/glossary.md`）で書く
- 仕様: <https://github.com/GoogleCloudPlatform/open-knowledge-format>

## 2. 構成

| パス | 役割 | 編集方法 |
|---|---|---|
| `index.md`（各階層） | 目次。段階的開示の入口 | **自動生成。手で書かない**（マーカー外の前文のみ手書き可） |
| `log.md`（各層） | 変更履歴 | `okf log --write` で追記。手書き修正も可 |
| `CONVENTIONS.md` | 語彙・書式の唯一の基準 | 手書き |
| `AGENTS.md` | 本ファイル | 手書き |
| `project/` | 層をまたぐ知識（概要・用語集・ADR） | 手書き / LLM |
| — | 層ごとの仕様・手順書 | 手書き / LLM |
| `backlog/` | やること1件1ファイル | `okf new backlog` |
| `_templates/` | テンプレート集。**バンドル対象外**（index にも lint にも出ない） | 手書き |
| `_assets/` / `*.html` | `okf render` の閲覧用生成物。**バンドル対象外・Git管理外** | 手で編集しない |

## 3. 作業パターン別の手順

### A. 新しいドキュメントを作る

1. `_templates/` から該当するテンプレートを選ぶ（下表）
2. `okf new doc --layer <layer> --type "<type>" --title "<title>"` で雛形を生成してもよい
3. 本文を書く。**frontmatter の `code_globs` に必ず根拠コードのパス/glob を書く**（これが更新検知の起点になる）
4. `okf index --write` で目次を更新する

| 書きたいもの | type | テンプレート |
|---|---|---|
| 構造・データフロー・図 | `Architecture` | `_templates/architecture.md` |
| 一覧・仕様（API / コンポーネント / テーブル） | `Reference` | `_templates/reference.md` |
| 手順書・使い方 | `How-To` | `_templates/how-to.md` |
| 設計判断の記録（なぜそうしたか） | `Decision Record` | `_templates/decision-record.md` |
| やりたいこと | `Backlog Item` | `_templates/backlog-item.md` |
| 用語集 | `Glossary` | `_templates/glossary.md` |
| プロジェクト全体像 | `Project Overview` | — |
| 執筆規約 | `Convention` | — |

### B. コードを変更したあと（最重要）

**探索しないこと。** 更新すべきドキュメントはスクリプトが教えてくれる。

```bash
okf affected --base main
```

出力されたファイル**だけ**を開いて本文を更新し、`generated.at` を現在時刻に更新する。そのうえで:

```bash
okf sync
```

これで `index.md` 再生成 → `log.md` 追記 → lint → 陳腐化チェックまで一括で走る。

### C. ユーザーが「やりたいこと」を言ったとき

```bash
okf new backlog --title "<やりたいこと>" --layer <layer>
```

ID 採番と frontmatter はスクリプトが埋める。LLM は `## 背景・現状` `## 進め方` `## 完了条件` を調査して記入する。

### D. 作業が完了したとき — 完了の定義

次の3点が揃って初めて「完了」とする。1つでも欠けていたら完了ではない。

1. 影響ドキュメントの本文更新（対象は `okf affected` が出力するもの）
2. 該当層 `docs/<layer>/log.md` への追記（`okf log --write` で生成）
3. 対応する `docs/backlog/*.md` の `state:` 更新（完了なら `state: done` + `done_at`）

## 4. やってはいけないこと

- ❌ `index.md` を手で書く（自動生成物。`<!-- okf:auto:start -->` 〜 `<!-- okf:auto:end -->` の中身は上書きされる）
- ❌ `type` を [CONVENTIONS.md](/CONVENTIONS.md) の語彙表にない値で書く（lint が error にする）
- ❌ `status`（ドキュメントの状態）と `state`（backlog の進捗）を混同する。**別物**
- ❌ 巨大な1ファイルに追記し続ける。分割して `related` で繋ぐ
- ❌ `docs/` の外に恒久ドキュメントを置く

## 5. コマンド早見表

```bash
okf index --write            # 全 index.md を再生成
okf log --write              # git 履歴から log.md に追記
okf lint                     # OKF 適合 + 語彙検証
okf stale                    # 陳腐化レポート
okf affected --base main     # 更新すべきドキュメントを列挙
okf new backlog --title "..." --layer shared
okf status                   # backlog 集計
okf render                   # Markdown の隣に閲覧用 HTML を生成
okf render --output _site    # 公開用の独立サイトを生成
okf sync                     # index → log → lint → stale を一括
```
