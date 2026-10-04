---
type: Convention
title: Issue tracker 運用
description: GitHub Issues をこのリポジトリの課題管理先として運用する規約。
tags: [agents, issues]
status: stable
layer: shared
generated:
  by: codex/gpt-6
  at: 2026-10-04T08:39:09Z
related:
  - /CONVENTIONS.md
  - /agents/triage-labels.md
  - /agents/pr-lifecycle.md
---

# Issue tracker: GitHub Issues

このリポジトリでは、作業項目を [GitHub Issues](https://github.com/shirashu687/okf-devkit/issues) で管理する。

## 規約

- 新しい作業項目は1タスク1Issueとし、`gh issue create` で起票する。起票時は `needs-triage` ラベルを付ける。
- Issue の open / closed は課題の未完了 / 完了を示し、状態ラベルは次に必要な行動と担当を示す。進行状況は本文に記録する。
- `docs/backlog/`、`.scratch/`、外部 Issue tracker は使わない。PR は受付対象にしない。
- 旧 `docs/backlog/` の B-0001〜B-0009 は 2026-09-15 に Issue #4〜#12 へ移管し、ファイルは削除した。移行前の本文は git 履歴を参照する。

## triage

open Issueにはカテゴリ1つと状態ラベル1つを付ける。受付時は `needs-triage` で記録し、初期整理でカテゴリ・範囲・次の行動を確定する。対応表とclose時の除去対象は [triage-labels.md](/agents/triage-labels.md) にある。
状態を置換する時は前の状態ラベルだけを除き、無関係なラベルを保持する。分類やラベルの存在を実装・外部操作の許可と扱わない。

## 現在状態の正本

Issue本文に短い日付付きの「現在状態」を置き、調査・承認・着手・PR・merge・受け入れの節目で更新する。
記載するのは、得られた成果と未完了の範囲、対象PR/SHA/検証などの根拠リンク、次の具体的な行動と担当（agent / human / 情報提供者）である。承認は誰が何を許可したか分かる根拠へリンクする。
長い作業ログや認証情報を本文へ貼らない。古いコメント・調査・判断の履歴は保持し、現在状態を別コメントへ分散させない。
コメントで経過を知らせる場合も本文の現在状態へリンクし、そこへ反映していない矛盾する「最新状態」を残さない。

## PRとの接続と完了

調査・設計だけのPRや部分実装PRは `Refs #<Issue番号>` で接続し、残る受け入れ条件を本文へ書く。`Closes` / `Fixes` / `Resolves` で未達のIssueを自動closeしない。
PR作成は成果がレビュー可能になった時点、mergeはmainへ統合された時点として記録する。Issueの受け入れ完了とは分け、必要な実環境検証・手動操作・判断が残る間はopenを保つ。
受け入れ条件が満たされ、closeする権限・依頼範囲があることを確認してからcloseし、次の行動の状態ラベルを除去する。対応しない場合は判断根拠を記録して `wontfix` を保持する。
具体的な各節目の手順と報告は [PRとIssueのライフサイクル](/agents/pr-lifecycle.md) に従う。

## 操作の範囲

本文・ラベル・コメント・closeの実操作は利用者が依頼した対象と範囲で行い、何を変更したか報告する。文書やテンプレートを編集する作業だけでは、既存Issueの一括修正・コメント投稿・closeを実行しない。
