---
type: Backlog Item
title: PyPI 公開の準備をする
description: README が案内している pip install okf-devkit を実際に成立させるため、メタデータを直して公開手順を決める。
tags: [shared]
status: stable
layer: shared
generated:
  by: "process:okf-cli"
  at: "2026-08-26T12:49:03Z"
state: todo
priority: medium
effort: M
feasibility: C
ai: assisted
cost: false
created: "2026-08-26"
done_at: null
related: []
---

# PyPI 公開の準備をする

## やりたいこと

`okf-devkit` を PyPI に公開し、README の `pip install okf-devkit` が本当に動く状態にする。

## 背景・現状

- README の冒頭と「インストール」節は `pip install okf-devkit` を案内しているが、パッケージはまだ
  公開されていない（`version = "0.1.0"` / `Development Status :: 3 - Alpha`）。
- `pyproject.toml` の `[project.urls]` は Homepage / Repository とも
  `https://github.com/rintaro/okf-devkit` を指しているが、`git remote -v` の origin は
  `https://github.com/shirashu687/okf-devkit.git` である。**このまま公開すると PyPI のページに
  存在しない URL が載る。**
- リリース用のワークフローは無く、CI は `test` と `smoke` の 2 ジョブだけ。

## 進め方

1. `[project.urls]` を実際のリポジトリ URL に直す。
2. 配布名 `okf-devkit` が PyPI で空いているか確認する。
3. タグ（`v0.1.0`）を打ったときに build → publish する GitHub Actions を足す。
   PyPI の Trusted Publishing（OIDC）を使えば API トークンを Secrets に置かずに済む。
4. 公開前に、ビルド成果物から package_data が漏れていないことを実際に確認する。
   `defaults.yml` / `scaffold/**` / `assets/**` が入っていないと `okf init` が
   「scaffold が見つかりません」で落ちる。

   ```bash
   python -m build
   pip install dist/okf_devkit-0.1.0-py3-none-any.whl
   okf init --site-name Smoke   # 別ディレクトリで
   ```

5. 公開後、README のインストール手順を実態に合わせる（必要ならバッジを足す）。

## 完了条件

- [ ] `pyproject.toml` の URL が origin と一致している
- [ ] タグ打ちで publish される GitHub Actions がある
- [ ] クリーンな環境で `pip install okf-devkit` → `okf init` → `okf lint` が通る
- [ ] 影響ドキュメントを更新した（`okf affected` の出力）
- [ ] 該当層の `log.md` に追記した
- [ ] 本ファイルの `state` を `done` にし `done_at` を記入した

## 結果

<完了時に記入する。PR / コミットへのリンク、実際に変更したファイル、想定と違った点。>
