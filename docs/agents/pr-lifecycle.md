---
type: Convention
title: PR準備状態と統合手順
description: PRのDraft解除、部分成果、検証証拠とmerge判断を区別する開発運用規約。
tags: [agents, pull-request]
status: stable
layer: shared
generated:
  by: codex/gpt-6
  at: 2026-10-04T08:40:36Z
code_globs:
  - .github/PULL_REQUEST_TEMPLATE.md
  - .github/ISSUE_TEMPLATE/work-item.md
related:
  - /agents/issue-tracker.md
  - /agents/triage-labels.md
  - /agents/release-node.md
---

# PR準備状態と統合手順

PRはIssueの成果をレビューする単位であり、Issue全体の完了、mergeの許可、Release公開をそれぞれ別に判断する。これは人とAIが使う開発ライフサイクルであり、確認権限やCustom Rulesの変更ではない。

## Draft と Ready

| 状態 | 判断基準 |
| --- | --- |
| Draft | 当該PRに必須の判断・実装・検証・依存baseのいずれかが未完了。未完了項目、次の担当、解除条件を本文に書く |
| Ready | 当該PRの宣言した範囲と受入条件が完了し、現在head SHAとbaseを対象とする必須検証・独立レビューの証拠が揃う。除外範囲とIssueに残る作業を明示する |

「全PRは常にDraft」「CIが緑なら常にReady」という慣習にしない。完成した設計文書だけのPRや承認済みの部分成果は、その範囲を正確に宣言すればReadyにできる。未実装の全機能が完成したとは書かない。除外して合意した検証を後から当該PR必須へ戻さない。範囲を満たす証拠が無ければDraftに留める。

作成者は提出時と各push後に基準を再評価する。完了したPRは慣習でDraftのまま放置せず、本文の証拠を更新して作成者または委任された担当がReadyへ変更する。人の判断・受入が当該PRの必須条件なら、その回答が先である。依頼が「Draft PR作成まで」の場合はReadyへ変更せず、その明示的な停止条件・解除担当と理由を本文に記録する。問題が再発したらDraftへ戻し、理由と次の一手を更新する。

## 本文と証拠

[PRテンプレート](../../.github/PULL_REQUEST_TEMPLATE.md)を使う。本文を最新版へ書き換え、過去のレビューやコメントは履歴として残す。

- 問題と変更後の振る舞い、当該PRの範囲・受入条件・除外範囲・残作業を示す。
- Issue全体の受入条件をこのmergeで満たす場合だけ `Closes #N` を使う。設計のみ・公開準備のみ・部分実装は `Refs #N` とし、残条件と担当を示す。複数PRでの最後の完了も条件を照合してからClosing keywordを選ぶ。
- 現在head SHA、base branchとSHA、実行した検証の対象版・コマンド・成功/失敗/未実行/実行不能・証拠URLを示す。ローカルの成功を遠隔CIや実イベントの成功へ読み替えない。
- 独立レビューを規約軸（Standards）と仕様軸（Spec）に分け、比較元・対象SHA・指摘の修正/未解決を示す。AI/別担当による独立レビュー記録はGitHubの `APPROVED` reviewと別物。GitHub承認やbranch protectionを満たしたと偽らず、設定が求める承認は別に確認する。
- Draftは必須未完・ブロッカー・解除担当を、Readyは基準を満たす根拠を示す。別途合意した作業の未実行はIssueに残す。

## base と最新SHA

作業開始時に比較元を固定し、他者の未コミット変更を触らない。PR作成・各更新・merge直前に、意図したbase、差分、現在head、依存、変更宣言とCI対象を再確認する。base/head変更で既存証拠が対象から外れたら、必要な検証とレビューをやり直す。記録のみの変更に認められた検証の扱いは既存のプロジェクト設定に従い、最新SHAのCI確認を省略する理由にしない。

親PRのsquash merge後は子PRのbaseと差分を再確認する。元の親commitがmainの祖先とは限らないため、親の差分再混入、機能の消失、誤った自動closeを確認し、適切なmain基点へ整えた後に検証・独立レビュー・最新SHAのCIを確認する。既存ブランチの無断書換えやforce pushを手順の前提にしない。

## 状態を更新する時点

各時点で作業担当がIssue本文の現在状態と次アクションのラベルを揃え、PR作成者がPR本文とDraft/Readyを再評価する。操作権限がない場合は差分案と次の担当を報告し、変更済みとは書かない。

| 時点 | 更新内容 |
| --- | --- |
| 調査完了 | カテゴリ・範囲・残る判断/不足事実・次の担当を整理し、初期整理済みならneeds-triageから移す |
| 方針承認 | 承認した範囲と根拠を要約し、実行可能な次の行動と担当を明記する |
| 着手 | 着手した範囲・依存・作業担当を記録する。進行中でも状態ラベルは次の必要行動で選ぶ |
| PR提出・各push | 当該PRの範囲と残条件、対象head/base、検証/review証拠、Draft解除条件またはReady根拠を更新する |
| merge | 実main差分と成果を照合し、部分完了・残作業・受入担当を記録する |
| 受入完了 | Issue全体の条件と根拠を照合してclose権限を確認し、close時の待ち状態ラベルを除く |

## merge と Release

Readyで、正しいbase/diff/現在CIと必要なGitHub承認を確認した後でも、mergeはユーザーの権限・対象と操作の許可に基づく別判断である。Draft作成依頼をmerge許可と扱わない。複数PRをmergeする場合も一件ずつ依存と更新後の状態を照合する。

merge後はIssueの受入条件に対する実際のmain差分と証拠を確認し、最新状態を更新する。設計・部分成果のmergeではIssueをopenのままにする。Release/tag/publishは[配布手順](/agents/release-node.md)の別ゲートに従う。PRのReadyやmergeを公開済みの証拠にしない。

## 既存成果を読む際の境界

- PR #27 はMarkdown4ファイルの設計成果であり、Issue #12のCLI分割本体は未実装。PR #28 は公開準備であり、Issue #8の公開完了ではない。
- PR #25 で合意して除外したClaude実イベント確認は、後から同PRの必須完了条件へ戻さない。
- PR #30 のbase問題はPR #33で復旧済み。親squash後の再確認ルールは今後の再発防止である。
- PR #35 は導入・更新手順と配布の検証実装。main `d539e28` のCI全11ジョブ成功は、実タグからのRelease API書込・初回公開の成功を示さない。Releaseの実行とIssue #32の日常help改善は別範囲である。

これらは過去コメントを改変せず現在の範囲を読むための例であり、個別PRをこの文書だけで再承認・merge・公開しない。
