---
type: Backlog Item
title: Python 以外の実行環境からも使えるようにする
description: Python が入っていないリポジトリでも okf を使えるよう、配布方式を決めて用意する。
tags: [shared, scaffold]
status: stable
layer: shared
generated:
  by: "process:okf-cli"
  at: "2026-09-10T14:28:26Z"
state: done
priority: medium
effort: L
feasibility: C
ai: assisted
cost: false
created: "2026-08-26"
done_at: "2026-09-10"
related:
  - /backlog/B-0005-pypi-release.md
  - /project/decisions/0001-node-runtime.md
  - /cli/node-runtime.md
---

# Python 以外の実行環境からも使えるようにする

## やりたいこと

Python 環境を前提にしないインストール手段を用意する。TypeScript / Node のリポジトリで、
ドキュメントツールのためだけに Python を入れさせたくない。

## 背景・現状（起票時）

- 実装は Python 専用。`pyproject.toml` は `requires-python = ">=3.11"`、依存は
  `markdown-it-py` と `pyyaml` の 2 つ。
- 想定している配布経路は PyPI 一本（[B-0005 PyPI 公開の準備をする](/backlog/B-0005-pypi-release.md)）で、
  利用者は `pip install okf-devkit` するしかない。
- `.okf/hooks/render_hook.sh` は okf を次の順で探す ——
  `<repo>/.venv/bin/okf` → `.venv/Scripts/okf.exe` → 主ワークツリー側の `.venv` →
  `python -m okf_devkit` → PATH 上の `okf` / `python3` / `python`。
  **探索経路が全て Python 前提**なので、別ランタイムを足すならこのラッパーも直す必要がある。
- 一方このツールが対象にしているのは「コードとドキュメントの連動」であり、対象リポジトリの
  言語は問わない。JS / TS リポジトリでこそ使いたいのに、そこに Python 依存を持ち込むのは
  導入の障壁になる。

## 進め方（起票時の比較）

まず配布方式を決める。**実装を 2 つ持つかどうか**が分かれ目。

| 案 | 内容 | 長所 | 短所 |
|---|---|---|---|
| A | npm パッケージが GitHub Releases の単体バイナリ（PyInstaller / Nuitka）を取得する | 実装は 1 つのまま。`npx okf` で動く | OS × arch 分のビルド CI が要る。配布サイズが数十 MB |
| B | TypeScript へ全面移植する | Node にネイティブ。npm だけで完結 | **実装が 2 つになる。**出力バイト列が完全一致しないと `index --check` / `render --check` が環境ごとに割れる |
| C | 配布は PyPI のままにし、`uvx okf` / `pipx run okf` を案内する | 追加実装ゼロ。Python 本体の取得は uv が面倒を見る | 利用者に uv / pipx を求める。Node 一色のチームには依然「別世界」 |

1. まず C を README に書いて当面の導入障壁を下げる（コスト 0）。ただし PyPI 公開が前提。
2. 本命は A。`okf` という**コマンド名を変えない**ことが重要で、hook ラッパーもエージェント設定も
   コマンド名で書かれている。
3. B は採らない方向で検討する。`index` / `log` / `lint` の出力が 1 バイトでも揺れると
   `--check` 系が CI で割れるため、採るなら 2 実装で共有する golden test の仕組みが先に要る。
4. どの案でも `.okf/hooks/render_hook.sh` / `.ps1` の探索順に候補を足す
   （`node_modules/.bin/okf`、`npx --no-install okf` など）。scaffold 側の変更なので、
   既に配布済みの hook を更新する手順も要る。
5. 決定は Decision Record に残す。

   ```bash
   okf new doc --layer shared --type "Decision Record" --title "Python 以外の配布方式" --slug distribution
   ```

## 2026-09-10の決定

起票時のA案優先・B案回避は、利用者によるNode.js実装の追加選択で置き換えた。
[決定記録](/project/decisions/0001-node-runtime.md)に従いJavaScriptの独立実装を追加し、
設定・scaffold・HTMLアセットを共有して、Node単独テストとPython版との生成内容比較を行う。
`okf`というコマンド名を維持し、既存hookを2ファイルだけ更新する手順も案内する。
なお `render --check` は生成可能性の検査であり、HTMLの保存済みバイト列との比較ではない。

## 完了条件

- [x] 配布方式の決定が Decision Record として残っている
- [x] Python を入れていない環境で `okf lint` が実行できる（PATHからPythonを除いたテスト）
- [x] `.okf/hooks/` のラッパーが新しい実行経路を見つけられる
- [x] 影響ドキュメントを更新した（`okf affected` の出力）
- [x] 該当層の `log.md` に実コミットハッシュ付きエントリを生成した
- [x] 本ファイルの `state` を `done` にし `done_at` を記入した

## 結果

`node/*.mjs`、`package.json`、`package-lock.json` と `tests/node/*.mjs` を追加し、共有hookを更新した。
READMEと[利用手順](/cli/node-runtime.md)からチェックアウト・tgz導入・既存hook更新を辿れる。
`npm pack` の配布物を別ディレクトリへオフラインインストールし、init → index → lint → renderを実行した。
新実装はPythonを取得・起動しない。比較テストの開発環境にはPythonが必要。npmレジストリへの公開は未実施。
実装コミット `41f58f1` の後に `okf log --write` を実行し、cli・render・scaffoldの3層へハッシュ付きエントリを生成した。
