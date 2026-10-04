---
type: How-To
title: HTML の階層ナビと元ファイルを確認する
description: 設定した層とディレクトリ階層を辿り元 Markdown のパスを確認する手順。
tags: [render, navigation]
status: stable
layer: render
generated:
  by: process:codex
  at: "2026-10-03T00:17:54Z"
code_globs:
  - src/okf_devkit/renderer.py
  - node/renderer.mjs
  - src/okf_devkit/assets/*
  - tests/test_render.py
  - tests/node/native.test.mjs
  - tests/node/compatibility.test.mjs
related:
  - /render/backlog-progress.md
  - /cli/node-runtime.md
---

# HTML の階層ナビと元ファイルを確認する

`okf render` を実行して出力した HTML をブラウザーで開く。隣接出力でも `--output _site` の別出力でも同じナビを使える。

サイドナビは実際のディレクトリ階層で表示し、三角印またはディレクトリ名から開閉できる。現在のページを含む祖先は初期状態で展開され、現在の項目を強調する。階層の順序は `okf.yml` の `layers` と `layer_dirs` に合わせる。複数の層が同じ親を持つ場合は設定順の最初の層を基準にし、設定外のディレクトリも名前順で表示する。層名とディレクトリ名が異なる場合は両方を表示する。

各項目はタイトルの下に元のファイル名を表示する。Backlog の状態補助表示も保持する。検索欄はタイトル・ファイル名/パス・状態・タグを対象とし、検索結果のあるディレクトリを展開する。検索を空に戻すと現在のページの祖先を展開した状態に戻る。ページ内目次の表示条件は従来のまま（h2以上が3件以上）。

本文冒頭の `Source:` にリポジトリからの元 Markdown パスを表示し、リンクから元ファイルを開ける。スペース・`#`・`%` を含むファイル名はURLをエンコードする。元ファイルや状態の編集・同期機能は追加しない。

配色と明暗テーマは既存のものを維持する。階層のガイド線、現在位置の色、補助ファイル名の文字サイズ・余白を調整してタイトルとの区別を付ける。狭い画面では既存のメニューボタンからナビを開く。
