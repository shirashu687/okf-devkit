---
type: Decision Record
title: Python不要環境へNode.js実装を追加する
description: Node.jsによる独立実装と共有資産・比較テストでPython不要の導入経路を用意する。
tags: [decision, node, distribution]
status: stable
layer: shared
generated:
  by: process:okf-devkit
  at: "2026-09-10T12:00:00Z"
code_globs:
  - node/*.mjs
  - package.json
  - tests/node/*.mjs
related:
  - /backlog/B-0007-non-python-runtime.md
  - /cli/node-runtime.md
---

# 0001. Python不要環境へNode.js実装を追加する

- **決定日**: 2026-09-10
- **状態**: 採用

## 背景

Pythonのない環境で同等のCLIを使いたいという依頼があり、利用者はNode.js版の追加を選択した。
従来のB-0007ではバイナリ配布を本命とし、二重実装の維持費を理由に移植を避ける方向だった。

## 選択肢

| 案 | 利点 | 負担 |
| --- | --- | --- |
| Pythonを含む単体バイナリ | 実装を一つに保てる | OS・CPUごとのビルドと大きな配布物 |
| Node.js実装 | 既存Node環境でPythonなしに実行できる | 二つの実装の互換性維持 |
| PowerShell実装 | Windows環境との親和性 | YAML・Markdown処理と他OS対応の負担 |

## 決定

`node/` にNode.js 22+向け実装を追加し、npmパッケージのbin名を `okf` とする。
Python本体のダウンロード・起動には依存しない。Python版も継続して利用できる。

## 理由

利用者のNode.js環境に合わせられ、同じ実装をWindows・Linux・macOSで利用する構成にできる。
`defaults.yml`、scaffold、HTMLアセットをPython版と共用し、Node単独テストとPython比較テストを分ける。
YAML 1.1の解釈には `yaml`、HTML変換にはPython側と同系統の `markdown-it` を使う。

## 影響

二つの実装を保守する。共通仕様変更時は両方へ反映し、索引・履歴・HTMLの生成内容を比較する。
全入力に対するバイト一致を保証するものではなく、診断文・厳格な入力拒否・コンソール改行に差がある。
新しいhookはローカルnpmパッケージも探索する。既存hookは手順に従いコピーして更新する。
npm公開は別作業であり、この変更の成果はチェックアウトと `npm pack` によるローカル配布である。
