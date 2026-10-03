---
type: Architecture
title: CLI 分割の移行設計
description: Python CLI の可変状態とテスト互換性を守る段階的なモジュール分割案。
tags: [cli, migration]
status: draft
layer: cli
generated:
  by: codex/gpt-6
  at: 2026-10-03T00:11:38Z
code_globs:
  - src/okf_devkit/cli.py
  - src/okf_devkit/renderer.py
  - tests/helpers.py
  - tests/test_yaml.py
related:
  - /cli/node-runtime.md
---

# CLI 分割の移行設計

この文書は Issue #12 の事前調査と技術設計であり、モジュール分割の実装完了を表さない。CLI の引数・終了値・生成結果と Python/Node の互換性を維持し、純粋な処理から順に移す。

## 現状の依存とテスト面

調査対象 main の `9d72e0e5798883d81789582d8879f139865d37b5` では cli.py は2922行。ASTで `REPO_ROOT` の Name 参照を27件、tests/*.py の `okf.<名前>` を49種類確認した。件数はこの版の測定値であり、分割の完了判定はIssueの行数と振る舞い条件を使う。

| 可変状態 | 現在の所有者・呼出し | 分割で守ること |
|---|---|---|
| REPO_ROOT | cli.main が確定し、helpers が直接代入・復元 | 別モジュールへの値コピーを禁止し、現在のルートを明示的に渡す |
| _pyyaml | cli.parse_yaml が参照、helpers/test_yaml が差替え | パーサ実行時の所有者を差し替え、内蔵経路が実際に走ることを確認 |
| _PATH_TIME_MAP | Git履歴時刻のキャッシュ、helpers が None に戻す | 根の切替えで前リポジトリのキャッシュを引き継がない |
| _GLOB_CACHE | glob変換キャッシュ、helpers が clear | 移動先の同じオブジェクトを参照し、コピーを作らない |
| DEFAULTS_PATH / SCAFFOLD_DIR | 同梱素材の絶対位置 | CWDや利用者ルートではなくパッケージ位置から解決 |

Doc/Bundle は単なるデータではなく設定・ファイル読取・YAML処理に依存する。Git helpers はルートと時刻キャッシュに依存する。Issueの依存図を形式的な一列として実装せず、モデルとGit処理を相互importさせない。

## 小さい変更単位

| 段階 | 新しい module / interface | 単独で確認する結果 |
|---|---|---|
| 0 | 現在のcliのまま、根指定とYAML切替えの回帰条件を固定 | 二つの異なる一時ルート、非CWDからの--root/--config、連続main呼出しが対象を取り違えない |
| 1 | errors.py と純粋fsutil。日付・glob・atomic writeはpathを受ける | 同じ例外classをcliから再export。write-if-changedとWindows共有違反処理を維持 |
| 2 | yamlio.py、parse_yaml(text, source)、yaml_scalar(value) | test_yamlの差替えをyamlioへ移し、同じ入力で両backend一致と内蔵の拒否経路を確認 |
| 3 | doc.py / config.py。Bundleへrootを渡す | プロジェクト設定、素材位置、除外、frontmatter、予約文書を維持 |
| 4 | gitutil.py。rootと必要なcacheを呼出しから渡す | log/stale/affectedの結果・時刻・rename/特殊名解析を維持 |
| 5 | commands/index, log, lint, stale, affected, new, status, render, sync, init | 一コマンドずつ移し、同じCLI出力・終了値・ファイル差分を確認 |
| 6 | cli.py は引数解釈と入口、互換exportのみ | 200行以下、Python全件とNode互換、根指定・YAML不在経路を最終確認 |

各段階は独立commit/PRで必要テストを通してから次へ進む。初回から大量のシンボルを移動したり、共通contextへすべての設定を詰め込んだりしない。CLIの公開入口 `main` / `run` と既存の呼出し用シンボルの再exportを維持する。

## ルートと互換exportの移行

`from module import REPO_ROOT` による参照は採用しない。初回はルート所有者をcliに残し、切り出し側へ `Path` を引数で渡す。Bundleはrootを保持し、その操作はBundleのrootに従う。rootを必要とする既存cli関数は、現在の `cli.REPO_ROOT` を読み、移動先へ渡す薄い互換adapterとして一時的に残す。これによりhelpersの `okf.REPO_ROOT = ...` が突然無効になることを防ぐ。

commands移動時は `main` が解決したrootをBundle/必要なinterfaceへ渡す。キャッシュはroot別、またはroot変更時に確実に初期化し、二つのルートの連続処理で検証する。最終的な所有場所の変更は互換adapterとテスト移行を同じ変更単位にする。入口の200行条件はparserとexportの実測により確認し、行数だけを減らす圧縮はしない。

## YAMLの差替えが空振りしない確認

yamlioへ移した関数のglobalsはyamlioを指す。cliから関数を再exportするだけでは `okf._pyyaml = None` は効かない。テストは実行する所有者 `yamlio._pyyaml` を差し替える。Doc/config経由のlintも同じ所有者を使うようにする。

移行中に旧cli経由の直接呼出しを残す場合、互換 `cli.parse_yaml` は旧 `_pyyaml` の値を明示してparserへ渡すadapterとし、通常経路とtest seamを区別する。Doc/Bundleのテストは移動先所有者を差し替える。backendとして明示した None と省略（既定backend）を区別するsentinelが必要になる場合だけ導入する。

差替え確認では内蔵経路の呼出し観測も行い、単に期待結果が一致するだけで成功としない。PyYAMLが実際にない環境でも同じ拒否構文・frontmatter処理を確認する。例外の型とメッセージが呼出し先ごとに変わらないことも確認する。

## 先行変更との統合順

未統合 `origin/shirashu687/npm` はmainより14commit先でcli/initとscaffold、testsへ変更を持つ。#6/#7/#11/#17 のコマンド変更と #4 の実装本文も進行している。大きいcommands移動はこれらの統合順が確定した後に行う。純粋helpersの先行切出しでも、開始時に最新baseとnpm差分を再確認する。

この設計段階では実行コード・配布設定・公開方針・hook設定を変更しない。Node移植は行わず、Python移動後も既存の `npm run test:compat` で対応出力を確認する。新ファイルは現行 `src/okf_devkit/**` → cli のlayer_mapで分類できる。分割ごとに `okf affected` の結果を更新し、#4の本文code_globsへ移動先を加え、層ログを残す。
