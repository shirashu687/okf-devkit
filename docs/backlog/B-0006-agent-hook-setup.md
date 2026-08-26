---
type: Backlog Item
title: エージェントの Stop hook を自リポジトリに設定する
description: README が勧めている Stop hook をこのリポジトリ自身に設定し、hook の契約を日常的に検証する。
tags: [shared]
status: stable
layer: shared
generated:
  by: "process:okf-cli"
  at: "2026-08-26T12:49:03Z"
state: todo
priority: low
effort: S
feasibility: A
ai: assisted
cost: false
created: "2026-08-26"
done_at: null
related: []
---

# エージェントの Stop hook を自リポジトリに設定する

## やりたいこと

`okf init` が置いた `.okf/hooks/render_hook.sh` を、このリポジトリのエージェント設定から
実際に呼ぶようにする。

## 背景・現状

- `okf init` により `.okf/hooks/render_hook.sh` / `.ps1` は生成済みだが、それを呼ぶ側の設定
  （`.claude/settings.json` / `.codex/hooks.json`）はこのリポジトリに無い。
- README の「エージェント連携」節は利用者に設定を勧めているのに、自分では使っていない。
  そのため hook の契約 —— 成功時は `{}` を返し、失敗時は exit 1、**exit 2 や `decision: block` は
  返さない** —— が日常の作業で検証されていない。
- CI の `smoke` ジョブは `sh .okf/hooks/render_hook.sh` の出力が `{}` であることだけを見ている。

## 進め方

1. `.claude/settings.json` に README 記載の Stop hook を入れる。
2. 生成 HTML は `.gitignore` 済み（`docs/*.html` / `docs/**/*.html` / `docs/_assets/`）なので、
   コミットには混ざらない。念のため hook を数回走らせた後に `git status` を確認する。
3. 内容が変わらなければ書き込まない（`write_if_changed`）ため連打しても安全だが、
   実際に作業を数回まわして所要時間が邪魔にならないかを見る。
4. 問題なければ README の該当節に「このリポジトリでも同じ設定を使っている」と書き添える。

## 完了条件

- [ ] 作業終了時に `docs/` の閲覧用 HTML が自動再生成される
- [ ] hook が失敗してもエージェントの継続実行がブロックされない
- [ ] 生成 HTML がコミットに混ざらない
- [ ] 影響ドキュメントを更新した（`okf affected` の出力）
- [ ] 該当層の `log.md` に追記した
- [ ] 本ファイルの `state` を `done` にし `done_at` を記入した

## 結果

<完了時に記入する。PR / コミットへのリンク、実際に変更したファイル、想定と違った点。>
