---
type: Reference
title: コマンド仕様
description: PythonとNode CLIのコマンドごとの入出力と検査モードの仕様。
tags: [cli, implementation]
status: stable
layer: cli
generated:
  by: codex/gpt-6
  at: 2026-10-04T11:43:53Z
code_globs:
  - src/node/cli.mjs
  - src/okf_devkit/compat.py
  - src/okf_devkit/parser.py
  - src/okf_devkit/code_sources.py
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
  - src/node/*.mjs
  - .github/workflows/ci.yml
related:
  - /cli/architecture.md
  - /render/architecture.md
  - /scaffold/reference.md
  - /agents/operate-okf.md
  - /project/decisions/0003-external-code-sources.md
---

# コマンド仕様

例の `okf` は導入済みの CLI に読み替える。Python 版と Node.js 版に共通する書き方は、`--root` と `--config` をサブコマンドの前に置く。引数の一覧は `okf <command> --help`、文書の新規作成は `okf new doc --help`、backlog の新規作成は `okf new backlog --help` で確認できる。[AI の日常操作](/agents/operate-okf.md)

Python 版の引数解析、コマンドへの振り分け、Git や文書モデルの処理については [CLI の処理構造](/cli/architecture.md) を参照する。

| コマンド | 入力・結果 | 書き込み条件 |
|---|---|---|
| init | バンドル、設定、テンプレートを初期配置。`--agent` で hook を選び、`--runner` で案内の起動表記を選ぶ | 既存ファイルは通常スキップ。エージェント設定と `.gitignore` は `--force` でも保持 |
| --version | 実行中のパッケージの版を表示 | なし。プロジェクト設定は不要 |
| doctor | CLI の実体と版、設定、層の glob、hook 登録、Git 除外、旧 HTML 候補を表示 | なし。設定や層の定義を読めなければ exit 1 |
| upgrade --check | 現行の層・サイト名・配置を使って、配布 scaffold に対する一致・追加候補・差分を表示 | なし。差分があっても exit 0、比較できない対象があれば exit 1 |
| index | frontmatter から各階層の目次を計画 | `--write`。`--check` は差分があれば exit 1 |
| log | Git のコミットを層別履歴へ変換 | `--write`。`--range` / `--layer` で範囲を限定 |
| lint | OKF の書式を検査。0.3 でプロジェクト固有の規約も検査する場合は `--project` を指定 | なし。エラーで終了コード 1。`--strict` は警告も対象 |
| stale | 期日・コード更新・検証状態のレポート | なし。指摘があっても exit 0 |
| affected | `--base` との差分または `--paths` を文書へ逆引き。外部リポジトリは `--source <name> --base <ref>` を使う | なし。対応文書と未カバーのパスを表示 |
| new doc | layer/type/title とテンプレートから文書を作る。`--code-globs` は複数指定可 | 新規 Markdown。`--index` を指定した場合は索引も更新 |
| new backlog | タイトルと優先度等から backlog 文書を作る | 新規 Markdown。`--index` を指定した場合は索引も更新 |
| status | backlog の state を集計 | なし。text/json 出力 |
| render | Markdown とアセットから HTML を作る。`--open` は生成先のトップページを開く | 既定は `_site/`。`--output docs` で従来の隣接配置を指定。`--check` / hook 時はブラウザを起動しない |
| sync | index → log → lint → stale をまとめて実行 | index/log 更新。log失敗は警告で継続し得る。`--gate` は差戻し判定で状態を書き込む |

## 結果と書き込みの境界

`affected` は対応文書に加えて未カバーパスも読む。`code_globs` がない文書とバンドル外のREADME等は自動逆引きの保証外なので、変更内容から別途確認する。
初回コミット前は作業ツリーを調べ、`log` は追記をスキップする。`main` がない場合は実在する基準の SHA を `affected --base` へ指定するか、`affected --paths src/main.js` のように変更を渡す。
`sync` のlogはGitのコミット済み履歴だけを扱う。未コミット変更はlogに記録せず、logの警告・スキップを確認する。index更新や最終exit0からlog追記成功を推定しない。

`sync` で、同じ文書の接頭辞なし `code_globs` に一致するファイルがなく、`lint` の L10 と `stale` の orphan が重なる場合は、行番号付きの L10 を lint 欄に1件表示する。単独の `lint` と `stale` では、それぞれの診断を確認できる。名前付き外部コードソースの更新時刻が未検証の場合は stale 欄に表示する。

`stale` の指摘と `sync --gate` の同じlint error再検出はexit0になり得る。gateは初回errorでexit2、同一error集合の再検出ではexit0としてループを抑える。指摘が解消したことやCI成功を意味しない。
`render --hook` はHTMLを書き込み、成功時 `{}` / exit0、失敗時exit1。モデル継続のblock判定は返さない。終了イベント用advisory adapterは失敗をstderrへ出してexit0にするため、そのexit0を生成成功の証拠にしない。
`init --force` は既存の OKF 設定、文書やhookスクリプトを置換する。エージェント設定と `.gitignore` は例外で、常に保持する。設定の部分更新や新しい案内の移行に使わず、既存ファイルとの必要な差分だけを確認して更新する。初回導入時の登録と既存設定への追加は [終了hookの手順](/agents/completion-hooks.md) を参照する。

`upgrade --check` は生成ガイドの frontmatter の生成時刻を比較から除き、来歴が分からない差分をファイル単位で手動確認として表示する。必要な変更は配布 scaffold と照合する。hook と Git 除外の追記箇所は [終了hookの手順](/agents/completion-hooks.md) を参照する。既存の初期化で `--runner` や `--agent` を指定した場合は、比較時にも同じ値を渡せる。`doctor` の hook 診断は設定の読み取り結果で、実行環境の確認には製品側のイベント検証を使う。

## 外部リポジトリのコードを参照する

文書プロジェクトの `okf.yml` に外部コードソースを登録する。`path` は作業ツリーのルートを指定する。相対パスは文書プロジェクトルートが起点。`path_env` を指定した場合は、その環境変数の空でない値を優先する。英字で始まるソース名に英数字、`_`、`-` を使える。

```yaml
code_sources:
  - name: app
    path: ../app-repo
    path_env: APP_REPO_DIR
```

文書の `code_globs` に `app:src/**` を書くと、`app` 内の `src/` を参照する。接頭辞のない `src/**` は従来どおり文書プロジェクト内を参照する。`lint` は配置を確認して根拠ファイルを照合する。ソースの未配置・未登録と、配置済みで一致するファイルがない場合は、それぞれ理由を警告する。OKF 0.3 バンドルでこのプロジェクト固有の検査を使うときは `lint --project` を指定する。

```powershell
okf affected --source app --base main
```

指定ソースで `main` と現在の HEAD が分かれた地点からの変更と、作業ツリーの未コミット変更を集める。ソース名が一致する `code_globs` から対応文書を探し、未カバーのパスも表示する。文書側の `layer_map` はローカル変更の調査に適用する。外部ソースの変更を調べる際は `--base` を指定する。配置先、比較対象、共通の起点を確認できない場合は「差分未確認」を警告し、終了コード `0` を返す。

`stale` は外部コードの更新時刻を未検証と表示する。文書の期限やローカルコードの更新時刻は従来どおり判定する。`log` の対象は文書プロジェクトの Git 履歴。

## OKF のバンドル仕様を選ぶ

新規バンドルを OKF 0.3 として生成するには、初回の `index --write` より前に `okf.yml` の `index.okf_version` に `"0.3"` を指定する。既存バンドルではルート `index.md` の `okf_version` が優先され、索引更新は既存のメタデータと手書き部分を保持する。版宣言の追加・変更は手動で行う。新規生成時の既定は 0.2。

OKF 0.3 では、予約ファイル以外の Markdown に空でない `type` があればコンセプトとして扱う。型のない Markdown や未知の型を含むバンドルも読み込める。`lint` は OKF の書式を検査し、独自の型・レイヤー・根拠コード・索引の最新性も検査する場合は `lint --project` を使う。0.2 と版未宣言の既存バンドルには従来の検査を適用する。

0.3 の HTML では CommonMark のリンク、GFM テーブル、脚注を表示する。パスは記述ファイルからの相対、または先頭 `/` のバンドルルート基準で解決する。版が 0.2 以前、または未宣言の場合に限り、相対のパスフィールドをバンドルルートから再試行する。Markdown 本文のリンクにはこの再試行を適用しない。廃止済み文書の `superseded_by` は後継文書として表示する。

0.3 の信頼ラベルは `generated.at` 以降の有効な `verified` から決める。同時刻の検証も含み、`generated` がなければ有効な検証をすべて評価する。`team:` は機械確認の扱い。以前の検証は原文に残る。鮮度は `stale_after` と現在時刻を比べ、日付のみの場合は UTC の 00:00 とする。不正な値は `lint`、`stale`、HTML で表示する。プロジェクト独自の `code_globs` の変更検知は別に報告する。`sync` は 0.3 でもプロジェクトの規約を検査する。

## 新規文書の根拠コードと検査

`new doc` の `Project Overview`、`Architecture`、`Reference`、`How-To` には `--code-globs` が必要。その他の型では省略できる。生成後は本文を補い、目次を更新してから規約を検査する。雛形の記入例が残ると警告が出る。警告も失敗として扱う場合は、OKF 0.2 なら `lint --strict`、OKF 0.3 なら `lint --project --strict` を使う。

日本語タイトルでは `--slug` でファイル名を指定できる。`new --index` の索引更新に失敗した場合は、作成済みの Markdown を使い、原因を修正して `index --write` を実行する。既存バンドルに `Project Overview` の雛形がなければ、インストール済みパッケージの `scaffold/templates/project-overview.md` を、バンドルの `_templates/project-overview.md` へコピーする。別の空ディレクトリで `init` して生成した同名の雛形も使える。既に配置済みの雛形はそのまま使う。

パッケージスクリプトが引数列の先頭で渡す区切り `--` は1個まで受け取る。`new doc` / `new backlog` では種類名の直後に置く。オプション列の途中にある区切りや追加の区切りは受け付けない。

## 出力先と旧生成物の整理

旧生成物の整理は `render --output _site --cleanup-from docs --check` で計画を確認し、`--check` を外した明示実行だけで行う。通常の render / hook は旧出力を整理しない。hash・manifest で識別できる未編集生成物だけを新出力成功後に退避し、未知・編集済み出力は保持する。receipt と非上書き復元、旧新出力先の安全境界は [生成済みHTMLの整理](/render/output-cleanup.md) を参照する。

## 自リポジトリの CI

`self-check` は完全な Git 履歴を取得して `okf lint`、`okf index --check`、`okf render --check` を実行する。古い index は差分検査で失敗する。`okf stale` は参考レポートとして表示し、指摘件数の閾値を設けない。warn を失敗扱いにする `lint --strict` は採用していない。

`render --check` は全ページとアセットをメモリ内で生成できるかを検証する。既存 HTML との差分を比較するコマンドではなく、HTML 未生成のクリーン checkout でも使える。生成 HTML を Git に追加する必要はない。通常のテスト・一時バンドル smoke と並行して、実際の docs バンドルを検査する。

PR の CI は Node.js 22 と 24 の両方で `npm run test:release` を実行する。`npm run test:package` で tgz の導入・復旧を検査するのは Node.js 22 のジョブ。両バージョンで、CI が作った同一の tgz のインストールも確認する。[タグから公開する手順](/agents/release-node.md)

## YAML処理の所有者

設定・frontmatterの解析とnewのscalar/flow生成は `yamlio.py` が所有する。コマンドの引数・終了値・生成文字列は維持し、通常のDoc/Bundleはyamlioの現在backendを読む。旧 `cli.parse_yaml` の直接呼出しは旧backend差替えの互換adapterを通る。YAMLを省略した環境では従来の厳格なsubsetと拒否メッセージを使う。
