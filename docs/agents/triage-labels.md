---
type: Convention
title: Triage labels
description: GitHub Issues で使う triage カテゴリと状態ラベルの対応表。
tags: [agents, triage]
status: stable
layer: shared
generated:
  by: codex/gpt-6
  at: 2026-10-04T08:39:09Z
related:
  - /agents/issue-tracker.md
  - /agents/pr-lifecycle.md
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
| needs-triage | needs-triage | 初期のカテゴリ・範囲・次の行動が未整理 |
| needs-info | needs-info | 次の判断・作業に必要な事実が不足 |
| ready-for-agent | ready-for-agent | 承認済みの次の行動をエージェントが進められる |
| ready-for-human | ready-for-human | 次に人の判断・手動操作・受け入れ確認が必要 |
| wontfix | wontfix | 対応しない判断が受け入れられた |

状態ラベルは**次に必要な行動と担当**を表す。実装中・PR作成済み・merge済みという進捗はIssue本文の現在状態と根拠リンクへ記す。open / closedは課題の未完了 / 完了の区別であり、状態ラベルとは別に扱う。
`needs-triage` は従来の広い「maintainerの確認待ち」から、初期整理が未完了の場合へ意味を明確化する。人の承認待ちは `ready-for-human`、不足事実の確認待ちは `needs-info` に分ける。新しいラベル名は追加しない。

## 付け替えと完了時

open Issueはカテゴリ1つと状態1つを持つ。受付直後でカテゴリが未判定なら `needs-triage` で記録し、初期整理時にカテゴリを確定する。不足事実・必要な承認・次の行動を本文へ記し、その内容と状態を一致させる。
調査や設計は承認済み範囲でエージェントが進められるなら `ready-for-agent`。その結果、人の製品判断が必要になった時点で `ready-for-human` にする。承認後に次の作業が明確なら `ready-for-agent` へ戻す。
PR作成やmergeだけを理由にラベルを固定しない。例えばPRレビュー・手動実行・受け入れが人の次の行動なら `ready-for-human`、残る承認済み修正がエージェントの次の行動なら `ready-for-agent` とする。

付け替えでは前の状態ラベルだけを除き、選んだ状態1つを付ける。カテゴリの変更が必要ならその理由を記録して対象カテゴリだけを置換し、無関係なラベルを削除しない。
受け入れ完了または対応しない判断によりcloseする時は、次の行動を表す4ラベル（`needs-triage` / `needs-info` / `ready-for-agent` / `ready-for-human`）を除く。カテゴリと、対応しない場合の `wontfix` は保持する。過去のコメント・判断・ラベル変更履歴を消さない。
受け入れ条件、部分PRの扱い、更新時点は [PRとIssueのライフサイクル](/agents/pr-lifecycle.md) に従う。
