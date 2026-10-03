---
type: How-To
title: Node.js版をPythonなしで使う
description: Node.js版CLIの導入・対応機能・hook更新・互換性の検証方法を説明する。
tags: [cli, node, distribution]
status: stable
layer: cli
generated:
  by: codex/gpt-6
  at: 2026-10-03T10:19:54Z
code_globs:
  - node/*.mjs
  - package.json
  - package-lock.json
  - tests/node/*.mjs
  - src/okf_devkit/scaffold/hooks/*
related:
  - /project/decisions/0001-node-runtime.md
---

# Node.js版をPythonなしで使う

## 導入

Node.js 22以上とnpmを使用する。履歴を読む機能とhookにはGitも必要。
Pythonは実行・インストール時ともに不要。npmレジストリへの公開は未実施なので、チェックアウトまたはローカルtgzから利用する。

```powershell
# okf-devkit のチェックアウトで実行
npm ci
node node/cli.mjs --help
node node/cli.mjs --root "C:/path/to/project" init --layer "app=src/**"
node node/cli.mjs --root "C:/path/to/project" index --write
node node/cli.mjs --root "C:/path/to/project" lint
```

導入先で `npm exec -- okf` を使うには、チェックアウトで `npm pack` を実行し、生成した `okf-devkit-0.1.0.tgz` を導入先の `npm install --save-dev <tgzのパス>` でインストールする。
POSIX環境ではパスを書き換え、同じコマンドを利用する。

## 対応機能

| コマンド | 振る舞い |
| --- | --- |
| init | 共有scaffoldから設定・文書・hookを生成。既存ファイルはforce指定時のみ置換 |
| index | relative / bundle-absolute形式、backlog集計、write / check、全マーカーの事前検証 |
| log | Gitのfirst-parent履歴、baseline、層振り分け、ハッシュによる重複防止 |
| lint | L1〜L14、strict指定でwarnも非ゼロ終了 |
| stale | expired / orphan / outdated / unverified / draft-stale、JSON出力 |
| affected | base比較・作業ツリー・明示pathsから文書と未カバーパスを出力 |
| new | backlog / docの雛形、語彙検査、採番、出力先の検証 |
| status | backlogの状態・優先度集計、JSON出力 |
| render | 共有HTMLアセット、目次・関連・被リンク・Mermaid、output / check / hook / open |
| sync | index → log → lint → stale、gateの指紋による差し戻し制限 |

`new doc` の Project Overview / Architecture / Reference / How-To 型では `--code-globs "src/**"` が必須。複数のglobを指定でき、relatedは空リストで生成する。既存スクリプトにも根拠コード引数を追加する。
`--root` / `--config` はコマンドの前後で指定できる。
`render --open` は生成先の `index.html` を既定ブラウザで開く。Windows は rundll32、macOS は open、Linux は xdg-open を使用し、起動コマンドを開始できない場合は警告として扱う。起動後の表示やコマンド終了結果までは確認しない。
`--check` / `--hook` との併用では開かない。Mermaid の file:// 制限がある場合はローカルHTTP配信を使う。
`render` は既定でプロジェクトルートの `_site/` へ生成する。`.gitignore` に `_site/` を追加する。従来の隣接配置は `--output docs`（bundle_rootに合わせる）で使用できる。既存の隣接HTMLは自動削除しない。
`render --check` は書き込まず生成可否を検証する。保存済みHTMLとの一致検査ではない。
`render --output _site --cleanup-from docs --check` は旧生成物の退避計画も表示する。`--check` を外すと新出力成功後に未編集生成物だけを `.okf/render-backups/<id>/` へ退避する。手書き・編集済み・識別できない旧版出力は保持し、`--hook` との併用は拒否する。詳細は [生成済みHTMLの整理](/render/output-cleanup.md) を参照。
`render --hook` は成功時に `{}`、失敗時に1を返す。`sync --gate` は初回のlint errorで2、同じエラー集合の再検出で0を返す。
`sync` のlog入力はコミット済み履歴だけなので、今回の未コミット変更は履歴へ反映されない。

## 既存hookの更新

新規 `init` はNode.jsを探索するhookを生成する。導入済みプロジェクトでは、カスタムhookとの差分を確認して以下の2ファイルだけをコピーする。
`init --force` は設定や文書も上書きするため、hook更新専用には使わない。

```powershell
# 導入先プロジェクトで、npmパッケージをインストールした後に実行
Copy-Item node_modules/okf-devkit/src/okf_devkit/scaffold/hooks/render_hook.ps1 .okf/hooks/render_hook.ps1
Copy-Item node_modules/okf-devkit/src/okf_devkit/scaffold/hooks/render_hook.sh .okf/hooks/render_hook.sh
```

POSIXでは `cp` で同じ2ファイルをコピーする。探索順はローカルnpmパッケージ、主ワークツリーのnpmパッケージ、従来のPython経路、開発チェックアウト。
開発チェックアウトは `src/okf_devkit/defaults.yml` がある場合だけ候補にする。npm依存が未導入でも既存Python環境を優先して利用できる。
hook実行時にnpmレジストリへアクセスしない。Windows PowerShell 5.1でもUTF-8 BOMなしのhookを読めるよう、ps1のソースはASCIIで記述する。

## 検証と互換性

```powershell
npm test
npm run test:compat
```

`npm test` はPythonを要求せず、PATHからPythonを外したCLI・hook実行も検証する。
`npm run test:compat` は開発時の比較用で、既存 `.venv` または環境変数 `OKF_TEST_PYTHON` で指定したPythonを要求する。
生成日時を除くscaffoldと新規文書、索引2形式、Git履歴、レポート、HTMLを共通入力で比較する。コンソールのCRLF/LFのみ比較時に正規化し、ファイル内容はそのまま比較する。

YAMLは1.1として読み、日付を文字列に正規化する。Node.js版では重複キー・循環aliasをエラーにする。
全YAML構文・全Markdown・全カスタム正規表現の同値性を保証しない。`kind_rules.pattern` はJavaScriptのRegExpで評価するため、Python専用正規表現構文は移植が必要。
Node.js版はシンボリックリンクを含む出力先が対象範囲外なら書き込みを拒否する。PowerShell単独の実装ではなく、Node.js CLIをPowerShellから実行する。

HTML の Backlog 進捗一覧は Python 版と同じ読み取り専用表示で、設定ディレクトリ・状態別件数・本文リンクを扱う。手順は [Backlog の進捗表示](/render/backlog-progress.md) を参照。

HTML の階層ナビ・元ファイル表示も Python 版と同じ構造を生成する。[階層ナビの手順](/render/navigation.md) を参照。

`init` は shared 層の履歴をバンドルルートの `log.md` に作成し、生成設定の `log.paths.shared` と一致させる。層をまたぐ本文の配置先 `project/` とは分離され、`log --layer shared --write` はこの既存ファイルへ追記する。既存プロジェクトの `project/log.md` は自動移動・削除しない。
