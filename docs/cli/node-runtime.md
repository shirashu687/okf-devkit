---
type: How-To
title: Node.js版をPythonなしで使う
description: Node.js版CLIの導入・対応機能・hook更新・互換性の検証方法を説明する。
tags: [cli, node, distribution]
status: stable
layer: cli
generated:
  by: devin/swe-2-max
  at: "2026-09-27T10:42:00Z"
code_globs:
  - node/*.mjs
  - package.json
  - package-lock.json
  - tests/node/*.mjs
  - src/okf_devkit/scaffold/hooks/*
  - src/okf_devkit/scaffold/*.tmpl
  - src/okf_devkit/scaffold/templates/*
  - src/okf_devkit/cli.py
  - tests/test_init.py
related:
  - /project/decisions/0001-node-runtime.md
---

# Node.js版をPythonなしで使う

## 導入

Node.js 22以上・npm・Gitを使用する。Pythonは実行・インストール時ともに不要。
本人・少人数向けの標準経路は、GitHubの固定コミットから各プロジェクトへのローカル導入とする。npmレジストリ公開は行わない。
初回導入・更新・新しい作業コピーの準備には、GitHubと依存取得先への通信が必要。通常のCLI実行は導入済みファイルを使う。

利用先のプロジェクトルートで実行する。`<COMMIT_SHA>` は利用する版の完全な40桁SHAに置き換える。

```sh
npm install --save-dev "git+https://github.com/shirashu687/okf-devkit.git#<COMMIT_SHA>"
npm pkg get scripts.okf
```

既存の `scripts.okf` がなければ次を実行する。既にある場合は既存用途を確認して統合し、無条件に置き換えない。
別用途の `scripts.okf` を保持する場合は `scripts."okf:dev"` のような別名へ設定する。initが読むのは `scripts.okf` のみのため、別名を使うときは生成案内とinit出力内の `npm run okf --` 表記を同じ名前へ手で揃える。

```sh
npm pkg set "scripts.okf=node node_modules/okf-devkit/node/cli.mjs"
npm run okf -- init --layer "app=src/**"
npm run okf -- index --write
npm run okf -- lint
```

初回のinstallは `package.json` がないプロジェクトにも依存の記録を作成する。
`package.json` と `package-lock.json` をGitに保存し、`node_modules/` を `.gitignore` に追加する。
initは既存のpackage設定やlockfileを書き換えない。空でない文字列の `scripts.okf` があれば、生成するAGENTS・CONVENTIONS・log・`_templates` の呼出し例と完了メッセージを `npm run okf --` に揃える。設定がなければ従来の `okf` 表記を維持する。既存文書は通常のinitでは保持される。

### 新しいclone・worktreeと更新

新しい作業コピーでは、そのプロジェクトルートで一度 `npm ci` を実行する。以後は `npm run okf -- lint` などを使う。サブディレクトリや複数packageのある構成では、対象の `okf.yml` と起動設定があるルートに移動する。

別の作業コピーやグローバルのokfには依存しない。未導入で起動に失敗した場合は `npm ci` の結果を確認する。起動時に `npx` で別パッケージを取得するなどの代替は行わない。

更新は新しい固定SHAでinstallを再実行し、packageとlockfileの差分、`npm run okf -- lint` を確認する。既存の文書・hookの更新は次節の手順で行う。自動更新・定期リリースは設けず、保守終了時はREADMEに状態を明記する。

### 配布方式の比較と採用理由

| 方法 | 利点 | 保守・セキュリティ上の考慮 | 判断 |
| --- | --- | --- | --- |
| GitHubの固定SHAから導入 | 公開アカウントや配布物作成を増やさず、利用先で導入できる | ソースと依存の信頼は必要。SHAと利用先lockfileで版を固定し、更新時に差分を確認する | 採用 |
| GitHub Releasesのtgz | 利用者へ検証した配布物を渡せる | 配布物の作成・検証・保管が必要。公開元と依存への信頼は残る | 将来の候補 |
| npmレジストリ公開 | 名前で導入・検索できる | 公開アカウント・公開権限・公開手順の保守が増える | 当面見送り |
| cloneして直接実行 | 開発中のコードをすぐ試せる | 配置場所と長いパスの管理が必要 | 開発用 |

npm非公開でも依存パッケージの保守は残る。SHA固定は安全性の証明ではなく、利用版を変動させないための措置。
配布経路は後から変更できるため、新たなADRは設けず本手順を更新する。
根拠: [npm install](https://docs.npmjs.com/cli/install/)、[npm scripts](https://docs.npmjs.com/cli/v11/commands/npm-run/)、[Issue #14](https://github.com/shirashu687/okf-devkit/issues/14)。

### 開発用cloneとローカルtgz

```powershell
# okf-devkit のチェックアウトで実行
npm ci
node node/cli.mjs --help
node node/cli.mjs --root "C:/path/to/project" init --layer "app=src/**"
node node/cli.mjs --root "C:/path/to/project" index --write
node node/cli.mjs --root "C:/path/to/project" lint
```

ローカル配布では、チェックアウトで `npm pack` を実行し、生成したtgzを導入先の `npm install --save-dev <tgzのパス>` でインストールする。その後、上記と同じscripts設定と呼出しを使う。別PC・worktreeで `npm ci` する場合も、そのtgzをlockfileの参照先に用意する必要がある。
POSIX環境ではパスを書き換え、同じコマンドを利用する。

## 既存プロジェクトの案内を更新する

導入とscripts設定後、既存の `docs/AGENTS.md` の実行案内を次の内容へ変更する。独自の規約は保持する。ルートのAGENTS.mdやCLAUDE.mdにも実行コマンドがあれば揃える。

> コマンドは `okf.yml` と `package.json` があるプロジェクトルートで実行する。新しいclone・worktreeでは最初に `npm ci` を実行する。OKF CLIは `npm run okf -- lint`、`npm run okf -- index --write` のように呼ぶ。導入・起動に失敗したら、そのエラーを報告する。

AGENTS・CONVENTIONS内の `okf …` の実行例を `npm run okf -- …` に置き換える。Python版を使い続けるプロジェクトは変更不要。
旧版から移行するときも同じ手順を使う。案内の更新だけを目的に `init --force` を使うと設定や編集済み文書まで上書きするため、必要な部分だけ編集する。

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
| render | 共有HTMLアセット、目次・関連・被リンク・Mermaid、output / check / hook |
| sync | index → log → lint → stale、gateの指紋による差し戻し制限 |

`--root` / `--config` はコマンドの前後で指定できる。
`render --check` は書き込まず生成可否を検証する。保存済みHTMLとの一致検査ではない。
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
