---
type: How-To
title: 生成済みHTMLを別の出力先へ整理する
description: renderの計画表示、未編集生成物の退避、識別できない旧版出力と失敗時の扱いを説明する。
tags: [render, migration]
status: stable
layer: render
generated:
  by: codex/gpt-6
  at: 2026-10-03T10:19:54Z
code_globs:
  - src/okf_devkit/render_cleanup.py
  - src/okf_devkit/renderer.py
  - src/okf_devkit/cli.py
  - node/render-cleanup.mjs
  - node/renderer.mjs
  - node/cli.mjs
  - tests/test_render_cleanup.py
  - tests/node/render-cleanup.test.mjs
  - tests/node/cleanup-compatibility.test.mjs
related:
  - /cli/node-runtime.md
---

# 生成済みHTMLを別の出力先へ整理する

`render --output` は生成先の指定であり、以前の出力先を自動で移動・削除しない。`--cleanup-from` を明示したときだけ、確認できた旧生成物を退避する。PythonとNodeで同じ手順を使う。Markdownを正本として保持し、整理対象にしない。

## 計画を確認してから実行する

```bash
okf render --output _site --cleanup-from docs --check
okf render --output _site --cleanup-from docs
```

`docs` は実際の旧出力先に合わせる。`--check` は新出力の生成可能性と移動・保持の計画を表示し、出力、manifest、退避先を一切作らない。内容と対象を確認してから `--check` を外す。Stop hookには整理オプションを設定しない。`--hook` との併用は書込み前に拒否する。

## 生成物の識別

通常のCLI renderは出力成功後に `.okf-render-manifest.json` を原子的に記録する。version、generator、リポジトリ相対の出力先、HTMLと共有CSS/JSの出力相対パス・SHA-256を保持する。整理時はパス形式、範囲、生成物の種類と現在のハッシュを確認し、編集されたファイルを移動しない。manifest自身やソースMarkdownは移動対象に含めない。

manifestのない旧版は、旧出力先で現在のレンダラーが作る計画とバイト単位で完全一致するHTMLと共有CSS/JSだけを対象にする。古い版の見た目・編集・判別できないファイルは残す。生成ヘッダーだけを根拠に削除せず、全HTMLの一括削除も行わない。削除済みMarkdownに対応する旧HTMLは、正常なmanifestで未編集と確認できる場合だけ退避できる。

## 範囲と実行順序

旧新出力先はリポジトリ内の別ディレクトリとし、同一・入れ子・リポジトリルート・symlinkやWindows junctionを拒否する。`.okf/render-backups/` を出力先にしたり、その退避領域を包含する出力先を整理したりしない。新出力先の対象ファイルが手書き・編集済みなら、衝突として書込み前に失敗する。

新出力とそのmanifestの生成に成功してから、旧ファイルのハッシュを再確認して退避する。退避先は `.okf/render-backups/<id>/` の新規ディレクトリで、旧リポジトリ相対パスを保持する。`receipt.json` は旧新の関係と全対象の旧パス・退避パス・ハッシュをコピー前に記録し、完了したコピーと移動、復旧状態を原子的に更新する。整理対象がゼロなら退避ディレクトリを作らない。旧manifestは残る場合があるため、再実行でも毎回現在のファイルを照合する。

途中失敗では既に退避した旧ファイルの復元を試みる。元パスに別ファイルが現れた場合は上書きせず、退避物とreceiptに復旧情報を残して失敗を返す。新出力まで巻き戻す保証はない。別プロセスで同じ出力を変更しながら整理しない。

## 復元と確認

receiptの旧パス、退避パス、記録したハッシュを確認し、復元先にファイルがない場合だけ元へ戻す。既存ファイルやMarkdownを上書きしない。判別できない旧HTMLの扱いや退避物の保持期間は、実ファイルを確認して別途決める。

`.gitignore` へ `_site/`、`.okf-render-manifest.json`、`.okf/render-backups/` を追加する。HTML・manifest・退避ファイルをソース文書として管理しない。低水準のrenderer APIの既定出力・通常動作は維持し、整理はCLIの明示指定で行う。
