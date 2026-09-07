---
type: Backlog Item
title: okf new doc 直後に lint の warn が出ないようにする
description: okf new doc が置くプレースホルダがそのまま lint の warn になるため、生成直後のファイルが規約を満たさない。
tags: [cli]
status: stable
layer: cli
generated:
  by: "process:okf-cli"
  at: "2026-08-26T12:49:03Z"
state: todo
priority: medium
effort: M
feasibility: B
ai: assisted
cost: false
created: "2026-08-26"
done_at: null
related:
  - /backlog/B-0002-ci-self-lint.md
---

# okf new doc 直後に lint の warn が出ないようにする

## やりたいこと

`okf new doc` で作った直後のファイルが、そのままで `okf lint` を warn 0 で通るようにする。

## 背景・現状

実測（このリポジトリで確認）:

```console
$ okf new doc --layer cli --type "Reference" --title "placeholder probe" --slug probe
docs/cli/probe.md
$ okf lint
docs/cli/probe.md:11 warn L10 `code_globs: <リポジトリルートからのパス or glob>` にマッチするファイルがありません
docs/cli/probe.md:13 warn L11 `related` のリンク先が存在しません: </関連ドキュメントのバンドル相対パス>
```

- `cmd_new()` が `set_fm_field()` で埋めるのは `type` / `title` / `layer` / `generated.by` /
  `generated.at` の 5 つだけ。`_templates/*.md` の `code_globs` と `related` はプレースホルダのまま残る。
- `okf sync --gate` は error だけを exit 2 の対象にするのでエージェントは止まらないが、
  「新規作成した直後のファイルが lint に引っかかる」状態は warn を無視する癖をつける。
  [B-0002 CI で自リポジトリの docs バンドルを検証する](/backlog/B-0002-ci-self-lint.md) で `okf lint --strict` に上げたくても、これが残っていると上げられない。
- 併せて軽微な不具合が 1 つ。`cmd_new()` の H1 置換に使う正規表現は末尾が `\s*$` で、
  この `\s*` が直後の改行まで食う。そのため生成物では H1 の次の空行が消え、
  `# タイトル` の直後にいきなり `## やりたいこと` が来る。

## 進め方

設計判断が要るので、まず方針を決める。

| 案 | 内容 | 評価 |
|---|---|---|
| A | `okf new doc` に `--code-globs <glob>`（複数可）を足し、`code_globs` を必須型では必須にする | 生成時点で更新検知の起点が決まる。AGENTS.md の「`code_globs` に必ず根拠コードを書く」とも整合する |
| B | プレースホルダ行を削って `code_globs: []` にする | warn は「`code_globs` がありません」1 件に減るだけで、0 にはならない |
| C | lint 側でプレースホルダ（`<...>`）を warn 対象から除外する | 書き忘れも見逃すので不可 |

A を軸に、`related` は常に空リストで生成する（プレースホルダを残さない）のが妥当。

1. `p_new_doc` に `--code-globs`（`nargs="+"`）を足し、`set_fm_field()` で `code_globs` を差し替える。
2. `CODE_GLOBS_REQUIRED_TYPES` の型で未指定なら、`OkfError` で「`--code-globs` を指定してください」と落とす。
3. `related` のプレースホルダ行を削除し、`related: []` にする。
4. H1 置換の正規表現の末尾を、改行を含まない空白だけにマッチする形へ直し、直後の空行を残す。
5. `tests/test_new.py` に「生成直後のバンドルが lint warn 0 で通る」ケースを足す。

## 完了条件

- [ ] `okf new doc` の生成直後に `okf lint` が warn 0 で通る
- [ ] H1 の直後の空行が残る
- [ ] `tests/test_new.py` に回帰テストがある
- [ ] 影響ドキュメントを更新した（`okf affected` の出力）
- [ ] 該当層の `log.md` に追記した
- [ ] 本ファイルの `state` を `done` にし `done_at` を記入した

## 結果

<完了時に記入する。PR / コミットへのリンク、実際に変更したファイル、想定と違った点。>
