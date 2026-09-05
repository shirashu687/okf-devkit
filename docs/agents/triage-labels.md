---
type: Convention
title: Triage labels
description: docs/backlog で使う triage カテゴリと状態ラベルの対応表。
tags: [agents, triage]
status: stable
layer: shared
generated:
  by: process:okf-devkit
  at: 2026-09-05T14:17:35+09:00
related:
  - /agents/issue-tracker.md
  - /CONVENTIONS.md
---

# Triage labels

## Category roles

| Role | Label in this tracker | Meaning |
|---|---|---|
| bug | bug | 何かが壊れている |
| enhancement | enhancement | 新機能または改善 |

## State roles

| Canonical role | Label in this tracker | Meaning |
|---|---|---|
| needs-triage | needs-triage | maintainer の確認待ち |
| needs-info | needs-info | 起票者から追加情報が必要 |
| ready-for-agent | ready-for-agent | エージェントが作業可能 |
| ready-for-human | ready-for-human | 人間の判断・作業が必要 |
| wontfix | wontfix | 対応しない |

triage 済みの backlog item には、カテゴリを1つ、状態を1つだけ tags に記録する。state は backlog の進捗であり、これらのラベルとは別に扱う。
