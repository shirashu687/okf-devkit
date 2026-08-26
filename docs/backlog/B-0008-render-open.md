---
type: Backlog Item
title: 生成した HTML をコマンド一発で開けるようにする
description: render した HTML を開く手段が無く README の説明とも食い違うため、開くコマンドを用意する。
tags: [cli, render]
status: stable
layer: cli
generated:
  by: "process:okf-cli"
  at: "2026-08-26T13:09:11Z"
state: todo
priority: medium
effort: S
feasibility: A
ai: full
cost: false
created: "2026-08-26"
done_at: null
related: []
---

# 生成した HTML をコマンド一発で開けるようにする

## やりたいこと

`okf render` で作った HTML を、パスを手で辿らずにブラウザで開けるようにする。

## 背景・現状

- README のクイックスタートは `okf render` を「閲覧用 HTML を生成して**ブラウザで開く**」と
  説明しているが、**実際には開かない**。`cmd_render()` は `render_bundle()` を呼んで件数を
  出力するだけで、`webbrowser` も `os.startfile` も使っていない（パッケージ全体を検索しても
  該当箇所は無い）。README の説明が実装より進んでいる。
- そのため今は `docs/index.html` を自分で探して開くことになる。`--output _site` を付けると
  出力先も変わるので、覚えることが増える。
- `file://` で開いた場合、`assets/docs.js` が CDN から動的 import している mermaid
  （`import("https://cdn.jsdelivr.net/npm/mermaid@11.15.0/...")`）はページのオリジンが
  opaque になるためブロックされうる。その場合は `.catch()` で `mermaid-fallback` に落ちるので
  ページは壊れないが、**図は描画されない**。図を確認したいときはローカル HTTP サーバ越しに見る
  必要がある。

## 進め方

1. `okf render --open` を足す。`report.output_root` からトップページのパスを組み立て、
   `webbrowser.open(path.as_uri())` で開く。依存は増えない（標準ライブラリ）。
2. `--check` と `--hook` が指定されているときは**絶対に開かない**。Stop hook のたびに
   ブラウザが開くと作業にならない。
3. mermaid を含むページ向けに `okf serve [--port N] [--open]` を検討する。
   標準ライブラリの `http.server` で出力ディレクトリを配信するだけでよい。
   `--output` 未指定だと配信ルートが `docs/`（Markdown と HTML が同居）になる点に注意。
4. README のクイックスタートを実態に合わせる（`okf render` は生成のみ、開くのは `--open`）。
5. `tests/test_render.py` に「`--hook` / `--check` ではブラウザを開かない」ケースを足す
   （`webbrowser.open` を差し替えて呼ばれないことを確認する）。

## 完了条件

- [ ] `okf render --open` でトップページがブラウザで開く
- [ ] `okf render --hook` と `okf render --check` ではブラウザが開かない
- [ ] README の説明が実装と一致している
- [ ] 影響ドキュメントを更新した（`okf affected` の出力）
- [ ] 該当層の `log.md` に追記した
- [ ] 本ファイルの `state` を `done` にし `done_at` を記入した

## 結果

<完了時に記入する。PR / コミットへのリンク、実際に変更したファイル、想定と違った点。>
