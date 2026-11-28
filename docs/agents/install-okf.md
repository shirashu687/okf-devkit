---
type: How-To
title: AIにokf-devkitの導入・セットアップ・更新を依頼する
description: AIが対象repoに合う固定Node版の導入・初期設定・検証・更新・復旧を支援する。
tags: [agents, node, distribution, how-to]
status: draft
layer: shared
generated:
  by: codex/gpt-6
  at: 2026-10-29T15:09:10Z
code_globs:
  - package.json
  - package-lock.json
  - src/node/*.mjs
  - src/okf_devkit/scaffold/hooks/*
  - .github/workflows/release.yml
  - scripts/release-*.mjs
  - scripts/package-smoke.mjs
related:
  - /project/decisions/0002-github-node-distribution.md
  - /project/releases/v0.1.0.md
  - /cli/node-runtime.md
  - /agents/operate-okf.md
  - /agents/completion-hooks.md
  - /render/output-cleanup.md
---

# AIにokf-devkitの導入・セットアップ・更新を依頼する

この手順は、利用者から導入または更新を依頼されたエージェント向け。Node 版の本体は GitHub、依存パッケージは npm から取得する。Python 版も引き続き使える。日々の文書更新は [日常操作ガイド](/agents/operate-okf.md) を参照する。

## 初回セットアップを任されたAIへ

「導入して初期設定と検証まで」という依頼は、パッケージ導入に加え、対象repoへの初期配置とAI向け入口の接続までを含む。以下の手順1〜5を実施し、完了条件を確認する。導入だけの依頼では初期化・AI設定を追加しない。
依頼済みの範囲では、調査結果と変更予定を短く伝えて作業を進める。環境やコードから分かるレイヤー構成などを利用者へ再質問せず、新しいパッケージ管理の追加、依頼範囲を越える変更、利用者編集との競合がある場合に具体案を確認する。

このガイドは **okf-devkit側の文書** であり、導入先に `docs/agents/install-okf.md` があることを前提にしない。外部から読んだ場合、本文の `/agents/...` 等のリンクは、ガイドを取得した同じリビジョンの `docs/` 配下として解決する。案内URLの `main` はガイドの参照先であり、インストールする本体は手順3の完全SHAまたは検証済み配布物へ固定する。

1. **対象repoを調べる。** 手順1で既存の指示・パッケージ管理・OKF導入状態を確認し、実在するソースディレクトリからレイヤーと `code_globs` の候補を決める。`app=src/**` を一律に使わない。
2. **固定版をローカル導入する。** 手順2〜4に従い、既存の管理方式で導入してCLIの実体と由来を確認する。manifestがない場合は手順2の具体案を確認する。導入済みなら重ねて初期化せず、必要な差分を調べる。
3. **設定と文書を初期配置する。** 手順5の `init` を対象repoに合わせて実行し、`okf.yml`、バンドルの `AGENTS.md`・`CONVENTIONS.md`・テンプレート・層別logを確認する。既存docsがある場合は配置と衝突を先に調べ、既存文書を一括変換しない。新規バンドルには、実コードを根拠に `code_globs` を持つ最小の概要文書を作り、雛形の本文を補完する。作成方法は [日常操作ガイド](/agents/operate-okf.md) を参照する。
4. **利用中のAIの入口へつなぐ。** 対象repoのルート `AGENTS.md`、`CLAUDE.md` 等の既存の入口へ、バンドルの `AGENTS.md` を読む案内と実際のCLI呼び出し方を必要な範囲だけ追記する。入口がなければ利用中のAIに合うものを作る。次回のコード変更時に `affected --base <変更前の固定SHA>` から文書更新へ進めるよう案内する。パスは選んだバンドル配置へ合わせ、既存ルールを保持する。okf-devkit開発用の `harness/` やルートの指示全文をコピーしない。
5. **生成物と動作を確認する。** 手順5の索引生成・検査に加えて `index --check` と対象repoで必須の既存テストを実行する。HTMLの出力先とGit除外を確認して `render` を実行し、閲覧先を報告する。選んだ版のhook生成・登録状態を確認し、実AIイベントの検証とCLI単体の検証を区別する。人による信頼設定が必要なら、その操作を案内する。

### セットアップの完了条件

| 確認対象 | 完了の根拠 |
| --- | --- |
| CLI | 導入元の完全SHAまたは配布物、lockfile、実行したCLIの実体を確認し、`--help` が成功する |
| 設定と文書 | 実ソースとレイヤーが対応し、新規バンドルには本文と `code_globs` を補完した文書がある。既存の利用者編集を保持している |
| AI向け入口 | 利用中のAIの入口から、実在するバンドルの規約と実CLIの使い方を参照できる |
| 検証 | `index --write`、`lint`、`index --check`、`render --check`、`render` と対象repoの必須テストの結果を個別に確認する。警告も対応または残件として報告する |
| 引継ぎ | 変更ファイル、日常操作、HTML閲覧先、復旧方法、人の操作待ち・未検証範囲を報告する |

失敗・未実行・実行不能があれば、対応する項目を完了扱いにしない。hookの実イベント確認や人の信頼操作が残る場合は、ローカルのセットアップ・CLI検証の結果と分けて示す。

## 配布状況と導入経路

公開済みの v0.1.0 プレリリースは、固定 URL から tgz を取得できる。同梱 README にある古い PyPI 例や公開状況の記述については、このガイドの手順を使う。収録機能はリリースノートで確認する。[GitHub Release](https://github.com/shirashu687/okf-devkit/releases/tag/v0.1.0) · [リリースノート](/project/releases/v0.1.0.md)

OKF 0.3 対応や `doctor`、`upgrade --check` を試す場合は、それらを含む確認済みの完全 Git SHA を選ぶ。タグの作成から公開までの作業は配布担当者向けの手順に従う。[公開手順](/agents/release-node.md)

## 1. 環境と既存状態を読む

対象repoの入口・規約とGit状態、package.json、lockfile、workspace、既存の `okf.yml`、docs、hookとAI設定を読む。
未コミット変更は利用者の作業として保つ。npm/yarn/pnpmの管理方式を勝手に切り替えない。
Node.js 22 以上と Git を用意する。パッケージマネージャーは、起動する実体とバージョン、そのバージョンが要求する Node.js の範囲を確認する。Windows の PowerShell で `npm` が実行ポリシーにより制限される場合は `npm.cmd` を使える。POSIX では `npm` に読み替える。

```powershell
node --version
npm.cmd --version
git --version
Get-Command node,npm.cmd,git,okf -ErrorAction SilentlyContinue
```

不足していれば [Node.js公式導入案内](https://nodejs.org/en/download) と [Git公式案内](https://git-scm.com/downloads) を提示して手動導入を待つ。AIが無断でOSのランタイム・PATH・実行ポリシーを変えない。
Python版やglobal版の `okf` がある場合、解決されたパス・起動内容を調べる。裸の `okf` の成功をローカルNode版の検証に置き換えない。

## 2. 具体的な変更案を確認する

標準は対象repoのdevDependencyとして固定導入する。利用者がglobalを選ぶ場合だけglobal案へ進む。
取得元・完全SHAまたはReleaseタグ/tgz・変更するmanifest/lockfile・通信先・initの有無と生成先・バックアップ/復旧案を提示する。
既存依頼で承認された範囲は継続し、新しい管理方式・global範囲・既存設定の変更を含む場合だけ具体案の承認を求める。

非Node repoにmanifestがなければ、プロジェクトに合わせたprivateなpackage.json案と配置を提示する。例えば承認済みの独立repoルートなら `{"private":true}` が出発点になる。
既存workspaceのルート/メンバーとlockfileの位置を確認し、勝手な `npm init -y` やネストした別lockfileを作らない。npm以外が管理している場合は利用者の方式に合わせ、下記npmコマンドを機械的に実行しない。

依存を導入する前に `node_modules/` を使う構成では Git の除外を確認する。新規の単独リポジトリであればルートの `.gitignore` に `/node_modules/` を追加できる。

## 3. 取得とインストール

### 公開済み tgz

GitHub Release の版・asset 名・URL と SHA-256 を確認する。v0.1.0 では以下の3ファイルを取得できる。

```powershell
# 新しい空の取得ディレクトリで実行
$assetBase = "https://github.com/shirashu687/okf-devkit/releases/download/v0.1.0"
foreach ($assetName in @("okf-devkit-0.1.0.tgz", "release-manifest.json", "SHA256SUMS")) {
    Invoke-WebRequest "$assetBase/$assetName" -OutFile $assetName
}
$releaseManifest = Get-Content release-manifest.json -Raw | ConvertFrom-Json
Get-FileHash okf-devkit-0.1.0.tgz,release-manifest.json -Algorithm SHA256
Get-Content SHA256SUMS
$releaseManifest
```

manifest の repository は `shirashu687/okf-devkit`、tag は `v0.1.0`、version は `0.1.0`、commit は `12cdb44c2876b50bd7337a5ea20f7744a27d7802`。tgz の名前・実ファイルサイズ・SHA-256 が manifest に一致することを確認する。v0.1.0 の tgz の SHA-256 は `b32e09ddacd885da8bf1e8c84d1fde5dd9411169b92c388f5271db5552ddf080`。tgz と manifest の両方を `SHA256SUMS` に照合する。POSIX では `sha256sum -c SHA256SUMS` が使える。3ファイルがそろい、チェックサムの2項目と manifest の内容がすべて一致した場合に先へ進む。

照合した tgz を導入先からアクセスできる共有可能な位置に置く。次は導入先ルートの `vendor/okf-devkit-0.1.0.tgz` をそのまま使う例で、既存のパッケージマネージャーの行を実行する。

```bash
# npm
npm install --save-dev --save-exact --ignore-scripts "./vendor/okf-devkit-0.1.0.tgz"
# pnpm
pnpm add --save-dev --save-exact --ignore-scripts "./vendor/okf-devkit-0.1.0.tgz"
# Yarn Classic (1.x)
yarn add --dev --exact --ignore-scripts "./vendor/okf-devkit-0.1.0.tgz"
# Yarn 4
yarn add --dev --exact --mode=skip-build "okf-devkit@file:./vendor/okf-devkit-0.1.0.tgz"
```

既存の lockfile からの再導入には npm の `npm ci --ignore-scripts`、pnpm の `pnpm install --frozen-lockfile --ignore-scripts`、Yarn 1 の `yarn install --frozen-lockfile --ignore-scripts`、Yarn 4 の `yarn install --immutable --mode=skip-build` を使う。既存プロジェクトで別途必要な build は導入と分ける。Yarn 4 のオプションは [Yarn の CLI リファレンス](https://yarnpkg.com/cli/install) を参照する。

固定 HTTPS URL を lockfile に記録する運用では同じ Release URL を引数にできる。Yarn 4 では `okf-devkit@https://…` の形にする。公開版の導入と再導入は Node.js 24 で npm 11.9、pnpm 11.25、Yarn 1.22、Yarn 4.9 を使って確認した。Node.js 22 系では npm 11.9 は 22.9 以上、pnpm 11.25 は 22.13 以上が必要。

### 開発版の Git SHA と Python 版

Node の開発版は、確認済みの完全な 40 桁の Git SHA を HTTPS で取得して tgz にする。以下の SHA は SSH 認証なしで取得手順を確認したときのもの。試したい機能を含む完全 SHA に置き換える。`okf-devkit-source` は導入先とは別の新規ディレクトリ。

```bash
git init okf-devkit-source
git -C okf-devkit-source fetch --depth 1 https://github.com/shirashu687/okf-devkit.git 195252d3354acece9c72c987a9f0ab6559db6aa3
git -C okf-devkit-source switch --detach FETCH_HEAD
git -C okf-devkit-source rev-parse HEAD
cd okf-devkit-source
npm pack --ignore-scripts
```

出力された SHA と指定値を照合し、tgz と SHA-256 を記録する。導入先では上記と同じパッケージマネージャーの tgz 手順を使う。

Python 3.11 以上では、選んだ仮想環境で `python -m pip install "git+https://github.com/shirashu687/okf-devkit.git@<確認済みの完全SHA>"` を実行する。同じ SHA をチェックアウトして `python -m pip install -e .` で導入する方法もある。

```powershell
# 取得済みファイルの確認。EXPECTED_SHA256との一致を確認してからインストール
Get-FileHash "C:/approved/path/okf-devkit-VERSION.tgz" -Algorithm SHA256
npm.cmd install --save-dev --save-exact --ignore-scripts "C:/approved/path/okf-devkit-VERSION.tgz"
```

ファイル経路をmanifestへ保存した場合は、その経路がCI/他端末でも利用可能か確認する。公開済み固定asset URLへ保存する案または承認済みの配布物保管を選び、個人PCだけの絶対パスをチームの再現手段にしない。
固定URLとchecksumはバイト一致の確認であり、取得元の信頼性の証明ではない。
manifestとlockfileの差分で指定版・予期しない依存変更を確認する。導入は `--ignore-scripts` を既定とし、ライフサイクルscriptを実行せず、インストールから `init`・AI設定・hookを自動作成しない。依存取得の通信は行う。
対象repoに必要な既存buildは、承認済みの別工程として扱う。導入のためにglobal npm設定・PATH・script実行ポリシーを変更しない。

globalを明示選択した場合は、同じ確認済みtgzに `npm.cmd install --global --ignore-scripts <取得済みtgz>` を用いる。既存globalの版・導入元・復旧元を先に記録する。同一本体tgzでも推移依存の同一性は保証せず、repoのlockfile管理と同等とは扱わない。

## 4. CLIの実体と動作を検証する

`node_modules` を使うローカル版はリポジトリルートから実ファイルを明示する。`--version` に対応する版は実行中の版を確認できる。v0.1.0 プレリリースは同梱 manifest の版を読む。

```powershell
node -p "JSON.parse(require('node:fs').readFileSync('node_modules/okf-devkit/package.json','utf8')).version"
node node_modules/okf-devkit/node/cli.mjs --help
```

選んだSHA/tgzの由来をlockfileと照合する。package.jsonの版文字列だけでGitコミットを証明しない。
workspace等で配置が異なる場合は実際のインストール先を解決して同じCLIファイルを呼ぶ。
Yarn 4 の Plug'n'Play では `yarn run -B okf --help` で導入済みバイナリを起動し、同じ接頭辞で `init` や `lint` を実行する。hook が利用する `node_modules` ベースの探索とは別経路なので、実際の hook の起動先を確認する。版は `yarn node -p "require('okf-devkit/package.json').version"` で確認する。手順5の各コマンドでも CLI の起動部分を `yarn run -B okf` に置き換える。
起動スクリプトを使う場合は、npm は `npm run okf -- index --check`、pnpm は `pnpm run okf index --check` のように引数を渡す。
`npx okf` / `npm exec -- okf` は未導入時に別パッケージを取得し得るため、導入確認前の検証には使わない。
globalの場合もbin shim/対象packageを解決してNode版であることを確認する。

## 5. 初期化とAI設定を別に扱う

インストールだけでは `init` やAI設定変更を実行しない。初期化の依頼がある場合、レイヤー/ソースglob/生成先を調べ、生成するファイルを確認して実行する。
`--layer NAME=GLOB[:DIR]` の層名は英小文字・数字で始め、以降は英小文字・数字・`-`・`_` を使える。`shared` は予約済みで層名は重複できない。実ディレクトリが camelCase なら `appclient=src/appClient/**:appClient` のように `DIR` を指定できる。

```powershell
# app と src/** は対象repoへ合わせる
node node_modules/okf-devkit/node/cli.mjs init --layer "app=src/**"
node node_modules/okf-devkit/node/cli.mjs index --write
node node_modules/okf-devkit/node/cli.mjs lint
node node_modules/okf-devkit/node/cli.mjs index --check
node node_modules/okf-devkit/node/cli.mjs render --check
```

使えるオプションは導入した版の `init --help` で確認する。対応版では `--agent codex` のように選んだ製品の設定を新規作成する。既定は全対応製品で、`--agent none` は登録を省く。`--runner "node node_modules/okf-devkit/node/cli.mjs"` を渡すと、生成する案内の起動表記を揃えられる。

`init` は既存ファイルをスキップする。`--force` を指定すると既存の生成物を置き換えるが、エージェント設定と `.gitignore` は保持する。導入済みの `okf.yml` や文書、hook は、変更前との差分を見て管理元が分かる箇所だけを更新する。利用者の編集と競合したら、変更を止めて調整する。[既存リポジトリの更新ガイド](/agents/upgrade-existing-okf.md)
AI設定・終了hookは [終了hook手順](/agents/completion-hooks.md) の製品別対応と信頼を確認し、repo内の承認済み箇所だけを扱う。global hookは変更しない。
インストール版の選択だけでhookの実行版は決まらない。ローカル/主worktree/Python/開発checkoutの探索順と実配置を確認し、選んだNode版へ到達することを検証する。実AIイベント未検証ならその限界を報告する。
生成物のignoreも差分で確認する。HTMLの保存・旧出力整理は [cleanup手順](/render/output-cleanup.md) の別操作とする。

### リポジトリ側の AI 入口に貼る文案

既存の `AGENTS.md` または `CLAUDE.md` に、配置と起動方法を合わせて追記できる。下の例は `docs/` と `node_modules/` を使う Node 版を想定している。

```markdown
## OKF 文書を扱うとき

- [文書の作業ガイド](docs/AGENTS.md) と [執筆規約](docs/CONVENTIONS.md) を読む。
- [日常操作ガイド](https://github.com/shirashu687/okf-devkit/blob/main/docs/agents/operate-okf.md) と導入済み CLI の help で手順を確認する。
- リポジトリルートから `node node_modules/okf-devkit/node/cli.mjs` を実行する。
- 文書や初期化の出力にある `okf ...` はこの起動表記に置き換える。CLI の自動取得を避けるため `npx okf` は使わない。
- 変更の影響は `affected --paths <変更パス>`、HTML は `render --check` を起動表記の後に指定する。
- 索引は `node node_modules/okf-devkit/node/cli.mjs index --write`、検査は `node node_modules/okf-devkit/node/cli.mjs lint` を実行する。
```

バンドルの位置が異なる場合はリンクも合わせる。Yarn 4 Plug'n'Play では起動表記を `yarn run -B okf`、Python 版では `python -m okf_devkit.cli` に替える。

## 6. 明示依頼による更新と復旧

導入済みリポジトリの棚卸し、個別の設定差分と OKF 仕様の切り替えは [既存リポジトリの更新ガイド](/agents/upgrade-existing-okf.md) を使う。

更新前に現行版・取得元・lockfile・Node/npm版とmanifestを保存する。設定/文書/hook/生成物のバックアップはパッケージ復旧用と区別する。
指定された新SHA/公開済みassetへ更新し、手順4と対象repoの検証を実施する。対応する版では `doctor` で導入状態を確認し、`upgrade --check` で取り込む scaffold の差分を確認する。設定更新は手順5の既知範囲の差分のみ。
失敗時は今回変更したmanifestとlockfileを保存内容へ戻し、npm管理repoなら `npm.cmd ci --ignore-scripts` で保存した依存状態を再作成する。ciはnode_modulesを入れ替えるため、その影響も事前に確認する。必要な既存buildは承認済みの別工程とする。globalの復旧は保存した旧tgz/取得元を `--ignore-scripts` 付きで再導入する。
設定/文書/HTMLはそれぞれのバックアップから競合を確認して戻す。後から加わった利用者編集を上書きせず、`git reset --hard` や無関係な変更の一括取消を使わない。

## 7. アンインストールと報告

ローカルnpm依存の撤去は承認済み範囲で `npm.cmd uninstall --save-dev okf-devkit`、global選択時だけ `npm.cmd uninstall --global okf-devkit` を使う。既存管理方式が別ならそれに従う。
OKF文書・設定・HTML・AI設定をパッケージ撤去と一緒に削除しない。今回追加したhook/設定の既知箇所だけを差分確認し、撤去の依頼がある場合に調整する。
報告には対象repo、導入元・版・実CLI、変更ファイル、検証結果、未確認の実AIイベント、復旧方法を記す。private認証情報や全文ログを貼らない。

## AIへ貼り付ける依頼文

導入先repoをAIエージェントで開いて渡す。導入先にこのガイドを事前配置する必要はない。

```text
次の導入ガイドを読み、このリポジトリにokf-devkitを導入し、
初期設定と検証まで実施してください。
https://raw.githubusercontent.com/shirashu687/okf-devkit/main/docs/agents/install-okf.md

リポジトリの構成に合うレイヤーとソースの対応を設定し、
利用中のAIがドキュメントの規約を参照できる入口も整えてください。
既存の文書・設定・未コミット変更は保持してください。
```

URLを取得できない環境では、ガイド本文を添えて同じ依頼を渡す。導入だけを依頼する場合は「初期設定と検証まで」を「インストールとCLIの検証まで。初期化・AI設定の変更は不要」に変え、レイヤー設定・入口整備の2行を外す。更新・復旧は手順6の対象版と範囲を指定する。

## 公式資料

- [npm install](https://docs.npmjs.com/cli/v11/commands/npm-install/)：Git/tgz依存と導入方式
- [npm ci](https://docs.npmjs.com/cli/v11/commands/npm-ci/)：lockfileに基づく再導入
- [npm exec](https://docs.npmjs.com/cli/v11/commands/npm-exec/)：未導入パッケージの取得
- [GitHub Releaseの管理](https://docs.github.com/en/repositories/releasing-projects-on-github/managing-releases-in-a-repository)：Draftと公開操作
