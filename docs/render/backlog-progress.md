---
type: How-To
title: Backlog の進捗を HTML で確認する
description: 読み取り専用の Backlog 状態一覧と件数を既存 HTML で閲覧する手順。
tags: [render, backlog]
status: stable
layer: render
generated:
  by: process:codex
  at: "2026-10-04T01:48:12Z"
code_globs:
  - src/okf_devkit/renderer.py
  - node/renderer.mjs
  - src/okf_devkit/assets/*
  - tests/test_render.py
  - tests/node/native.test.mjs
  - tests/node/compatibility.test.mjs
related:
  - /cli/node-runtime.md
  - /project/decisions/0001-node-runtime.md
---

# Backlog の進捗を HTML で確認する

## 閲覧手順

```bash
okf index --write
okf render --output _site
```

出力先の `index.html` をブラウザーで開く。Python 版と Node.js 版は同じ一覧を生成する。
ルートと `backlog.dir` の索引 HTML に、状態別の件数とタイトル・ID（採番を含む元ファイルのパス）・`state` の一覧が表示される。タイトルから項目の本文 HTML へ移動できる。本文の「Markdownを開く」から元ファイルを確認できる。既定は `_site` に出力する。隣接出力は `okf render --output docs`（カスタムbundle_rootならそのパス）で同じ情報を確認できる。

`todo` は未着手、`doing` は進行中、`done` は完了、`dropped` は取り下げ。色だけに頼らず文字で表示する。`status` は文書自体の状態なので、進捗の集計には使わない。サイドナビにも Backlog Item のファイル名と状態を表示し、既存の検索欄でタイトル・ID・状態・タグを検索できる。検索はサイドナビの絞り込みであり、一覧の件数は全対象を表す。

## 設定と対象

一覧対象は `okf.yml` の `backlog.dir` 直下の `Backlog Item`。予約文書・別 type・配下の別ディレクトリは一覧に含めない。設定の `state_order` 順に表示し、`states` の追加語彙も件数へ含める。未知の状態は最後に表示し、未設定の状態は「未設定」として隠さず表示する。語彙の不適合は `okf lint` で確認する。

対象が0件の場合もルート HTML に空の一覧と状態ごとの0件を表示する。Backlog 索引が未作成でもルートで確認できる。索引も閲覧したい場合は先に `okf index --write` を実行する。

## 状態を反映する

元 Markdown の frontmatter の `state` を更新して `okf render` を再実行すると、一覧・件数も更新される。生成・閲覧では元 Markdown を変更しない。画面からの編集・同期や別の管理データは持たない。このリポジトリ自身の課題管理は GitHub Issues を継続する。

サイドナビは [階層ナビの手順](/render/navigation.md) に従いディレクトリ階層で表示する。検索中は一致する項目の祖先を展開する。状態・全件数の意味は変わらない。

## 状態別リストとカンバン

初期表示は状態別リスト。タイトルを主にし、元ファイルのIDと設定の許可値に一致する既存のpriority・effortを補助情報として表示する。doing・todoとカスタム状態は開いた状態、done・droppedは折り畳み、summaryをキーボードでも開閉できる。状態名・並び順・全対象件数は元の設定とMarkdownを基準にする。

JavaScriptが有効なら「カンバン表示」で同じ項目を列状に切り替えられる。狭い画面では一列になる。Backlog専用検索はタイトル・ID・状態・補助情報で絞り込み、一致した完了項目も開いて表示する。検索を消すと検索開始前の開閉状態へ戻る。件数サマリーは全対象を表し、検索結果件数は別に読み上げる。JavaScriptが無効でも本文リンクとネイティブの折り畳みリストを利用できる。

切替・検索は表示だけを変更し、Markdown、state、生成時刻、cleanup manifestを編集しない。
