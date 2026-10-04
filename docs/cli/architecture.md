---
type: Architecture
title: CLI の処理構造
description: 設定と Markdown を読み込み各コマンドへ渡す Python CLI の構造。
tags: [cli, implementation]
status: stable
layer: cli
generated:
  by: codex/gpt-6
  at: 2026-10-04T10:30:21Z
code_globs:
  - tests/test_config.py
  - tests/test_doc.py
  - src/okf_devkit/config.py
  - src/okf_devkit/doc.py
  - src/okf_devkit/cli.py
  - src/okf_devkit/yamlio.py
  - src/okf_devkit/errors.py
  - src/okf_devkit/fsutil.py
  - tests/test_cli_context.py
  - tests/test_fsutil.py
related:
  - /cli/commands.md
  - /cli/node-runtime.md
---

# CLI の処理構造
第3段階では frontmatter の所有者を `doc.py`、設定マージとBundle探索の所有者を `config.py` に分離した。canonical Doc/Bundle は `repo_root` を明示的に受け、Bundleの `.repo_root` はプロジェクトroot、`.root` は設定された文書rootを示す。文書cacheとrepo相対パスは構築時のrootに固定する。モデルはGitやcliをimportしない。旧 `cli.Doc(path, bundle_root)` と `cli.Bundle(config_path)` は一時的なsubclass adapterで保持し、CLI経由のDoc型とrenderer callbackも維持する。YAMLの実行所有者と同梱defaults位置は変わらない。


Issue #12 の最初の分割では、共通例外を `errors.py`、rootに依存しないファイル・日付・glob処理を `fsutil.py` へ移す。従来のcliシンボルは同じ関数・例外classを再exportし、glob cacheも同じオブジェクトを参照する。rootはcliが所有し、Git時刻cacheは現在のrootが変わると再取得する。同じrootへのmain再呼出しでもcacheを更新し、途中に追加されたコミットを反映する。

Python のエントリーポイントは `run()` → `main()`。`build_parser()` が引数を解釈し、`resolve_root()` がプロジェクトルートを決める。`init` は Bundle を作る前に処理し、それ以外は Bundle の存在を確認して `cmd_*` に振り分ける。

`--help` と各サブコマンドのhelpは引数・用途・実行例を表示し、設定読取やBundle構築より前に終了する。`new --help` はkind一覧、`new doc --help` / `new backlog --help` は各操作の引数を示す。Python/Nodeのhelpと非書込みを共通入力で検証する。

## 設定と文書モデル

第2段階ではparser・内蔵YAML subset・scalar/flow serializerを `yamlio.py` へ移す。通常のDoc/frontmatterとBundle/configは `yamlio.parse_yaml` を呼び、現在の `yamlio._pyyaml` がbackendを決める。旧 `cli.parse_yaml` は旧 `cli._pyyaml` を明示backendとして渡す互換アダプターなので、直接呼出しの差替えと通常経路の所有者を区別する。例外・serializer・内蔵parserの旧cli名前は同じ実装を再exportする。

`--root`、`--config` の親、自動探索の順でルートを決める。自動探索は最も近い `okf.yml` を優先し、Git のトップディレクトリへフォールバックする。`load_merged_config()` は同梱 `defaults.yml` とプロジェクト設定を合成する。辞書は再帰マージし、リストとスカラーは置き換える。

`Bundle` はバンドル配置、設定、Markdown の列挙を担う。`Doc` は frontmatter と本文を解析する。予約文書 index/log の扱いと除外ディレクトリはコマンドの用途に応じて Bundle の列挙オプションを使う。

## 更新と検査

| 処理 | 入口と根拠 |
|---|---|
| index | `_plan_index()` が生成内容を計画し `cmd_index()` が表示・書込・差分検査を選ぶ |
| lint | `run_lint()` が Finding を集め、`cmd_lint()` が終了値を決める |
| affected | `changed_paths()` または明示パスを `compute_affected()` の `code_globs` 照合へ渡す |
| stale | `run_stale()` が期日、検証情報、コード最終更新時刻を調べる |
| render | `cmd_render()` が renderer を遅延 import して Bundle と Doc を渡す |

`affected` は `code_globs` のない文書を逆引き対象にしない。`layer_map` は未カバーのパス分類にも使う。Git 履歴を参照する log/stale は履歴の深さに依存する。

## エラーと hook

通常の `OkfError` は標準エラーへ表示し exit 1。`sync --gate` は初回のlint errorでexit 2、同じerror集合の再検出ではexit 0になり得る。終了値だけをlint合格判定にしない。gate の状態はユーザーのキャッシュ領域に置き、セッション識別子と指摘の fingerprint を使う。HTML の Stop hook 入口は `render --hook` で、成功時は空の JSON を返す。

Node の独立実装と対応範囲は [Node ランタイム](/cli/node-runtime.md) を参照する。
