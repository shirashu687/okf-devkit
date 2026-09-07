---
type: Backlog Item
title: okf init が作る shared 層 log.md の位置を設定と一致させる
description: okf init が作る shared 層の log.md が設定の指す場所と食い違い、履歴が二か所に割れるのを直す。
tags: [scaffold]
status: stable
layer: scaffold
generated:
  by: "process:okf-cli"
  at: "2026-08-26T12:49:03Z"
state: todo
priority: high
effort: S
feasibility: A
ai: full
cost: false
created: "2026-08-26"
done_at: null
related: []
---

# okf init が作る shared 層 log.md の位置を設定と一致させる

## やりたいこと

`okf init` が生成する shared 層の `log.md` の位置を、同じ init が書き出す `okf.yml` の
`log.paths.shared` と一致させる。

## 背景・現状

init 直後の生成物と設定が食い違っている。

| 何が | どこを指しているか |
|---|---|
| `cmd_init()` | `emit(f"{bundle_root}/project/log.md", empty_log("shared"))` → **`docs/project/log.md`** を作る |
| `_render_okf_yml()` が書く `okf.yml` | `log.paths.shared: log.md` → **`docs/log.md`** |
| 同梱の `defaults.yml` | `log.paths.shared: log.md`（コメントも「shared（= バンドルルートの log.md）」と明記） |

`Bundle.log_path()` は `log.paths` を正とするため、`okf log --layer shared --write` を実行すると
`docs/log.md` が**新規作成**される。init が作った `docs/project/log.md` は永久に空のまま残り、
shared 層の履歴が二か所に見える状態になる。

このリポジトリでは暫定対応として、init が作った `docs/project/log.md` を `docs/log.md` へ移動済み
（`defaults.yml` のコメントに合わせた）。`docs/project/` は `okf new doc --layer shared` を実行した
時点で作られるので、空ディレクトリを先に用意する必要はない。

## 進め方

1. どちらに寄せるかを決める。`defaults.yml` のコメントが「shared = バンドルルートの `log.md`」と
   明言している以上、**init 側を直す**のが筋。
2. `cmd_init()` の `emit(f"{bundle_root}/project/log.md", ...)` を `emit(f"{bundle_root}/log.md", ...)` にする。
3. `tests/test_init.py` に回帰テストを足す ——「init 直後の shared log が `log.paths.shared` の
   指す場所に 1 つだけ存在する」。
4. `AGENTS.md.tmpl` の構成表で `project/` を説明している行が log.md の位置に触れていないか確認する。
5. CI の `smoke` ジョブに `test -s docs/log.md`（`okf log --layer shared --write` の後）を足すと、
   同じ食い違いが再発したときに気づける。

## 完了条件

- [ ] `okf init` した直後のリポジトリで `okf log --layer shared --write` を実行しても、新しい `log.md` が増えない
- [ ] `tests/test_init.py` に回帰テストがある
- [ ] 影響ドキュメントを更新した（`okf affected` の出力）
- [ ] 該当層の `log.md` に追記した
- [ ] 本ファイルの `state` を `done` にし `done_at` を記入した

## 結果

<完了時に記入する。PR / コミットへのリンク、実際に変更したファイル、想定と違った点。>
