---
type: Convention
title: Issue tracker 運用
description: GitHub Issues をこのリポジトリの課題管理先として運用する規約。
tags: [agents, issues]
status: stable
layer: shared
generated:
  by: devin/swe-2-max
  at: 2026-09-14T15:25:14Z
related:
  - /CONVENTIONS.md
  - /agents/triage-labels.md
---

# Issue tracker: GitHub Issues

このリポジトリでは、作業項目を [GitHub Issues](https://github.com/shirashu687/okf-devkit/issues) で管理する。

## 規約

- 新しい作業項目は1タスク1Issueとし、`gh issue create` で起票する。起票時は `needs-triage` ラベルを付ける。
- Issue の open / closed が進捗であり、triage ラベルとは別に扱う。
- `docs/backlog/`、`.scratch/`、外部 Issue tracker は使わない。PR は受付対象にしない。
- 旧 `docs/backlog/` の B-0001〜B-0009 は 2026-09-15 に Issue #4〜#12 へ移管し、ファイルは削除した。移行前の本文は git 履歴を参照する。

## triage

Issue には既存ラベルを保持したうえで、カテゴリ1つと状態ラベル1つを付ける。対応表は [triage-labels.md](/agents/triage-labels.md) にある。
