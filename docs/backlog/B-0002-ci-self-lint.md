---
type: Backlog Item
title: CI で自リポジトリの docs バンドルを検証する
description: CI で自リポジトリの docs バンドルを検証し、ドキュメントの更新漏れをプルリクで落とせるようにする。
tags: [shared]
status: stable
layer: shared
generated:
  by: "process:okf-cli"
  at: "2026-08-26T12:49:03Z"
state: todo
priority: high
effort: S
feasibility: A
ai: full
cost: false
created: "2026-08-26"
done_at: null
related:
  - /backlog/B-0001-self-hosted-docs.md
  - /backlog/B-0004-new-doc-placeholder.md
---

# CI で自リポジトリの docs バンドルを検証する

## やりたいこと

`.github/workflows/ci.yml` に、**このリポジトリ自身の `docs/`** を検証するジョブを足す。

## 背景・現状

- 現在の CI は 2 ジョブ。`test` は `python tests/run_all.py` を回すだけ、`smoke` は `mktemp -d` した
  一時リポジトリに対して init → index → lint → render → log を通す。
- どちらも検証しているのは「init 直後のバンドルが壊れていないこと」であり、
  **このリポジトリの `docs/` は一度も検証されない**。
- そのため `docs/index.md` の再生成を忘れても（lint L13 が error になる状態でも）CI は緑のまま通る。
- README の「CI」節は利用者に `okf lint` / `okf index --check` / `okf render --check` を勧めているのに、
  自分では回していない。

## 進め方

1. `ci.yml` に `self-check` ジョブを追加する（`ubuntu-latest` / `pip install -e .`）。
2. 実行するのは次の 3 つ。いずれも書き込みをせず、差分があれば exit 1 になる。

   ```bash
   okf lint
   okf index --check
   okf render --check
   ```

3. `actions/checkout` は `fetch-depth: 0` にする。lint 系だけなら浅いクローンでも動くが、
   `okf stale` の outdated 判定と `okf log` は git 履歴を辿るため、浅いと結果が不正確になる
   （`is_shallow()` が警告を出す）。
4. `okf stale` は常に exit 0 を返すので、CI に足しても落ちない。まずはレポート表示として追加し、
   閾値で落とすかは運用してから決める。
5. `okf lint --strict`（warn も exit 1）に上げるかは、[B-0004 okf new doc 直後に lint の warn が出ないようにする](/backlog/B-0004-new-doc-placeholder.md) の warn を潰してから判断する。

## 完了条件

- [ ] `docs/index.md` を古いままにしたプルリクで CI が落ちる
- [ ] `okf render --check` が CI で通る
- [ ] 影響ドキュメントを更新した（`okf affected` の出力）
- [ ] 該当層の `log.md` に追記した
- [ ] 本ファイルの `state` を `done` にし `done_at` を記入した

## 結果

<完了時に記入する。PR / コミットへのリンク、実際に変更したファイル、想定と違った点。>
