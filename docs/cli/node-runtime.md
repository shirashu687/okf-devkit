---
type: How-To
title: Node.js版をPythonなしで使う
description: Node.js版CLIの導入・対応機能・hook更新・互換性の検証方法を説明する。
tags: [cli, node, distribution]
status: stable
layer: cli
generated:
  by: codex/gpt-6
  at: 2026-10-04T09:15:06Z
code_globs:
  - src/node/*.mjs
  - package.json
  - package-lock.json
  - tests/node/*.mjs
  - src/okf_devkit/scaffold/hooks/*
related:
  - /agents/install-okf.md
  - /agents/upgrade-existing-okf.md
  - /cli/commands.md
  - /project/decisions/0001-node-runtime.md
---

# Node.js版をPythonなしで使う

## 導入

Node.js 22 以上と npm を使う。履歴を読む機能と hook には Git も必要。Node.js 版のインストールと実行に Python は不要。GitHub Release の tgz または Git SHA を固定して導入できる。[導入ガイド](/agents/install-okf.md)

```powershell
# okf-devkit のチェックアウトで実行
npm ci
node node/cli.mjs --help
node node/cli.mjs --root "C:/path/to/project" init --layer "app=src/**"
node node/cli.mjs --root "C:/path/to/project" index --write
node node/cli.mjs --root "C:/path/to/project" lint
```

チェックアウトした版を別のリポジトリで使う場合は、`npm pack --ignore-scripts` で tgz を作る。導入先で `npm install --save-dev --save-exact --ignore-scripts <tgzのパス>` を実行し、`node node_modules/okf-devkit/node/cli.mjs --help` で導入先の CLI を確認する。POSIX 環境では例のパスを実際の配置に合わせる。

## 日常操作とhelp

`<command> --help` でコマンドの用途、引数、実行例を確認する。新規作成の引数は `new doc --help` または `new backlog --help` で確認できる。初期化前でもヘルプを表示できる。`--root` と `--config` はサブコマンドの前に置くと Python 版でも同じ書き方を使える。[日常操作ガイド](/agents/operate-okf.md)

## 対応機能

| コマンド | 振る舞い |
| --- | --- |
| --version | 実行した CLI のバージョンを表示 |
| init | 設定、文書、hook を生成。`--agent` で登録先、`--runner` で案内の起動表記を指定 |
| doctor | CLI の実体、設定、層、hook 登録、Git 除外、旧 HTML の候補を表示 |
| upgrade --check | 導入先のファイルを配布時の雛形と比較し、差分を表示 |
| index | relative / bundle-absolute形式、backlog集計、write / check、全マーカーの事前検証 |
| log | Gitのfirst-parent履歴、baseline、層振り分け、ハッシュによる重複防止 |
| lint | OKF の書式を検査。0.3 でプロジェクト固有の規約も検査するには `--project`、警告で失敗させるには `--strict` を指定 |
| stale | expired / orphan / outdated / unverified / draft-stale / external-unverified、JSON出力 |
| affected | ローカル変更または `--source` で選んだ外部 Git の変更から文書と未カバーパスを出力 |
| new | backlog / docの雛形、語彙検査、採番、出力先の検証 |
| status | backlogの状態・優先度集計、JSON出力 |
| render | 共有HTMLアセット、目次・関連・被リンク・Mermaid、output / check / hook / open |
| sync | index → log → lint → stale、gateの指紋による差し戻し制限 |

`new doc` の Project Overview / Architecture / Reference / How-To 型では `--code-globs "src/**"` が必須。複数のglobを指定でき、relatedは空リストで生成する。既存スクリプトにも根拠コード引数を追加する。
Node.js 版では `--root` と `--config` をサブコマンドの後にも指定できる。[コマンド仕様](/cli/commands.md)
`render --open` は生成先の `index.html` を既定ブラウザで開く。Windows は rundll32、macOS は open、Linux は xdg-open を使用し、起動コマンドを開始できない場合は警告として扱う。起動後の表示やコマンド終了結果までは確認しない。
`--check` / `--hook` との併用では開かない。Mermaid の file:// 制限がある場合はローカルHTTP配信を使う。
`render` は既定でプロジェクトルートの `_site/` へ生成する。`_site/` は Git の除外対象にする。Markdown と同じディレクトリに出力する場合は、`--output docs` の `docs` をバンドルルートに合わせて指定する。旧生成物は後述の整理手順で確認する。
`render --check` は書き込まず生成可否を検証する。保存済みHTMLとの一致検査ではない。
`render --output _site --cleanup-from docs --check` は旧生成物の退避計画も表示する。`--check` を外すと新出力成功後に未編集生成物だけを `.okf/render-backups/<id>/` へ退避する。手書き・編集済み・識別できない旧版出力は保持し、`--hook` との併用は拒否する。詳細は [生成済みHTMLの整理](/render/output-cleanup.md) を参照。
`render --hook` は成功時に `{}`、失敗時に1を返す。`sync --gate` は初回のlint errorで2、同じエラー集合の再検出で0を返す。
`sync` のlog入力はコミット済み履歴だけなので、今回の未コミット変更は履歴へ反映されない。

## 既存hookの更新

対応版の `init` は、Node.js を探して起動するラッパーと、選んだエージェントの未作成の設定ファイルを配置する。導入済みのプロジェクトでは `doctor` と `upgrade --check` で状態を確認し、必要な差分を反映する。ラッパーを置き換える場合は、既存ファイルに独自の変更があるか確認してから以下の 2 ファイルをコピーする。[更新ガイド](/agents/upgrade-existing-okf.md) · [終了 hook の手順](/agents/completion-hooks.md)

```powershell
# 導入先プロジェクトで、npmパッケージをインストールした後に実行
Copy-Item node_modules/okf-devkit/src/okf_devkit/scaffold/hooks/render_hook.ps1 .okf/hooks/render_hook.ps1
Copy-Item node_modules/okf-devkit/src/okf_devkit/scaffold/hooks/render_hook.sh .okf/hooks/render_hook.sh
```

POSIXでは `cp` で同じ2ファイルをコピーする。探索順はローカルnpmパッケージ、主ワークツリーのnpmパッケージ、従来のPython経路、開発チェックアウト。
開発チェックアウトは `src/okf_devkit/defaults.yml` がある場合だけ候補にする。npm依存が未導入でも既存Python環境を優先して利用できる。
hook実行時にnpmレジストリへアクセスしない。Windows PowerShell 5.1でもUTF-8 BOMなしのhookを読めるよう、ps1のソースはASCIIで記述する。

このリポジトリの `.okf/hooks/` も共有 scaffold と同じラッパーを使い、
Claude、Copilot、Codexの終了設定は、この共通ラッパーをadvisoryアダプター経由で呼ぶ。
手動の共通ラッパーは失敗時に非0を返し、終了イベント用アダプターは標準エラーへ診断を残して0と `{}` を返す。
対応環境、信頼、二重生成の可能性、未検証の実イベントは [終了hookの手順](/agents/completion-hooks.md) を参照する。
プロジェクト内の設定だけを管理し、利用者のグローバルhook設定は変更しない。

## 検証と互換性

```powershell
npm test
npm run test:compat
```

`npm test` はPythonを要求せず、PATHからPythonを外したCLI・hook実行も検証する。
`npm run test:compat` は開発時の比較用で、既存 `.venv` または環境変数 `OKF_TEST_PYTHON` で指定したPythonを要求する。
生成日時を除くscaffoldと新規文書、索引2形式、Git履歴、レポート、HTMLを共通入力で比較する。コンソールのCRLF/LFのみ比較時に正規化し、ファイル内容はそのまま比較する。

プロジェクト設定と OKF 0.2 の frontmatter は YAML 1.1 として読み、日付を文字列に正規化する。OKF 0.3 の frontmatter には YAML 1.2 の Core Schema を使う。Node.js 版では重複キーと循環エイリアスをエラーにする。
全YAML構文・全Markdown・全カスタム正規表現の同値性を保証しない。`kind_rules.pattern` はJavaScriptのRegExpで評価するため、Python専用正規表現構文は移植が必要。
Node.js版はシンボリックリンクを含む出力先が対象範囲外なら書き込みを拒否する。PowerShell単独の実装ではなく、Node.js CLIをPowerShellから実行する。

HTML の Backlog 進捗一覧は Python 版と同じ読み取り専用表示で、設定ディレクトリ・状態別件数・本文リンクを扱う。手順は [Backlog の進捗表示](/render/backlog-progress.md) を参照。

HTML の階層ナビ・元ファイル表示も Python 版と同じ構造を生成する。[階層ナビの手順](/render/navigation.md) を参照。

`init` は shared 層の履歴をバンドルルートの `log.md` に作成し、生成設定の `log.paths.shared` と一致させる。層をまたぐ本文の配置先 `project/` とは分離され、`log --layer shared --write` はこの既存ファイルへ追記する。既存プロジェクトの `project/log.md` は自動移動・削除しない。

Backlogの閲覧は状態別の折り畳みリストを既定とし、同じ項目を任意のカンバン表示へ切り替える。専用検索は表示のみを変更し、元Markdownとcleanupの安全契約は保持する。Python/Nodeは同じHTMLと共通アセットを利用する。

## GitHub 配布と AI による導入

`package.json` は `private: true`。本体は GitHub から取得し、依存パッケージは npm から取得する。導入後は選んだ版の CLI を直接起動する。初期化、エージェント設定、導入したパッケージの復旧は、それぞれ必要に応じて実施する。[導入ガイド](/agents/install-okf.md)
