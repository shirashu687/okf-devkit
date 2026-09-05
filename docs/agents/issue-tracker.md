---
type: Convention
title: Issue tracker 運用
description: docs/backlog をローカルの課題管理先として運用する規約。
tags: [agents, backlog]
status: stable
layer: shared
generated:
  by: process:okf-devkit
  at: 2026-09-05T14:17:35+09:00
related:
  - /CONVENTIONS.md
  - /agents/triage-labels.md
---

# Issue tracker: docs/backlog

このリポジトリでは、作業項目を docs/backlog/ の Markdown ファイルで管理する。

## 規約

- 1タスク1ファイルとし、docs/backlog/T-NNNN-<kebab>.md に置く。
- 新規作成には、既存の仮想環境の .venv/Scripts/python.exe -m okf_devkit.cli new backlog --title "..." --layer shared を使う。
- state は todo / doing / done / dropped の進捗であり、triage ラベルとは別に扱う。
- .scratch/、GitHub Issues、外部 Issue tracker は使わない。PR は受付対象にしない。
- 詳細な frontmatter と完了条件は docs/CONVENTIONS.md に従う。

## triage

tags には既存タグを保持したうえで、カテゴリ1つと状態ラベル1つを追加する。対応表は triage-labels.md にある。
