---
type: Reference
title: 初期化と同梱雛形
description: init が配置するファイルと既定設定の合成ルール。
tags: [scaffold, implementation]
status: stable
layer: scaffold
generated:
  by: codex/gpt-6
  at: 2026-10-04T09:57:43Z
code_globs:
  - src/okf_devkit/gitutil.py
  - tests/test_gitutil.py
  - src/okf_devkit/scaffold/**
  - src/okf_devkit/defaults.yml
  - src/okf_devkit/cli.py
  - src/okf_devkit/yamlio.py
  - node/scaffold.mjs
related:
  - /cli/commands.md
---

# 初期化と同梱雛形

第4段階ではGit helperを `gitutil.py` に分離したが、initと同梱scaffold生成は従来入口に残る。生成したプロジェクトのGit呼出しはproject rootを明示して処理し、文書rootをGitのcwdには使わない。
Doc/config分離後もdefaultsはパッケージ内の `defaults.yml`、scaffoldは同梱の `scaffold/` を参照する。利用先のCWDや文書rootから配布素材を探さない。initの引数・生成先・既存ファイル保持は変更しない。


CLIの純粋helpers分離後も、initの配置物・設定と同梱素材の解決位置は維持する。素材位置はパッケージから解決し、現在のCWDや利用者rootへ移さない。

Python の `cmd_init()` は `src/okf_devkit/scaffold/` の素材からプロジェクトへファイルを配置する。Node の対応処理は `node/scaffold.mjs` にある。雛形素材と `defaults.yml` は両ランタイムが共有する。

## 配置物

| 素材・生成処理 | 出力 |
|---|---|
| okf.yml.tmpl と設定生成処理 | ルートの `okf.yml` |
| AGENTS.md.tmpl / CONVENTIONS.md.tmpl | バンドル内の作業入口と執筆規約 |
| templates/*.md | バンドルの `_templates/` |
| hooks/* | ルートの `.okf/hooks/` |
| 層定義と empty_log | 各層の log と shared 用 log |

`--bundle-root` は既定 docs で、プロジェクト内の相対パスへ制限する。`--site-name` の既定はルート名。`--layer NAME=GLOB[:DIR]` を複数指定して層・コード配置・文書配置を対応させる。既存ファイルは通常スキップし、`--force` を指定した場合だけ置き換える。

init は本文ドキュメントや目次を完成させない。配置後に語彙と layer_map を確認し、`okf new doc` で本文を作り、`okf index --write` と lint を実行する。hooks はリポジトリへ置くのみで、グローバルなエージェント設定への自動登録は行わない。

## 既定設定

`defaults.yml` は type/status、backlog の語彙、目次マーカー、commit kind 等の共通規則を持つ。プロジェクトの okf.yml は辞書を再帰的に上書きし、リスト・スカラーを丸ごと置換する。語彙変更時は CONVENTIONS.md と一致させる。

shared のログ出力先は設定の `log.paths.shared` で決まる。生成雛形の配置を変更する場合は、この設定と実際の配置が一致するかを確認する。

## YAML serializerの所有者

newのfrontmatterに埋め込むscalar/flow値は `yamlio.py` のserializerを使い、旧cli関数名は同じ実装の再exportとして残す。引用・改行拒否・空配列などの生成結果とscaffold素材はこの移動で変えない。生成後のDoc/config解析も通常はyamlio backend ownerを使う。
