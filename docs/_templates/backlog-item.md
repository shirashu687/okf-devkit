---
type: Backlog Item
title: <やりたいことの名前>
description: <一文で何をするかを書く。>
tags: [<layer>]
status: stable
layer: <client | server | batch | shared>
generated:
  by: process:okf-cli
  at: <YYYY-MM-DDTHH:MM:SSZ>
state: todo
priority: medium
effort: M
feasibility: B
ai: assisted
cost: false
created: <YYYY-MM-DD>
done_at: null
related: []
---

# <タイトル>

## やりたいこと

<★ユーザーが書くのはここだけ。1〜3行でよい。>

## 背景・現状

<LLM が調査して記入する。現在のコードがどうなっているか、なぜ必要か。>

## 進め方

<LLM が記入する。手順・影響範囲・変更するファイル。>

## 完了条件

- [ ] <満たすべき条件>
- [ ] 影響ドキュメントを更新した（`okf affected` の出力）
- [ ] 該当層の `log.md` に追記した
- [ ] 本ファイルの `state` を `done` にし `done_at` を記入した

## 結果

<完了時に記入する。PR / コミットへのリンク、実際に変更したファイル、想定と違った点。>
