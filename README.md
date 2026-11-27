# okf-devkit

`okf-devkit` は、[OKF v0.2](https://github.com/GoogleCloudPlatform/open-knowledge-format) のドキュメントをコードと一緒に保守する CLI です。変更に影響される文書の確認、目次と履歴の更新、規約の検査、HTML での閲覧を支援します。

ドキュメントは Markdown と Git で管理します。利用先に別リポジトリの harness を導入する必要はありません。

## AIエージェントに導入を任せる

導入先リポジトリをCodexやClaude Codeなど、ファイル編集とコマンド実行ができるAIエージェントで開き、次の依頼文を貼り付ける。

```text
次の導入ガイドを読み、このリポジトリにokf-devkitを導入し、
初期設定と検証まで実施してください。
https://raw.githubusercontent.com/shirashu687/okf-devkit/main/docs/agents/install-okf.md

リポジトリの構成に合うレイヤーとソースの対応を設定し、
利用中のAIがドキュメントの規約を参照できる入口も整えてください。
既存の文書・設定・未コミット変更は保持してください。
```

AIが構成と既存環境を調べ、固定版のローカル導入、`okf.yml` と文書の初期配置、AI向け入口の接続、索引生成・lint・HTML生成の確認まで進める。詳細と完了条件は [導入ガイド](docs/agents/install-okf.md) にまとめている。
新しいパッケージ管理の追加、既存設定との競合、認証やエージェントの信頼設定など、人の判断・操作が必要な箇所は具体的な内容を確認する。URLを取得できない環境では、導入ガイドの本文をAIへ渡す。

## はじめる

Node.js 22 以上、npm、Git を用意します。導入先のリポジトリルートで `node_modules/` が Git の除外対象であることを確認します。以下は v0.1.0 プレリリースの固定 tgz を既存の npm プロジェクトに導入する例です。取得済み tgz と SHA-256 の照合手順は [導入ガイド](docs/agents/install-okf.md) にあります。

```bash
npm install --save-dev --save-exact --ignore-scripts "https://github.com/shirashu687/okf-devkit/releases/download/v0.1.0/okf-devkit-0.1.0.tgz"
```

次に、導入先の `package.json` に `okf` スクリプトを登録します。すでに `scripts.okf` がある場合は上書きされるため、内容を確認して別の名前を選んでください。

```bash
npm pkg set "scripts.okf=node node_modules/okf-devkit/node/cli.mjs"
npm run okf -- --help
```

以降のコマンドでは `npm run okf --` に続けて引数を渡します。スクリプトは導入済みのローカル CLI を直接起動します。Windows の PowerShell で `npm` の実行が制限される場合は `npm.cmd` を使えます。

チームで同じ構成を使うには lockfile を管理してください。開発版を試す場合は導入ガイドに従って完全な Git SHA に固定します。v0.1.0 に含まれる機能は [リリースノート](docs/project/releases/v0.1.0.md) を参照してください。

npm 以外の管理方式、manifest のないリポジトリ、更新・復旧の場合は、[導入ガイド](docs/agents/install-okf.md)で手順を確認してください。global インストールや未導入時の `npx` は上の手順では使いません。

### 初期化と動作確認

初めて使うリポジトリで、同じルートから実行します。

```bash
npm run okf -- init
npm run okf -- index --write
npm run okf -- lint
npm run okf -- render --check
```

`init` は `okf.yml`、`docs/` 内の作業ガイド・規約・テンプレートと hook 用ラッパーを生成します。既定は `docs/` と `shared` 層です。既存ファイルはスキップします。`--force` は既存の生成物を上書きするため、更新には使わないでください。`index --write` は目次を書き込み、`lint` と `render --check` は検査結果を表示します。

内容をブラウザで見るには `npm run okf -- render --open` を実行します。HTML は既定で `_site/` に生成されます。`_site/` と `.okf/render-backups/` を Git の管理対象から除外してください。

### Python 版

Python 3.11 以上と Git を使う場合は、選んだ仮想環境に導入できます。依存の取得には通信が必要です。再現性が必要な場合は `main` の代わりに確認済みコミット SHA を指定してください。

```bash
python -m pip install "git+https://github.com/shirashu687/okf-devkit.git@main"
okf init
okf index --write
okf lint
```

## 日常の使い方

以下の `okf` は選んだ CLI を表します。ローカル Node 版では `npm run okf --` に置き換えてください。

1. 文書に根拠となるコードを `code_globs` として記載します。
2. コードを変更したら `okf affected --base <変更前のコミットSHA>` で影響を確認します。未カバーのパスや `code_globs` のない文書も確認し、必要な本文を更新します。
3. `okf sync` で目次と設定済みの層の履歴を更新し、lint と stale の診断を確認します。無引数の `init` では履歴の自動追記は設定されません。未コミットの変更は履歴に記録されないため、log のスキップや警告も確認してください。

読み取りだけの点検には `okf lint`、`okf index --check`、`okf stale`、`okf render --check` を使います。文書作成や閲覧を含む目的別の案内は [日常操作ガイド](docs/agents/operate-okf.md)、全コマンドの引数・副作用・終了状態は [コマンド仕様](docs/cli/commands.md) を参照してください。

## エージェントと設定

初期化で生成される hook ラッパーは、作業終了時の HTML 更新に利用できます。導入した版の出力と既存のエージェント設定を確認し、必要に応じて設定を追加してください。製品側の信頼設定や実行環境、重複実行の注意は [終了 hook の手順](docs/agents/completion-hooks.md) を参照してください。

まず既定の `shared` 層で始められます。コードと層の対応など、プロジェクト固有の設定は `okf.yml` に置き、共通の語彙はパッケージから読み込みます。複数層や設定の詳細は [初期化と同梱雛形](docs/scaffold/reference.md) と [コマンド仕様](docs/cli/commands.md) を参照してください。

## 開発

```bash
python -m venv .venv
.venv/bin/python -m pip install -e .  # Windows: .venv/Scripts/python -m pip install -e .
.venv/bin/python tests/run_all.py
npm ci
npm test
npm run test:compat
```

Node 版の利用と比較テストについては [Node.js 版の利用手順](docs/cli/node-runtime.md)、配布の手順は [Release 手順](docs/agents/release-node.md) を参照してください。

## 開発時のフォルダ構成

| パス | 役割 |
| --- | --- |
| `src/node/` | Python不要で動くNode.js版CLI本体 |
| `src/okf_devkit/` | Python版CLIと、両実装で共有する既定設定・雛形・HTMLアセット |
| `node/cli.mjs` | 既存の直接起動・hook・npm binを維持する互換入口 |
| `scripts/` | 配布物の作成・検査とCI・Release用処理 |
| `tests/` / `tests/node/` | Pythonテスト / Node単独・互換・配布テスト |
| `docs/` | このリポジトリのOKFドキュメント |
| `harness/` | 開発エージェントの手順・プロジェクト設定・作業記録 |

`src/okf_devkit/` はPythonの標準的なsrc layoutで、配布名 `okf-devkit` に対するimport名が `okf_devkit` となる。プロジェクトを二重に格納しているわけではない。
Python版とNode.js版は同じ仕様の独立実装で、共有資産は1組だけを両方が読む。
構成の理由、互換層や雛形が似て見える理由は[構成ガイド](docs/project/repository-layout.md)を参照する。整理方針と進捗は[Issue #58](https://github.com/shirashu687/okf-devkit/issues/58)で管理する。

## ライセンス

[MIT](LICENSE)
