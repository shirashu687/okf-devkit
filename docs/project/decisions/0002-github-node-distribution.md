---
type: Decision Record
title: GitHubでNode.js配布物を固定して配布する
description: GitHubの固定版配布と明示的なAI導入支援を採用し公開操作を人へ分離する。
tags: [decision, node, distribution]
status: stable
layer: shared
generated:
  by: codex/gpt-6
  at: 2026-10-04T09:15:06Z
code_globs:
  - package.json
  - package-lock.json
  - node/*.mjs
  - .github/workflows/release.yml
  - scripts/release-*.mjs
  - scripts/package-smoke.mjs
related:
  - /project/decisions/0001-node-runtime.md
  - /agents/install-okf.md
  - /agents/release-node.md
  - /cli/node-runtime.md
---

# 0002. GitHubでNode.js配布物を固定して配布する

- **決定日**: 2026-10-04
- **状態**: 採用（Issue #34 の利用者承認による方針。実装はDraft PRでレビューし、公開は別操作）

## 背景

Node.js版はチェックアウトとローカルtgzで利用できるが、導入先ごとに何を固定し、AIへ何を任せるかが不明確だった。
Python版は継続し、[0001](/project/decisions/0001-node-runtime.md)の独立Node実装を維持する。
承認済みの範囲は [Issue #34 の設計記録](https://github.com/shirashu687/okf-devkit/issues/34#issuecomment-5977634539) に記載する。

## 選択肢

| 案 | 利点 | 負担 |
| --- | --- | --- |
| npmレジストリへ本体を公開 | npmの通常導線 | 本体公開・認証の運用が追加される |
| GitHubの固定Git SHAとRelease tgz | Gitの対象版と配布物を指定できる | Node/npm/Gitと配布物確認が必要 |
| Node同梱exe | Node未導入でも実行可能 | OS別配布とランタイム更新の負担 |

## 決定

本体はnpmへ公開せず、GitHubの完全Git SHAまたは公開済みReleaseの固定tgzを使う。
Node.js 22以上・npm・Gitを前提とし、欠けている場合は利用者に手動導入を依頼する。Node同梱exeは作らない。
依存パッケージのnpmレジストリからの取得は認める。
本体の `package.json` は `private: true` としてnpm publishを拒否する。`npm pack` とGit依存としての導入は許容し、GitHub配布という承認済み方針を保つ。

標準はリポジトリローカルの固定依存とlockfile。グローバル導入は利用者の明示選択とする。
導入と `init` は別の操作であり、インストールだけではOKF設定やAI設定を作らない。
AIは導入・更新を明示的に依頼された回だけ支援し、自動更新機構を置かない。

タグを契機とするGitHub Actionsで一度作ったtgzを検査し、その同じバイト列とSHA-256をDraft Releaseへ添付する。
Draftの内容とCIを人が確認して公開する。workflow追加だけではReleaseは存在せず、例示URLを実在する成果として扱わない。
タグ・版番号の対応と重複時の拒否を検査し、既存配布物の上書きや自動publishは行わない。
upload直前にDraft状態・ID・タグ・対象コミット・asset・取得元を再確認する。ただしGitHub upload APIには「Draftの場合だけuploadする」という原子的条件がなく、同時publishを完全に防ぐ保証はない。人はworkflowの全job完了とDraftのasset確認後にのみPublishする。既に公開済みのReleaseは読み取り照合だけに留める。

## 理由と境界

Git SHAはコードの対象を固定する。tgzの固定URLとchecksumは対象版・取得後のバイト一致を確認する手段であり、配布者の信頼性を証明しない。
依存の解決結果は導入先のlockfileで記録する。globalでは同じ本体tgzでも推移依存まで同一になる保証がない。
private repoの認証・権限・可視性を変更して導入を成立させない。

AIによる設定管理は、今回の変更前内容を保存し、所有範囲が分かる差分だけを提案する。
現行 `init` は既存ファイルをスキップし、`--force` はファイル全体を置換する。管理部分だけの移行機能ではない。
利用者の編集と競合したら停止して調整し、更新用に `init --force` を使わない。
Node以外のプロジェクトへmanifestを加える場合は、privateなmanifest案・配置・lockfile方式を先に承認してもらう。既存workspaceを保つ。

## 影響

導入支援は [AI向け導入手順](/agents/install-okf.md)、日常の文書更新支援は [日常操作ガイド](/agents/operate-okf.md) の別責務とする。
インストール版と実際に呼ぶCLI/hookの一致を確認する。Python/PATHの既存 `okf` をNode版と取り違えない。
パッケージの復旧は保存したmanifest・lockfileと再インストール、設定・文書・HTMLの復旧は別バックアップから行う。
公開パッケージのリリース、既存ユーザー設定の一括書換えは本設計の導入操作に含めない。

## 参照

- [npm install](https://docs.npmjs.com/cli/v11/commands/npm-install/)
- [npm ci](https://docs.npmjs.com/cli/v11/commands/npm-ci/)
- [GitHub Releaseの管理](https://docs.github.com/en/repositories/releasing-projects-on-github/managing-releases-in-a-repository)
