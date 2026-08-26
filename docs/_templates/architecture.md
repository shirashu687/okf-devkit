---
type: Architecture
title: <構造の名前（例: バッチ処理パイプライン）>
description: <一文で何の構造かを説明する。>
tags: [<layer>, architecture]
status: draft
layer: <client | server | batch | shared>
generated:
  by: claude-code/opus-5
  at: <YYYY-MM-DDTHH:MM:SSZ>
code_globs:
  - <リポジトリルートからのパス or glob>
related:
  - </関連ドキュメントのバンドル相対パス>
---

# <タイトル>

<1〜3行で全体像を説明する。>

## 全体図

```mermaid
flowchart TD
    A[入口] --> B[処理]
    B --> C[出力]
```

## 構成要素

| 要素 | 責務 | 実装 |
|---|---|---|
| <名前> | <何をするか> | `<ファイルパス>` |

## データフロー

<どのデータがどこを通ってどう変換されるかを、図または箇条書きで示す。>

## 設計上の制約・前提

- <なぜこの構造なのか。判断の背景が長くなる場合は `Decision Record` に切り出し、`related` で繋ぐ。>
