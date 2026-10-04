---
type: Architecture
title: HTML レンダリングの処理構造
description: Markdown から閲覧用ページと静的アセットを生成する流れ。
tags: [render, implementation]
status: stable
layer: render
generated:
  by: codex/gpt-6
  at: 2026-10-04T06:11:06Z
code_globs:
  - src/okf_devkit/renderer.py
  - src/okf_devkit/assets/**
  - node/renderer.mjs
related:
  - /cli/commands.md
  - /render/output-cleanup.md
---

# HTML レンダリングの処理構造

CLI の既定出力先は `_site/` で、低レベル `render_bundle()` の既定隣接配置は維持する。明示的な `--cleanup-from` だけが旧生成物の整理を計画・実行し、通常実行と hook は整理しない。安全境界と退避・復元の契約は [生成済みHTMLの整理](/render/output-cleanup.md) を参照する。

`render_bundle()` は Bundle、Doc factory、任意の出力先、write フラグを受け取り `RenderReport` を返す。Python は markdown-it-py を利用する。Node 実装は `node/renderer.mjs` にあり、同じ同梱ページ・CSS・JavaScript アセットを使う。

## 生成の流れ

1. index/log を含むバンドルの Markdown を列挙し、各ソースに対応する `.html` の Page を作る。
2. Markdown のトークンと見出しを準備し、内部 Markdown リンクを HTML リンクへ変換する。
3. related と本文リンクから outbound 情報を集め、目次、ナビゲーション、パンくず、信頼度表示、被リンクを組み立てる。
4. `assets/page.html` のトークンへ内容を埋め込み、`_assets/docs.css` と `docs.js` を計画する。
5. write が有効なら変更された生成物だけを atomic write し、不要になった所有マーカー付き HTML を削除する。

HTML の frontmatter 表示は本文の信頼度・状態を補助する。ソースの SHA-256 の短縮値と元 Markdown へのリンクもページに含める。未解決の内部リンクは警告として報告する。

## 出力と検査の境界

低レベル `render_bundle()` の既定出力先はバンドルルートで Markdown の隣へ配置する。CLI の既定出力先は `_site/` で、`--output` はリポジトリ内に限定する。アセットは出力ルートの `_assets/` に配置し、各ページから相対参照する。

`--check` は write を無効にして同じ生成計画を走らせる。ファイル作成・削除も既存 HTML の差分比較も行わない。依存やアセット不足などの RenderError は CLI の運用エラーになる。警告だけでは失敗しない。

`_templates/` 等の除外ディレクトリは閲覧ページに含めない。不要 HTML の削除は所有マーカーを持つ生成物に限定し、手書き HTML を保存する。
