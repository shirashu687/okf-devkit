# 作業記録: <task-id-or-slug>

このファイルは1作業1枚の状態記録であり、仕様・チケット・会話全文の複製ではない。通常・大の作業、または中断して別セッションへ渡す作業で使う。配置は [config.md](../../project/config.md) の「作業記録と引継ぎ」で定める journal 配下の `<task-id-or-slug>.md` とする。

## メタデータ

| 項目 | 値 |
| --- | --- |
| 課題ID / 作業名 | `<task-id-or-slug>` |
| 状態 | `進行中` / `完了` / `中断` |
| 作業場所 | `<absolute path or repository name>` |
| ブランチ | `<branch>` |
| 開始日時 / 最終更新日時 | `<timestamp>` / `<timestamp>` |
| 開始SHA | `<commit SHA>` |
| 最新HEAD | `<commit SHA>` |
| 作業者 / 製品 / モデル | `<actor>` / `<product>` / `<model>` |
| 証拠の保存先 | `<paths or URLs; omit secrets>` |

## 目的・範囲

### 目的

<依頼された結果を一文で書く。>

### 対象

- <変更する領域>

### 対象外

- <今回実施しない領域>

### 完了条件

仕様・チケットへの参照だけを書く。本文を複製しない。

- <参照: path / section / acceptance id>

## 開始時の状態

開始SHAだけでは対象版を特定できない。開始時に存在した利用者の変更と、今回の変更を区別して記録する。

### 開始時から存在する変更

- 変更済み: `<path>` — <要約>
- 未追跡: `<path>` — <要約>
- なし / 確認方法: `<command or method>`

### 今回の変更

- 変更済み: `<path>` — <要約>
- 未追跡: `<path>` — <要約>

## 判断と根拠

今回の作業を完了するために必要な判断だけを、根拠への参照とともに記録する。恒久知識になった判断は仕様、CONTEXT、ADRへ移す。

| 判断 | 根拠 | 影響 |
| --- | --- | --- |
| <decision> | <path / section / observation> | <affected scope> |

## 摩擦観測とretroゲート

開始・再開時に [振り返り・改善台帳手順](../procedures/retrospective.md) と config が示す `harness/ledger.md` の期限・見直し対象を確認する。作業中は事実と根拠だけを短く記録し、原因の仮説、回数、改善効果を捏造しない。完了・中断時に次を埋め、台帳の詳細を複製しない。

| 項目 | 記録 |
| --- | --- |
| 確認範囲 | <依頼・既決要件・差分・検証/再試行・review・引継ぎの照合範囲> |
| 該当条件と根拠または非該当理由 | <SPEC §7.1のトリガー、根拠、またはトリガーなしの理由> |
| 短い観測メモ | <症状・対象版・操作・出力・根拠の所在。なければ「なし」> |
| 処理済み事象・台帳ID | <未処理だけをfull retroへ送ったか、`IMP-NNNN`、または「なし」> |
| 未確認範囲と次の一手 | <確認できない範囲、妨げ、再開時の具体的な確認> |
| full retrospective | <実施 / 不要 / 確認不能。実施時は候補・台帳更新・判断待ちを参照> |
| 人の判断待ち | <採用・撤去・権限を越える操作のIDと提示資料、または「なし」> |

トリガーなしの回は空のretro文書や台帳行を作らない。根拠不足やretroの実行不能は摩擦なし・実施済みと断定せず、中断または確認不能の限界と次の一手を残す。演習用の入力・出力と実作業の観測を分ける。

## 検証

結果欄は、適用する検証について `成功` / `失敗` / `未実行` / `実行不能` の4値だけを使う。適用しない検査は `適用` を `いいえ` とし、結果値を作らず理由を書く。再試行前の行を削除しない。

| 識別子 | 適用 | 結果 | 対象版・範囲 | コマンド / 確認方法 | 期待条件 | 証拠 | 理由・限界 / 再試行 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| <id> | はい / いいえ | <4値または —> | <HEAD / SHA / files / environment> | `<command or method>` | <expected> | <path / short output> | <reason or limit> |

### 再試行履歴

失敗・未実行・実行不能の後に再試行した場合、前回の結果と最終結果の両方が分かるようにする。

- `<id>` — <timestamp>: <previous result> → <new result>; <reason / changed target>

## review

通常・大・高リスクの変更では、開始SHAを固定比較点にして仕様軸と標準軸を分ける。未コミット・未追跡の対象変更を除外しない。

### 仕様軸

- 比較点: `<start SHA>`
- 対象: `<committed diff / working tree diff / untracked files>`
- 結果: `<findings, fixes, remaining risks>`

### 標準軸

- 比較点: `<start SHA>`
- 標準: `<AGENTS / config / policy / tests / conventions>`
- 結果: `<findings, fixes, remaining risks>`

## 残作業・妨げ・再開前提

### 残作業

- <one concrete remaining action>

### 妨げ

- <blocker, or `なし`>

### 再開前提

- <working directory / branch / dependency / permission / evidence assumption>

## 次の一手

<次に行う操作を一件だけ書く。対象、操作、期待結果を含める。>

## 完了 / 中断要約

<完了なら成果、検証、review、残存リスク、retro判定を要約する。中断なら未完了項目、妨げ、次の一手、最新検証を要約する。>
