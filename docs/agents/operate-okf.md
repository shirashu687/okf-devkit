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
  - src/node/*.mjs
  - src/okf_devkit/scaffold/AGENTS.md.tmpl
related:
  - /cli/commands.md
  - /cli/node-runtime.md
  - /agents/install-okf.md
  - /agents/upgrade-existing-okf.md
  - /agents/completion-hooks.md
  - /render/output-cleanup.md
  - /render/backlog-progress.md
---

# AIが目的から日常のOKF操作を選ぶ

作業前に、対象リポジトリの指示とバンドルの執筆規約を読む。コマンドの引数、書き込み先、終了コードは [コマンド仕様](/cli/commands.md) で確認できる。

例の `okf` は導入済みの CLI に読み替える。ローカルの Node 版ならリポジトリルートから `node node_modules/okf-devkit/node/cli.mjs`、Python 版なら導入済みの環境で `python -m okf_devkit.cli` を使う。対応版の `--version` と `doctor` で起動した CLI と設定を確認できる。`npx okf` は未導入時に別のパッケージを取得する場合がある。利用先にはこのリポジトリの開発用 `harness/` のコピーは不要。

| 目的 | 最小経路 | 次に読む |
| --- | --- | --- |
| コード変更後に文書を合わせる | `affected --base <固定SHA>` → 対象と未カバーを判断 → 本文更新 → `sync` の全診断を確認 | 下記「コード変更後」 |
| 新しい文書を作る | `new doc` → 本文補完 → `index --write` → 規約を検査 | コマンド仕様の根拠コード節 |
| 読み取りだけで点検する | `lint`、`index --check`、`stale`、`render --check` | 下記「結果の判定」 |
| HTMLで読む | `render`（既定 `_site/`）、必要時 `--open` | コマンド仕様の出力先節 |
| 初めて導入する | 環境を確認 → CLI を導入 → バンドルを初期化 | [導入ガイド](/agents/install-okf.md) |
| 導入済みの環境を更新する | 実際の設定を確認 → `upgrade --check` で比較 → 必要な差分を反映 | [更新ガイド](/agents/upgrade-existing-okf.md) |
| backlogを使う | 利用先の課題管理規約を確認 → 採用していれば `new backlog` / `status` | [読み取り専用の進捗表示](/render/backlog-progress.md) |

## コード変更後

`affected --base <固定SHA>` で変更したコードを調べ、`code_globs` が一致する文書の本文を実装と照合する。対応する文書がない変更パス、`code_globs` のない文書、README などバンドル外の文書も確認する。

外部コードは `okf.yml` の `code_sources` に登録し、`affected --source <ソース名> --base <固定SHA>` で確認する。「差分未確認」が出た場合は、対象のチェックアウトと比較対象が手元にあるか確認する。 [外部コードソースの設定](/cli/commands.md)

本文を直した箇所、変更が不要と判断した根拠、追加の確認や修正が必要な箇所を記録する。`generated.at` を更新する場合も本文が現在の実装を説明できているか確かめる。

`sync` はindexとlogを書き込むため、読み取り点検には使わない。index → log → lint → staleの各出力を確認する。
log失敗は警告で継続し得る。Git未導入・未コミット変更・設定範囲・logスキップを確認し、ログ追記の成功を別に判定する。logはコミット済み履歴だけを記録し、今回の未コミット変更は記録しない。必要ならコミット後に承認済みの範囲で `log --write` を実行する。

## 新規文書と既存ファイル

`new doc --layer <layer> --type Reference --title "<title>" --code-globs "<実コードglob>"` で雛形を作る。本文を補い、必要な関連文書を `related` に記載する。目次を更新したら、OKF 0.2 では `lint`、OKF 0.3 でプロジェクト固有の規約も検査する場合は `lint --project` を実行する。
`init` はバンドル設定・雛形・hookを作る初期化で、日常更新に使わない。既存ファイルはスキップし、`init --force` は多くの生成物を置換する。エージェント設定と `.gitignore` はforceでも保持する。既存利用先へ新しい案内を反映する場合は差分を確認して必要箇所だけを更新し、ユーザー編集との競合を止める。
backlogは採用している利用先だけで使う。このrepoの課題はGitHub Issuesで管理する。HTML一覧は読み取り専用で、状態更新は元Markdownと利用先規約に従う。

## 結果の判定と止める条件

`render --check` はメモリ内で HTML を生成できるか点検する。生成済みのファイルとの比較が必要な場合は、出力先を確認して別途差分を調べる。
`stale` は指摘があってもexit0。`sync --gate` は同じlint errorの再検出でexit0になり得る。終了0だけで指摘なし・文書更新完了・CI成功と判定せず、lint、stale、警告、logの各診断を確認する。
`render --hook` はHTMLを書き込む終了hook用操作、`sync --gate` は書き込みと差戻し回数管理を伴う。通常の読み取り点検やCIの合格判定には使わない。advisory終了adapterのexit0はモデルを止めないための扱いで、render成功の証明ではない。
エラー、未知の既存ファイル、logスキップ、未カバーの影響、ユーザー編集との競合があれば、対象と未完了を報告して必要な修正・調整を行う。無関係なファイルや設定を上書きして進めない。
HTML保存や旧出力整理は [cleanup手順](/render/output-cleanup.md)、実AIイベントの対応・未検証範囲は [終了hook手順](/agents/completion-hooks.md) を確認する。

報告は対象repo/比較SHA/実CLI、更新した本文と生成物、各検証結果、更新不要の根拠、未検証・要対応、次の行動を短く記す。課題の受け入れとcloseは利用先の運用・許可に従い、PR作成だけを完了と呼ばない。
