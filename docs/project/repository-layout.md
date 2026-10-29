---
type: Architecture
title: リポジトリのフォルダ構成
description: 二つのCLI実装と共有資産、互換入口、開発用処理の配置と理由を説明する。
tags: [architecture, development]
status: stable
layer: shared
generated:
  by: codex/gpt-6
  at: 2026-10-29T13:30:00Z
code_globs:
  - src/node/*.mjs
  - src/okf_devkit/**
  - node/cli.mjs
  - scripts/*.mjs
  - tests/node/*.mjs
  - pyproject.toml
  - package.json
related:
  - /cli/architecture.md
  - /cli/node-runtime.md
  - /project/decisions/0001-node-runtime.md
  - /agents/release-node.md
---

# リポジトリのフォルダ構成

## 実装と開発用処理

| 配置 | 所有する処理 |
| --- | --- |
| `src/node/` | Node.js版のCLI、モデル、各コマンド、HTML生成 |
| `src/okf_devkit/` | Python版のCLI、モデル、各コマンドと共有資産 |
| `node/cli.mjs` | Node CLIへの互換入口。mainの再公開と直接起動だけを行う |
| `scripts/` | tgz検査・隔離インストール、CI配布物、Releaseの作成・検査処理 |
| `tests/` | Pythonの既存テストと実行入口 |
| `tests/node/` | Node単独テスト、Python比較、Release guard、配布・復旧テスト |
| `docs/` | このリポジトリのOKFバンドル |
| `harness/` | 開発エージェントの運用設定と作業記録 |

Pythonの `src/okf_devkit/` はsetuptoolsのsrc layout。プロジェクト名・配布名は `okf-devkit`、import名は `okf_devkit` である。
`pyproject.toml` のpackage discoveryは `okf_devkit` とそのサブパッケージに限定する。隣の `src/node/` をPython namespace packageとして配らない。

Node本体は `src/node/` に置く。npmのbinと既存README・hookが参照する `node/cli.mjs` は維持する。
この入口にコマンド処理を追加せず、修正は `src/node/` に行う。
旧 `node/core.mjs` 等の内部モジュールは移動しているため、開発時の内部importも新配置を使う。

## 似て見えるファイルの意図

| 対象 | 理由と編集先 |
| --- | --- |
| PythonとNodeの同名コマンド | [ADR 0001](/project/decisions/0001-node-runtime.md)に基づく独立実装。Pythonなしでの利用とPython利用を両立する。仕様変更は両方へ反映し、比較テストで主要出力を照合する |
| Pythonのcli.pyとcommands等の同名関数 | cli.pyは旧import・constructor・注入状態を維持する入口。compat.pyがadapterを登録し、実処理はcommands等が所有する。[CLI構造](/cli/architecture.md)を参照 |
| ルート・docsの文書とscaffold内のAGENTS等 | 前者はこのプロジェクト用、scaffoldはinitで利用先へ渡す雛形。変更する利用者を確認して編集する |
| render_hook.shとrender_hook.ps1 | POSIXとWindows用。配布元はscaffold/hooks、.okf/hooksはこのリポジトリへ導入したコピー。利用先の編集済みコピーを自動上書きしない |
| docs/_templatesとscaffold/templates | このバンドルで使うテンプレートと、initで導入先へ配るテンプレート。導入先を変えるときはscaffoldを更新する |

## 共有資産と配布

`src/okf_devkit/defaults.yml`、`scaffold/`、`assets/` は1組だけ存在し、両実装で共有する。
Pythonはパッケージ内の資産として読み、Nodeはcore.mjsのdataDirから同じ実体を参照する。
npmのfiles一覧には互換入口・Node本体・共有資産を収録し、Python本体や開発用scripts/testsは収録しない。
Python wheelはPython本体とpackage-dataを収録する。

共有資産だけをルートのresourcesへ移すとPython wheelのデータ配置と参照方式も変わるため、今回は現在の配置を維持する。
二重実装や旧APIの廃止、独立resources化を進める場合は、用途・代替・移行期間と両配布物での検証を先に決める。
構成整理の方針・受入条件は[Issue #58](https://github.com/shirashu687/okf-devkit/issues/58)、機能削減は親の[Issue #15](https://github.com/shirashu687/okf-devkit/issues/15)で管理する。
