---
type: Convention
title: Triage labels
description: GitHub Issues で使う triage カテゴリと状態ラベルの対応表。
tags: [agents, triage]
status: stable
layer: shared
generated:
  by: devin/swe-2-max
  at: 2026-09-14T15:25:14Z
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

triage 済みの Issue には、カテゴリを1つ、状態を1つだけラベルとして付ける。Issue の open / closed が進捗であり、これらのラベルとは別に扱う。
