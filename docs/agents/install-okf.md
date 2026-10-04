---
type: How-To
title: AIにokf-devkitの導入と更新を依頼する
description: AIが環境と変更範囲を確認し固定Node版の導入・検証・更新・復旧を支援する。
tags: [agents, node, distribution, how-to]
status: draft
layer: shared
generated:
  by: codex/gpt-6
  at: 2026-10-04T14:59:46Z
code_globs:
  - package.json
  - package-lock.json
  - node/*.mjs
  - src/okf_devkit/scaffold/hooks/*
  - .github/workflows/release.yml
  - scripts/release-*.mjs
  - scripts/package-smoke.mjs
related:
  - /project/decisions/0002-github-node-distribution.md
  - /project/releases/v0.1.0.md
  - /cli/node-runtime.md
  - /agents/completion-hooks.md
  - /render/output-cleanup.md
---

# AIにokf-devkitの導入と更新を依頼する

明示的な導入・更新依頼を受けたAIの作業手順。日々の文書更新は [日常操作ガイド](/agents/operate-okf.md) の別責務とし、自動アップデータを設置しない。
本体はGitHubから取得し、依存の取得にはnpmを使う。Python版の既存利用は継続できる。
この文書のRelease経路は別途承認された公開後に使う。v0.1.0はタグ用workflow全10jobと3assetの検証済みDraftがあるが、現在未公開。公開済みPreReleaseの取得・実利用者への導入は未実施。機能・移行事項は [公開予定ノート](/project/releases/v0.1.0.md)、配布担当の工程は [公開手順](/agents/release-node.md) を参照する。公開前は確認済み完全Git SHAのソース経路を選ぶ。
既存v0.1.0の検証済みtgzはタグ対象12cdb44の固定バイトで、同梱READMEには修正前のPyPI例と古い公開状態の説明が残る。今回のリポジトリ文書修正はそのassetへ反映されないため、現在のこの導入ガイドを参照する。タグの移動、再pack、既存assetの差替えで案内を更新しない。
配布担当の人はworkflowの全job完了とDraftのasset確認後にのみPublishする。upload直前のDraft再確認は行うが、GitHub APIの原子的条件ではなく同時publishの完全防止は保証しない。既に公開済みのReleaseは読み取り照合だけとする。

## 1. 環境と既存状態を読む

対象repoの入口・規約とGit状態、package.json、lockfile、workspace、既存の `okf.yml`、docs、hookとAI設定を読む。
未コミット変更は利用者の作業として保つ。npm/yarn/pnpmの管理方式を勝手に切り替えない。
Node.js 22以上・npm・Gitの版と実体を確認する。WindowsはPowerShell実行ポリシーの影響を避けるため `npm.cmd` を使える。POSIXは `npm` に読み替える。

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

## 3. 取得とインストール

Git経路は利用者が選び、現物のコミットが存在する完全40桁SHAへ固定する。ブランチ名や `latest` を固定版と呼ばない。
現在のv0.1.0タグ対象は `12cdb44c2876b50bd7337a5ea20f7744a27d7802`。ソース導入でこの版を選ぶ場合はnpmのGit URLへこのSHAを指定する。下の195252dは以前の導入実測の履歴であり、現在のタグ対象と混同しない。今回、最新SHAのconsumer導入成功は主張しない。
以下は導入を実測した現行baseline（版0.1.0）の完全SHA。新しい版を依頼された場合は、その版の確認済みSHAへ置き換える。

```powershell
npm.cmd install --save-dev --save-exact --ignore-scripts "git+https://github.com/shirashu687/okf-devkit.git#195252d3354acece9c72c987a9f0ab6559db6aa3"
```

このSHAはWindowsの検証環境で初回導入後にnode_modulesを除去し、別の空cacheから `npm ci --ignore-scripts` で再導入できた。Git global設定を空にし、system設定・URL書換え・SSH agent/鍵/パスワード・対話認証を無効にした条件でlockfileのバイト保持とCLIのstrict lint/renderを確認した。
lockfileのresolvedはSSH形式へ正規化されたが、内部transportの詳細は観測していない。全OS・全npm版の再現やHTTPSへの内部fallbackは保証せず、導入先でresolvedと実際の再導入を確認する。globalなGit URL書換えや認証変更で回避しない。Release公開後は確認済みの固定HTTPS asset URLを標準とする。

公開済みRelease経路ではGitHubの実在するReleaseから版・asset名・取得URLとSHA-256を読み、ダウンロードしたtgzを照合する。privateの場合は既存の認可された取得経路を使い、URLや記録へtokenを埋め込まない。失敗時は認証/接続を依頼し、repoを公開しない。

このrepoは現在publicであるが、Draft assetは公開前のため通常の匿名取得経路には出ない。公開Releaseとrepoの可視性は別条件で、private repoのReleaseを公開してもrepoの認可は必要である。以下は**公開後に使う予定URLと未実行例**。現在は404となるため、実在する公開Releaseの確認前にダウンロード成功とは扱わない。

```powershell
# 公開後のみ、新しい空の取得ディレクトリで実行
$assetBase = "https://github.com/shirashu687/okf-devkit/releases/download/v0.1.0"
foreach ($assetName in @("okf-devkit-0.1.0.tgz", "release-manifest.json", "SHA256SUMS")) {
    Invoke-WebRequest "$assetBase/$assetName" -OutFile $assetName
}
$releaseManifest = Get-Content release-manifest.json -Raw | ConvertFrom-Json
Get-FileHash okf-devkit-0.1.0.tgz,release-manifest.json -Algorithm SHA256
Get-Content SHA256SUMS
$releaseManifest
```

manifestのrepositoryが`shirashu687/okf-devkit`、tag=`v0.1.0`、version=`0.1.0`、commit=`12cdb44c2876b50bd7337a5ea20f7744a27d7802`と一致するか照合する。filesが期待するtgz1件のみで、名前・実ファイルサイズ・SHA-256が一致することを確認する。計算したtgzとmanifestのhashをSHA256SUMSの対応する両行へ照合し、欠落・余分なasset・不一致なら停止する。公開後の実取得/hash確認はまだ実行していない。

Python版は選んだ仮想環境で`python -m pip install "git+https://github.com/shirashu687/okf-devkit.git@12cdb44c2876b50bd7337a5ea20f7744a27d7802"`、または同じSHAのcloneで`python -m pip install -e .`を使う。Python3.11以上、Gitと依存取得が必要。本体のPyPI公開とPython wheel/sdist assetはないため、`pip install okf-devkit`を取得手順としない。

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

ローカル版はrepoルートから実ファイルを明示する。現行CLIの `--version` に依存せず、インストール済みmanifestで版を確認する。

```powershell
node -p "JSON.parse(require('node:fs').readFileSync('node_modules/okf-devkit/package.json','utf8')).version"
node node_modules/okf-devkit/node/cli.mjs --help
```

選んだSHA/tgzの由来をlockfileと照合する。package.jsonの版文字列だけでGitコミットを証明しない。
workspace等で配置が異なる場合は実際のインストール先を解決して同じCLIファイルを呼ぶ。
`npx okf` / `npm exec -- okf` は未導入時に別パッケージを取得し得るため、導入確認前の検証には使わない。
globalの場合もbin shim/対象packageを解決してNode版であることを確認する。

## 5. 初期化とAI設定を別に扱う

インストールだけでは `init` やAI設定変更を実行しない。初期化の依頼がある場合、レイヤー/ソースglob/生成先を調べ、生成するファイルを確認して実行する。

```powershell
# app と src/** は対象repoへ合わせる
node node_modules/okf-devkit/node/cli.mjs init --layer "app=src/**"
node node_modules/okf-devkit/node/cli.mjs index --write
node node_modules/okf-devkit/node/cli.mjs lint
node node_modules/okf-devkit/node/cli.mjs render --check
```

現行 `init` は既存ファイルをスキップし、`--force` は対象ファイル全体を置換する。管理部分だけを更新する仕組みではない。
既存 `okf.yml`、文書、hookやAI入口は、保存した変更前内容と差分を取り、所有範囲が分かる部分だけを更新する。利用者の編集があれば調整し、競合時は止める。`init --force` を更新手段にしない。
AI設定・終了hookは [終了hook手順](/agents/completion-hooks.md) の製品別対応と信頼を確認し、repo内の承認済み箇所だけを扱う。global hookは変更しない。
インストール版の選択だけでhookの実行版は決まらない。ローカル/主worktree/Python/開発checkoutの探索順と実配置を確認し、選んだNode版へ到達することを検証する。実AIイベント未検証ならその限界を報告する。
生成物のignoreも差分で確認する。HTMLの保存・旧出力整理は [cleanup手順](/render/output-cleanup.md) の別操作とする。

## 6. 明示依頼による更新と復旧

更新前に現行版・取得元・lockfile・Node/npm版とmanifestを保存する。設定/文書/hook/生成物のバックアップはパッケージ復旧用と区別する。
指定された新SHA/公開済みassetへ更新し、手順4と対象repoの検証を実施する。設定更新は手順5の既知範囲の差分のみ。
失敗時は今回変更したmanifestとlockfileを保存内容へ戻し、npm管理repoなら `npm.cmd ci --ignore-scripts` で保存した依存状態を再作成する。ciはnode_modulesを入れ替えるため、その影響も事前に確認する。必要な既存buildは承認済みの別工程とする。globalの復旧は保存した旧tgz/取得元を `--ignore-scripts` 付きで再導入する。
設定/文書/HTMLはそれぞれのバックアップから競合を確認して戻す。後から加わった利用者編集を上書きせず、`git reset --hard` や無関係な変更の一括取消を使わない。

## 7. アンインストールと報告

ローカルnpm依存の撤去は承認済み範囲で `npm.cmd uninstall --save-dev okf-devkit`、global選択時だけ `npm.cmd uninstall --global okf-devkit` を使う。既存管理方式が別ならそれに従う。
OKF文書・設定・HTML・AI設定をパッケージ撤去と一緒に削除しない。今回追加したhook/設定の既知箇所だけを差分確認し、撤去の依頼がある場合に調整する。
報告には対象repo、導入元・版・実CLI、変更ファイル、検証結果、未確認の実AIイベント、復旧方法を記す。private認証情報や全文ログを貼らない。

## AIへ貼り付ける依頼文

> このrepoにokf-devkitのNode版を導入してください。docs/agents/install-okf.mdを読み、Node22以上/npm/Git、既存manifest・lockfile・workspace・Python/globalのokfを調べてください。本体はGitHubの確認済み完全SHAまたは公開済みReleaseの固定tgz、標準はrepo-localです。初期化とAI設定は別に提案し、既存ユーザー編集を守ってください。未承認の新しいmanifest管理やglobal変更は具体的な差分案で確認してください。実CLIと版・由来を検証し、更新/rollbackの保存元と結果を報告してください。自動更新、init --force、npm本体公開は行わないでください。

## 公式資料

- [npm install](https://docs.npmjs.com/cli/v11/commands/npm-install/)：Git/tgz依存と導入方式
- [npm ci](https://docs.npmjs.com/cli/v11/commands/npm-ci/)：lockfileに基づく再導入
- [npm exec](https://docs.npmjs.com/cli/v11/commands/npm-exec/)：未導入パッケージの取得
- [GitHub Releaseの管理](https://docs.github.com/en/repositories/releasing-projects-on-github/managing-releases-in-a-repository)：Draftと公開操作
