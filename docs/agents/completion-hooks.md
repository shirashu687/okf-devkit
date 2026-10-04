---
type: How-To
title: エージェント終了時の共通HTML生成
description: Claude、Copilot、Codexでリポジトリ共通のHTML生成を呼ぶ設定と検証範囲。
tags: [agents, hooks, render]
status: stable
layer: shared
generated:
  by: codex/gpt-6
  at: 2026-10-04T03:34:44Z
code_globs:
  - .okf/hooks/*
  - .claude/settings.json
  - .github/hooks/*.json
  - .github/copilot-instructions.md
  - .codex/hooks.json
  - tests/test_repo_hooks.py
related:
  - /cli/node-runtime.md
  - /render/index.md
---

# エージェント終了時の共通HTML生成

この設定は **このリポジトリの作業終了時に `_site/` を生成する**。Claude専用の生成処理ではなく、同じ `render --hook` を各ツールから呼ぶ。CopilotとCodexはツールの名前であり、GPTなどのモデルを切り替えても共通コマンドを使える。`okf init` の配布内容や利用者のグローバル設定は変更しない。

## 共通処理と終了イベント用アダプター

手動実行はリポジトリ内で以下を使う。成功時は標準出力 `{}` と終了値0、失敗時は非0と診断を返す。hookが使えない環境でも、この終了値をそのまま確認する。

```sh
sh .okf/hooks/render_hook.sh
```

```powershell
powershell -NoProfile -File .okf/hooks/render_hook.ps1
```

`.okf/hooks/agent_stop.sh` / `.ps1` は終了イベント向けのadvisoryアダプターで、同じ厳格なラッパーを呼ぶ。子コマンドの標準出力を抑え、成功・失敗とも `{}` と終了値0を返す。失敗の診断は標準エラーへ残す。終了値2、`decision: block`、継続要求を返さず、入力JSONや会話本文を実行・表示・保存しない。生成の成功をテストの成功として扱わない。

各登録には30秒（Claude）または60秒（Copilot/Codex）の上限がある。ツール側のtimeout、起動不能、セッション終了などではアダプター自体が完了できない場合がある。hookの常時成功や診断のUI表示までは保証しない。生成はローカル処理のみで、モデル呼出し、公開、`--cleanup-from` による出力先移行・旧出力退避は行わない。通常renderの対象出力内では、所有する古い生成HTMLの削除が従来どおり行われる。

## ツールごとの対応範囲

2026-10-04に下記の公式資料を確認した。設定・シェル起動・実コマンドはローカルで検証するが、認証操作や有料モデルのターンを開始して実終了イベントを発火する検証は行っていない。

| ツール・環境 | リポジトリ設定 | 利用条件・未検証範囲 |
| --- | --- | --- |
| Claude Code CLI | `.claude/settings.json` の `Stop` | 既存のbash設定を維持。GitとPOSIX shellが必要。実Stopイベント未検証。 |
| GitHub Copilot CLI | `.github/hooks/okf-render.json` のversion 1 `agentStop` | 起動時に設定を読み込む。bash / PowerShellを環境に合わせて使用。実agentStop未検証。ローカルCLI 1.0.25のversion表示のみ確認。 |
| Copilot cloud agent | 同じ `.github/hooks/okf-render.json` | 対象ブランチにファイルが存在し、Linuxでbash/Git/生成runtimeが利用できること。PowerShell設定は無視される。実クラウドjob未検証。 |
| VS Code Copilot Local | 同じCopilot互換ファイル | PreviewのLocal実装が互換形式をマッピングする。信頼済みworkspaceと `chat.useHooks` が前提。二重のnative設定は追加しない。実Localイベント未検証。 |
| VS Code Agent Host | provider固有設定による | Localの設定・payload・`chat.useHooks` をそのまま同一視しない。ここでは接続・登録・実イベント未検証。共通コマンドを手動で使う。 |
| Codex CLI | `.codex/hooks.json` の `Stop` | プロジェクト設定の信頼と `/hooks` によるhook hashの確認が必要。変更後は再確認する。CLI 0.159.0のversion表示とWindows/POSIXコマンド起動を確認、実Stop未検証。 |
| Codex IDE | 同じruntimeの対応・信頼状態による | repo設定の読み込みとhook信頼を環境で確認する。実IDEイベント未検証。 |
| Codex cloud | repo設定の自動発見・信頼は未確認 | 自動Stop hookの動作を保証しない。共通コマンドまたは作業指示による手動実行を使う。 |

Codexの起動cwdはセッションのcwdなので、登録コマンドはGitルートを解決する。Windows用 `commandWindows` はPowerShellを明示して起動し、空白を含むリポジトリの子ディレクトリからも確認している。信頼を迂回するフラグやExecutionPolicy Bypassは使わない。プロジェクト設定では無視される `notify` をrepoに追加せず、ユーザー設定へも書き込まない。

Copilotは互換設定の `.claude/settings.json` も追加で読み込む。そのためこのリポジトリでは、Claude用StopとCopilot用agentStopが同じ終了で両方動き、HTML生成が二度走る可能性がある。既存のClaude機能を自動で外さず、両方をadvisoryにする。連続生成でもMarkdown正本は変わらず、`--cleanup-from` による出力先移行・旧出力退避やモデル継続は起きない。生成物の再書込みと実行時間は発生し、二つのtimeout上限もそれぞれ適用される。イベントpayloadからツールを推測して重複を抑制しない。

## runtimeと手動フォールバック

厳格なラッパーはローカルnpmパッケージ、primary worktreeの依存、Python環境、開発checkoutを探索する。詳しい順序は [Node/Python実行経路](/cli/node-runtime.md) を参照する。クラウドではこのWindows PCのvenvやprimary worktreeを前提にせず、その環境にNode.jsとcheckoutの依存を準備するか、Pythonへ `okf-devkit` をインストールしてPATHから利用可能にする。hook内でインストールや認証は行わない。

hookが未対応・無効・未信頼なら、作業終了前に上の手動コマンドを実行する。`.github/copilot-instructions.md` も同じ手順とAGENTSの検証規約を参照する。失敗時は実際の終了値と診断を記録し、生成されたHTMLだけで完了を判断しない。

## 公式資料

- [Copilot hooks reference](https://docs.github.com/en/copilot/reference/hooks-reference): completion event、互換sources、cloudのshell制約。
- [Copilot CLIでhookを使う](https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/use-hooks): リポジトリ内の設定と起動時読込み。
- [VS Code hooks](https://code.visualstudio.com/docs/agent-customization/hooks) と [Local hooks reference](https://code.visualstudio.com/docs/agents/reference/hooks-reference): Preview、互換形式、workspaceの信頼、LocalとAgent Hostの違い。
- [Codex hooks](https://developers.openai.com/codex/hooks): repo設定、Stop、OS別コマンド、hookの信頼。
- [Codex advanced configuration](https://developers.openai.com/codex/config-advanced) と [configuration reference](https://developers.openai.com/codex/config-reference): notifyの形式とproject設定での制限。
