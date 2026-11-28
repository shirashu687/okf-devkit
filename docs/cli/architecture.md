---
type: Architecture
title: CLI の処理構造
description: 設定と Markdown を読み込み各コマンドへ渡す Python CLI の構造。
tags: [cli, implementation]
status: stable
layer: cli
generated:
  by: codex/gpt-6
  at: 2026-10-04T11:43:53Z
code_globs:
  - src/okf_devkit/compat.py
  - src/okf_devkit/parser.py
  - tests/test_cli_facade.py
  - src/okf_devkit/commands/stale.py
  - src/okf_devkit/commands/affected.py
  - src/okf_devkit/commands/new.py
  - src/okf_devkit/commands/status.py
  - src/okf_devkit/commands/render.py
  - src/okf_devkit/commands/sync.py
  - src/okf_devkit/commands/init.py
  - src/okf_devkit/commands/setup_checks.py
  - tests/test_commands_b.py
  - src/okf_devkit/commands/__init__.py
  - src/okf_devkit/commands/index.py
  - src/okf_devkit/commands/log.py
  - src/okf_devkit/commands/lint.py
  - tests/test_commands_context.py
  - src/okf_devkit/gitutil.py
  - tests/test_gitutil.py
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
  - /cli/module-migration.md
  - /cli/node-runtime.md
---

# CLI の処理構造

`cli.py` は引数解析を `parser.py` に委ね、プロジェクトルートを決めて `commands/` の各処理を呼ぶ。`compat.py` は旧 API を提供する。共通の例外は `errors.py`、ファイル・日付・glob の処理は `fsutil.py` にある。Issue #12 でこれらの処理を分割した際の経緯は移行記録を参照する。[モジュール分割の記録](/cli/module-migration.md)

コミット履歴や変更パス、ファイルの更新時刻を調べる処理は `gitutil.py` にある。呼び出し元がプロジェクトルートを渡し、`CommitTimesCache` を管理する。`main()` を再度呼ぶと Git の時刻キャッシュを初期化するため、同じリポジトリでも新しいコミットを参照できる。

Python のエントリーポイントは `run()` → `main()`。`build_parser()` が引数を解釈し、`resolve_root()` がプロジェクトルートを決める。`--version` はルート探索前に終了する。`init` は Bundle を作る前に処理し、`doctor` は設定や Bundle の不備も診断する。他のコマンドは Bundle を確認して `cmd_*` に振り分ける。

`--help` と各サブコマンドのhelpは引数・用途・実行例を表示し、設定読取やBundle構築より前に終了する。`new --help` はkind一覧、`new doc --help` / `new backlog --help` は各操作の引数を示す。Python/Nodeのhelpと非書込みを共通入力で検証する。

## 設定と文書モデル

第2段階ではparser・内蔵YAML subset・scalar/flow serializerを `yamlio.py` へ移す。通常のDoc/frontmatterとBundle/configは `yamlio.parse_yaml` を呼び、現在の `yamlio._pyyaml` がbackendを決める。旧 `cli.parse_yaml` は旧 `cli._pyyaml` を明示backendとして渡す互換アダプターなので、直接呼出しの差替えと通常経路の所有者を区別する。例外・serializer・内蔵parserの旧cli名前は同じ実装を再exportする。

`--root`、`--config` の親、自動探索の順でルートを決める。自動探索は最も近い `okf.yml` を優先し、Git のトップディレクトリへフォールバックする。`load_merged_config()` は同梱 `defaults.yml` とプロジェクト設定を合成する。辞書は再帰マージし、リストとスカラーは置き換える。

`config.py` の `Bundle` は設定を読み込み、バンドルの Markdown を列挙する。`.repo_root` はプロジェクトルート、`.root` は文書ルートを指す。`doc.py` の `Doc` は frontmatter と本文を読み込む。`index.md`、`log.md`、除外ディレクトリを列挙に含めるかどうかは、各コマンドが指定する。OKF 0.3 かどうかの判定には、バンドルルートの `index.md` の版宣言を使う。

## 更新と検査

| 処理 | 入口と根拠 |
|---|---|
| index | `commands/index.py` の `_plan_index()` が生成内容を計画し `cmd_index()` が表示・書込・差分検査を選ぶ |
| log | `commands/log.py` が明示project rootでGit履歴を集め、baselineと記録済みhashを照合する |
| lint | `commands/lint.py` の `run_lint()` が Finding を集め、`cmd_lint()` が終了値を決める |
| affected | `changed_paths()` または明示パスを `compute_affected()` へ渡し、ソース名が一致する `code_globs` と照合する |
| stale | `run_stale()` が期日、検証情報、ローカルコードの最終更新時刻を調べ、外部コードの更新時刻を未検証と表示する |
| render | `commands/render.py` が renderer/cleanup を遅延 import し、同じ project root に束縛した Doc factory を渡す |

ローカルの `affected` は `layer_map` で変更パスを絞り、接頭辞なしの `code_globs` と照合する。`--source` を選んだ場合は、そのコードソースの作業ツリーと Git 履歴から変更を集める。外部用の比較で基準を特定できない場合は「差分未確認」を警告する。Git 履歴を参照する `log` とローカルコードの `stale` 判定も履歴の深さに依存する。 [外部コードソースの利用方法](/cli/commands.md)

## エラーと hook

通常の `OkfError` は標準エラーへ表示し exit 1。`sync --gate` は初回のlint errorでexit 2、同じerror集合の再検出ではexit 0になり得る。終了値だけをlint合格判定にしない。gate の状態はユーザーのキャッシュ領域に置き、セッション識別子と指摘の fingerprint を使う。HTML の Stop hook 入口は `render --hook` で、成功時は空の JSON を返す。

Node の独立実装と対応範囲は [Node ランタイム](/cli/node-runtime.md) を参照する。

## 旧APIの互換入口

`compat.install_legacy_exports(ns)` は型と引数形を保った名前付きadapterをnamespaceへ登録する。root、YAML backend、Git cache、gate TTL、素材の場所、writerやDoc factoryは呼び出し時にnamespaceを読む。cacheの更新も同じnamespaceへ戻し、別のnamespaceを登録しても状態を混ぜない。通常のmodels/Git/commandsは明示rootを受け、旧CLIを参照しない。

DocとBundleはCLIのトップレベルclassとして残し、旧import名とpickleのlookupを維持する。adapterのmodule/nameも登録先に合わせる。型注釈は登録時の実際のDoc/Bundle等で解決し、`typing.get_type_hints` の意味を保つ。従来のfuture annotation文字列は型objectへ解決されるため、注釈そのものの表示形式は変わるが、引数名・順序・default・kindと解決後の型は維持する。parserはproject stateや書き込みに依存せず、`build_parser`、`main`、`run` は旧入口として利用できる。
