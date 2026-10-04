---
type: Reference
title: 初期化と同梱雛形
description: init が配置するファイルと既定設定の合成ルール。
tags: [scaffold, implementation]
status: stable
layer: scaffold
generated:
  by: codex/gpt-6
  at: 2026-10-04T10:20:56Z
code_globs:
  - src/okf_devkit/scaffold/**
  - src/okf_devkit/defaults.yml
  - src/okf_devkit/cli.py
  - src/okf_devkit/yamlio.py
  - node/scaffold.mjs
related:
  - /cli/commands.md
---

# 初期化と同梱雛形

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

## 配布する日常操作案内

生成するAGENTSは目的からコード変更後・新規文書・読み取り点検・閲覧・初回導入・backlogへ案内する。詳細なコマンド仕様は上流の参照表へ接続し、版差は利用するCLIのhelpと照合する。`affected`未カバーとバンドル外文書の影響、syncの書き込み/logスキップ、stale/gateの終了0の限界を明示する。ローカルNodeの実CLIを優先し、利用者の既存案内は通常initで保持する。開発者向けharnessを利用先へコピーしない。

## 既定設定

`defaults.yml` は type/status、backlog の語彙、目次マーカー、commit kind 等の共通規則を持つ。プロジェクトの okf.yml は辞書を再帰的に上書きし、リスト・スカラーを丸ごと置換する。語彙変更時は CONVENTIONS.md と一致させる。

shared のログ出力先は設定の `log.paths.shared` で決まる。生成雛形の配置を変更する場合は、この設定と実際の配置が一致するかを確認する。

## YAML serializerの所有者

newのfrontmatterに埋め込むscalar/flow値は `yamlio.py` のserializerを使い、旧cli関数名は同じ実装の再exportとして残す。引用・改行拒否・空配列などの生成結果とscaffold素材はこの移動で変えない。生成後のDoc/config解析も通常はyamlio backend ownerを使う。
