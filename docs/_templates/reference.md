---
type: Reference
title: <一覧の名前（例: サーバー API リファレンス）>
description: <一文で何の一覧かを説明する。>
tags: [<layer>, reference]
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

<1〜2行。この一覧が何を網羅しているかを書く。>

## <カテゴリ名>

| 名前 | 概要 | 実装 |
|---|---|---|
| `<名前>` | <何をするか> | `<ファイルパス>` |

### `<個別項目名>`

| 項目 | 内容 |
|---|---|
| シグネチャ / エンドポイント | `<例: PUT /setlistApi.php?action=save>` |
| 引数 / リクエスト | <パラメータ表または JSON 例> |
| 戻り値 / レスポンス | <型または JSON 例> |
| 備考 | <注意点・副作用> |

---

> **記述ルール**: 推測で書かず、コードから読み取れる事実のみ書く。項目が増えてファイルが長くなったら分割し、`related` と `index.md` で繋ぐ。
