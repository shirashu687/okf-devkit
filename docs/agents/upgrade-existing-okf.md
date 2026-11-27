---
type: How-To
title: 既存リポジトリの okf-devkit を更新する
description: 導入方式や設定が異なるリポジトリで、現状の棚卸しから必要な設定差分の確認までを進める手順と AI への依頼文。
tags: [agents, upgrade, migration]
status: stable
layer: shared
generated:
  by: codex/gpt-6
  at: "2026-11-27T00:00:00Z"
code_globs:
  - src/node/scaffold.mjs
  - src/okf_devkit/commands/init.py
  - src/okf_devkit/scaffold/**
related:
  - /agents/install-okf.md
  - /agents/operate-okf.md
  - /agents/completion-hooks.md
  - /cli/commands.md
  - /render/output-cleanup.md
---

# 既存リポジトリの okf-devkit を更新する

導入先に合う設定を残しながら、CLI と OKF バンドルを更新する。okf-devkit **v0.2.0** は配布パッケージのバージョン、OKF **0.3** はルート `index.md` が宣言する文書仕様のバージョン。CLI の更新とバンドルの仕様変更は別々に確認する。配布前に手順を試す場合は、対象機能を含むレビュー済みの完全 SHA を指定する。公開版の取得・照合は [導入ガイド](/agents/install-okf.md) に従う。

## 利用先の AI に貼り付ける依頼文

`<対象版>` は、公開済みのリリースタグまたは確認済みの完全 Git SHA に置き換える。先に「診断のみ」で実行し、差分が分かったら「指定した差分を反映」に変更できる。

```text
このリポジトリに導入済みの okf-devkit を調べ、対象版へ更新できるようにしてください。
対象版: <対象版>
作業モード: 診断のみ
OKF 文書仕様: 現行を維持。0.3 への変更は、影響と手順を提案してください。

1. リポジトリのルールと Git 状態、CLI の実体と版、導入元の固定方法、manifest・lockfile を確認してください。
   okf.yml、バンドルルートと index.md の版、既存の文書・テンプレート・レイヤー・履歴パス、
   Git 除外、エージェント設定と hooks、生成 HTML の配置を確認してください。複数バンドルは個別に扱ってください。
2. 利用先の CLI で可能なら doctor を実行し、対象版の upgrade --check で現行設定を比較してください。
   コマンドがない版では実体や設定を手で調べます。対象版を使う必要があるときは、既存作業ツリーを変更せずに確認できる環境を使ってください。
   診断結果を「そのまま使う」「追加・変更する」「判断が必要」に分け、根拠、対象ファイル、変更案を示してください。
3. 「指定した差分を反映」の場合は、指定した対象だけを更新してください。既存のパッケージ管理方式と CLI 起動方法を保持し、
   既存の未コミット変更、プロジェクト固有の設定・文書・hooks を保護してください。init --force での置換は避けてください。
   OKF 0.3 への変更を指定した場合は、下の「バンドルを OKF 0.3 に切り替える」に従ってください。
4. 更新後は選んだ CLI の実体・版を確認し、lint、index --check、render --check、stale を実行してください。
   生成差分は管理領域だけを確認し、必要なら index --write の後に再検査してください。
   変更点、実行した検証と結果、未検証事項、差分単位の戻し方を報告してください。
```

手順は [このガイドの URL](https://github.com/shirashu687/okf-devkit/blob/main/docs/agents/upgrade-existing-okf.md) と一緒に渡すか、利用先が URL を取得できない場合は本文を渡す。

## 導入先ごとの確認

| 対象 | 確認する内容 |
| --- | --- |
| CLI と依存 | npm / pnpm / Yarn / Python のうち実際に使っている手段と、manifest・lockfile・固定された配布元を照合する。Node のローカル起動や Python の仮想環境を使い、`--version` がない版はパッケージのメタデータから確認する。 |
| `okf.yml` | 実際のルート、`layers` / `layer_dirs`、順序に意味のある `layer_map`、`log.paths` / `log.baseline`、`index.link_style`、文書やコード走査の除外を照合する。既定値と同じ項目でも、明示設定した理由を確認できるまでは保持する。 |
| 案内とテンプレート | 既存の `AGENTS.md`、`CLAUDE.md`、執筆規約、雛形のうち、CLI の起動表記や生成先が古い部分を直す。利用先独自の説明、語彙、テンプレートは差分を見て残す。 |
| hook・Git 除外 | 実際に使うエージェントの設定と呼出先を追う。`doctor` の hook 表示は静的確認。イベントを試した場合は別途記録する。既存の `.gitignore` に必要な規則だけを足し、実際の出力ファイルで `git check-ignore` を確認する。 |
| 旧 HTML | 生成先と Git 状態を確認し、必要なら `render --cleanup-from <旧出力先> --check` で候補を出す。削除・移動は別の作業として、手書きや由来不明のファイルを保持する。 |

`upgrade --check` が使える場合は、初期化時と同じ `--agent` / `--runner` を選ぶ。比較一覧の「手動確認」は、該当ファイルを配布雛形・ガイドと比較して判断する。不明な初期化オプションは推定として報告する。初回設定との比較が必要なら、別の空ディレクトリで初期化して参照する。

## バンドルを OKF 0.3 に切り替える

OKF 0.3 対応の CLI が動作することを確認し、先に現在の版で検査結果と差分の基準を取る。未宣言のバンドルも、版を決めるまでは現行のまま扱う。

1. `resource`、`sources[].resource`、`computation`、`executor.resource`、`attester.resource`、`superseded_by` のうちローカルを指す値を確認する。文書からの相対パス、またはバンドルルートからの `/...` 表記に直す。バンドルルートへの旧版の再試行だけで解決している値を優先する。URI、クエリ、フラグメント、出典の範囲を記した説明は意味を保つ。
2. `generated.at` と `verified[].at` の前後関係を確認し、過去の検証履歴を保存する。信頼表示を上げる目的で履歴や時刻を書き換えない。必要な文書を実際に再確認する。`stale_after` に時刻を書く場合はオフセットを含め、日付だけなら UTC の開始時刻になることを確認する。
3. ルートの `index.md` の frontmatter に `okf_version: "0.3"` を設定する。任意の `title`、`description`、`license` と拡張キー、手書きの前後文を残す。生成マーカーの中は CLI の索引更新に任せる。導入先が持つ独自の執筆規約と必須チェックも確認する。
4. 変更前後の diff と検査結果を確認し、固定した CLI の版と仕様変更を記録する。戻す場合は、この更新で触ったパッケージ固定とロックファイル、版宣言、移行対象の個別差分を元に戻す。並行作業の変更を含む一括リセットは避ける。

[上流の OKF 0.3 変更一覧](https://github.com/open-knowledge-format/open-knowledge-format/blob/527e81aff55992be21507e97004286789126f88c/SPEC.md#13-changes-from-v02)
