---
type: Backlog Item
title: okf-devkit 自身の docs バンドルに本文ドキュメントを書く
description: okf-devkit 自身のコードを対象に本文ドキュメントを書き、affected と stale が実際に効く状態にする。
tags: [shared]
status: stable
layer: shared
generated:
  by: "process:okf-cli"
  at: "2026-08-26T12:49:02Z"
state: todo
priority: high
effort: L
feasibility: B
ai: assisted
cost: false
created: "2026-08-26"
done_at: null
related:
  - /backlog/B-0002-ci-self-lint.md
---

# okf-devkit 自身の docs バンドルに本文ドキュメントを書く

## やりたいこと

このリポジトリの `docs/` に、`cli` / `render` / `scaffold` 各層の本文ドキュメントを揃える。
okf-devkit が売りにしている「コードとドキュメントの連動」を、まず自分のリポジトリで成立させる。

## 背景・現状

- `okf init` 直後の `docs/` にあるのは `index.md` / `log.md` / `AGENTS.md` / `CONVENTIONS.md` だけで、
  **`code_globs` を持つ本文ドキュメントが 1 件も無い**。
- `compute_affected()` は `code_globs` が空のドキュメントを無条件に読み飛ばす。`run_stale()` の
  outdated 判定も `code_globs` の最終コミット時刻と `generated.at` の比較なので、起点が無ければ
  何も検出しない。つまり現状の `okf affected` は「未カバー」の羅列しか出さない。
- 実装の説明は `README.md` に集約されているが、README は利用者向けの一枚ものであり、
  層ごとの更新検知には使えない（frontmatter を持たず、バンドル外にある）。
- 結果として、okf-devkit は自分の主要機能を自リポジトリで検証できていない。

## 進め方

1. 雛形は `okf new doc` で作る。例:

   ```bash
   okf new doc --layer cli --type "Architecture" --title "CLI の処理構造" --slug architecture
   ```

2. 最低限、次の 4 本を書く。

   | ファイル | type | `code_globs` |
   |---|---|---|
   | `docs/cli/architecture.md` | Architecture | `src/okf_devkit/cli.py` |
   | `docs/cli/commands.md` | Reference | `src/okf_devkit/cli.py` |
   | `docs/render/architecture.md` | Architecture | `src/okf_devkit/renderer.py` / `src/okf_devkit/assets/**` |
   | `docs/scaffold/reference.md` | Reference | `src/okf_devkit/scaffold/**` / `src/okf_devkit/defaults.yml` |

3. README を写経しない。コードから読み取れる事実だけを書き、利用者向けの導入文は README に残す。
4. `okf index --write` → `okf lint` → `okf affected --paths src/okf_devkit/cli.py` の順に確認し、
   変更パスから実際にドキュメントが逆引きされることを見る。

## 完了条件

- [ ] `cli` / `render` / `scaffold` の各層に `code_globs` を持つドキュメントが 1 本以上ある
- [ ] `okf affected --paths src/okf_devkit/cli.py` が対応ドキュメントを出力する（「未カバー」だけにならない）
- [ ] `okf lint` が error 0 / warn 0 で通る
- [ ] 影響ドキュメントを更新した（`okf affected` の出力）
- [ ] 該当層の `log.md` に追記した
- [ ] 本ファイルの `state` を `done` にし `done_at` を記入した

## 結果

<完了時に記入する。PR / コミットへのリンク、実際に変更したファイル、想定と違った点。>
