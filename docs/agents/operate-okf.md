---
type: How-To
title: AIが目的から日常のOKF操作を選ぶ
description: AIが日常の目的に応じて読み取り・更新を選び診断と未検証範囲を確認する。
tags: [agents, cli, how-to]
status: stable
layer: shared
generated:
  by: codex/gpt-6
  at: 2026-10-04T09:04:08Z
code_globs:
  - src/okf_devkit/cli.py
  - node/*.mjs
  - src/okf_devkit/scaffold/AGENTS.md.tmpl
related:
  - /cli/commands.md
  - /cli/node-runtime.md
  - /agents/install-okf.md
  - /agents/completion-hooks.md
  - /render/output-cleanup.md
  - /render/backlog-progress.md
---

# AIが目的から日常のOKF操作を選ぶ

バンドルの執筆規約と利用先repoの指示を先に読む。ここは目的別の入口で、全コマンドの入出力・副作用・終了状態の正本は [コマンド仕様](/cli/commands.md)。開発者向けharnessを利用先へコピーしない。
例の `okf` は確認済みCLIに読み替える。ローカルNode版は対象repoから `node node_modules/okf-devkit/node/cli.mjs`、Python版は確認済み環境の `python -m okf_devkit.cli` 等を明示する。裸のPATH上のokfや未導入のnpxで選んだ版を取り違えない。

| 目的 | 最小経路 | 次に読む |
| --- | --- | --- |
| コード変更後に文書を合わせる | `affected --base <固定SHA>` → 対象と未カバーを判断 → 本文更新 → `sync` の全診断を確認 | 下記「コード変更後」 |
| 新しい文書を作る | `new doc` → 本文補完 → `index --write` → `lint` | コマンド仕様の根拠コード節 |
| 読み取りだけで点検する | `lint`、`index --check`、`stale`、`render --check` | 下記「結果の判定」 |
| HTMLで読む | `render`（既定 `_site/`）、必要時 `--open` | コマンド仕様の出力先節 |
| 初回導入・既存導入を更新する | 環境・実CLI・変更案を確認してからinstall/initを分ける | [導入ガイド](/agents/install-okf.md) |
| backlogを使う | 利用先の課題管理規約を確認 → 採用していれば `new backlog` / `status` | [読み取り専用の進捗表示](/render/backlog-progress.md) |

## コード変更後

`affected` は変更コードの `code_globs` 対応を逆引きする。固定した比較SHAを用い、出力された文書の本文を実コードに照合する。
未カバーの変更パス、`code_globs` 未設定の文書、README・harnessなどバンドル外の文書は別に人手で影響を確認する。出力ゼロを「文書更新不要」の証明にしない。
本文を更新した、内容に影響がない根拠を確認した、未検証/要対応が残る、のどれかを記録する。`generated.at` だけを新しくして更新完了にしない。

`sync` はindexとlogを書き込むため、読み取り点検には使わない。index → log → lint → staleの各出力を確認する。
log失敗は警告で継続し得る。Git未導入・未コミット変更・設定範囲・logスキップを確認し、ログ追記の成功を別に判定する。logはコミット済み履歴だけを記録し、今回の未コミット変更は記録しない。必要ならコミット後に承認済みの範囲で `log --write` を実行する。

## 新規文書と既存ファイル

`new doc --layer <layer> --type Reference --title "<title>" --code-globs "<実コードglob>"` で雛形を作り、本文・根拠コード・必要なrelatedを補完する。語彙や必須typeはコマンド仕様を参照する。
`init` はバンドル設定・雛形・hookを作る初期化で、日常更新に使わない。既存ファイルはスキップし、`init --force` は全体を置換する。既存利用先へ新しい案内を反映する場合は差分を確認して必要箇所だけを更新し、ユーザー編集との競合を止める。
backlogは採用している利用先だけで使う。このrepoの課題はGitHub Issuesで管理する。HTML一覧は読み取り専用で、状態更新は元Markdownと利用先規約に従う。

## 結果の判定と止める条件

読み取り点検はファイルを書かない。`render --check` は生成可否をメモリ内で検査し、保存済みHTMLとの差分は比較しない。
`stale` は指摘があってもexit0。`sync --gate` は同じlint errorの再検出でexit0になり得る。終了0だけで指摘なし・文書更新完了・CI成功と判定せず、lint、stale、警告、logの各診断を確認する。
`render --hook` はHTMLを書き込む終了hook用操作、`sync --gate` は書き込みと差戻し回数管理を伴う。通常の読み取り点検やCIの合格判定には使わない。advisory終了adapterのexit0はモデルを止めないための扱いで、render成功の証明ではない。
エラー、未知の既存ファイル、logスキップ、未カバーの影響、ユーザー編集との競合があれば、対象と未完了を報告して必要な修正・調整を行う。無関係なファイルや設定を上書きして進めない。
HTML保存や旧出力整理は [cleanup手順](/render/output-cleanup.md)、実AIイベントの対応・未検証範囲は [終了hook手順](/agents/completion-hooks.md) を確認する。

報告は対象repo/比較SHA/実CLI、更新した本文と生成物、各検証結果、更新不要の根拠、未検証・要対応、次の行動を短く記す。課題の受け入れとcloseは利用先の運用・許可に従い、PR作成だけを完了と呼ばない。
