---
type: Convention
title: ドキュメント執筆規約
description: このバンドルの frontmatter 語彙・リンク規約・index/log 書式を定義する唯一の基準。
tags: [docs, okf, convention]
status: stable
layer: shared
generated:
  by: process:okf-devkit
  at: 2026-09-07T11:39:02Z
related:
  - /AGENTS.md
---

# ドキュメント執筆規約

本リポジトリの `docs/` は **OKF (Open Knowledge Format) v0.2** バンドルである。
仕様本体: <https://github.com/GoogleCloudPlatform/open-knowledge-format>

OKF は「器」の仕様であり、**`type` に何を書くかなどの語彙は規定していない**。本ファイルがその語彙を定義し、`okf lint` が機械的に強制する。

> このファイルは `okf init` が生成した雛形である。**プロジェクトに合わせて自由に書き換えてよい。**
> ただし語彙表（§2 / §5 / §1-1 の `layer`）を変えたら、`okf.yml` の対応するキーも必ず合わせること。
> 食い違うと lint の判定と本ファイルの記述が矛盾する。

---

## 1. frontmatter

### 1-1. フィールド一覧

| フィールド | 区分 | 必須 | 内容 |
|---|---|---|---|
| `type` | OKF 標準 | **必須** | §2 の語彙表の値のみ |
| `title` | OKF 推奨 | 推奨 | 人が読む表示名。`index.md` のリンク文言になる |
| `description` | OKF 推奨 | 推奨 | **一文**の要約（句点1つ、120字以内）。`index.md` の説明文になる |
| `tags` | OKF 推奨 | 任意 | 横断分類の文字列リスト |
| `resource` | OKF 推奨 | 任意 | このドキュメントが指す実体の URI（管理画面 URL 等） |
| `status` | OKF 標準 | 推奨 | `draft` / `stable` / `deprecated`。既定は `stable` |
| `stale_after` | OKF 標準 | 任意 | `YYYY-MM-DD`。この日を過ぎたら見直し対象になる |
| `generated` | OKF 標準 | 推奨 | `{ by: <actor>, at: <ISO 8601> }`。誰がいつ生成したか |
| `verified` | OKF 標準 | 任意 | `[{ by: <actor>, at: <ISO 8601> }]`。誰がいつ検証したか |
| `sources` | OKF 標準 | 任意 | 出典（provenance）。外部仕様書の URL など**実体を一意に指す URI**。glob は書かない |
| `code_globs` | 独自拡張 | **コード由来の文書は必須** | 根拠となるコードのパス/glob のリスト。§3 参照 |
| `layer` | 独自拡張 | **必須** | cli、render、scaffold / `shared` |
| `related` | 独自拡張 | 任意 | 関連ドキュメントのバンドル相対パスのリスト |
| `state` 他 | 独自拡張 | backlog のみ | §5 参照 |

> OKF v0.2 §5 は「プロデューサーは任意のキーを追加してよい」と明示している。`layer` / `related` / `code_globs` / backlog 系はその拡張。

### 1-2. 記述例

```yaml
---
type: Reference
title: API リファレンス
description: 全エンドポイントのリクエスト・レスポンス仕様。
tags: [api]
status: stable
layer: shared
generated:
  by: claude-code/opus-5
  at: 2026-01-01T10:00:00Z
verified:
  - by: human:your-name
    at: 2026-01-01T12:00:00Z
code_globs:
  - src/api/*.ts
related:
  - /project/glossary.md
---
```

### 1-3. Actor 表記（OKF v0.2 §7）

`generated.by` / `verified[].by` は次の3形式のいずれか。

| 形式 | 用途 | 例 |
|---|---|---|
| `<producer>/<version>` | AI エージェント・ツール | `claude-code/opus-5` |
| `human:<id>` | 人間 | `human:your-name` |
| `process:<id>` | 自動プロセス | `process:okf-devkit` |

**`verified` に `human:` が含まれるかどうかで信頼度が決まる**（OKF v0.2 §5.3）。

| `verified` の状態 | 信頼度 | 意味 |
|---|---|---|
| キー無し | *unverified* | LLM が書いたまま、人が未確認 |
| `human:` 以外のみ | *machine-confirmed* | 機械的な確認のみ |
| `human:` を含む | *human-reviewed* | 人がレビュー済み |

### 1-4. `status` と `state` は別物

混同が起きやすいので明記する。

| キー | 対象 | 値 |
|---|---|---|
| `status` | **ドキュメント自体**のライフサイクル（OKF 予約） | `draft` / `stable` / `deprecated` |
| `state` | **backlog アイテムの進捗**（独自拡張） | `todo` / `doing` / `done` / `dropped` |

---

## 2. `type` 語彙表

**この表にない値は使わない**（`lint` が error にする）。値は OKF 仕様の例に合わせて Title Case。

| type | 用途 | 主な置き場所 | テンプレート |
|---|---|---|---|
| `Project Overview` | プロジェクト全体像 | `project/` | — |
| `Architecture` | 構造・データフロー・ER 図 | 各層 / `project/` | `_templates/architecture.md` |
| `Reference` | 一覧・仕様（API / コンポーネント / テーブル） | 各層 | `_templates/reference.md` |
| `How-To` | 手順書・使用ドキュメント | 各層 `guides/` | `_templates/how-to.md` |
| `Decision Record` | 設計判断の記録（ADR） | `project/decisions/` | `_templates/decision-record.md` |
| `Glossary` | 用語集 | `project/` | `_templates/glossary.md` |
| `Backlog Item` | やること1件 | `backlog/` | `_templates/backlog-item.md` |
| `Convention` | 執筆規約 | ルート | — |

`index.md` のセクション順もこの表の順で固定される（差分を安定させるため）。

---

## 3. `code_globs` — 更新検知の起点

**このドキュメントを導出したコードの場所**を書く独自拡張キー。仕組み全体の起点になるので、コード由来のドキュメントには**必ず書く**。

```yaml
code_globs:
  - src/api/users.ts
  - src/api/*.ts          # glob 可
```

- 値は**文字列のフラットなリスト**。リポジトリルートからの相対パス、または glob
- **OKF 標準の `sources` と混同しないこと。** `sources` は出典（provenance）用で、`resource` には「実体を一意に指す URI」を書く仕様であり、glob パターンは書けない。監視用途を標準フィールドに載せると汎用 OKF ツールがリンクを解決できないため、独自キーに分離している（OKF v0.2 §5 は独自キーの追加を明示的に許可しており、consumer は未知キーを保持する）
- **必須となる type**: `Project Overview` / `Architecture` / `Reference` / `How-To`。`Convention` / `Glossary` / `Decision Record` / `Backlog Item` は任意。`status: deprecated` の文書は必須要件から除外される

これにより:

| できること | コマンド |
|---|---|
| コード変更 → 更新すべきドキュメントの特定 | `okf affected --base main` |
| コードが消えた → 陳腐化の検出 | `okf stale`（*orphan*） |
| コードの方が新しい → 内容が古い候補の検出 | `okf stale`（*outdated*） |

---

## 4. リンク規約

OKF v0.2 §6 に従い、**バンドルルート起点の絶対パス**を推奨する。

```markdown
[用語集](/project/glossary.md)        ← 推奨（docs/project/glossary.md を指す）
[同階層のファイル](./other.md)         ← 可
```

- `related` フィールドも同じ絶対パス形式で書く
- **壊れたリンクはエラーにしない**（OKF v0.2 §11 が「壊れたリンクでバンドルを拒否してはならない」と規定）。`lint` は warn に留める
- リポジトリ内のコードを指す場合は、バンドル外なのでリポジトリルートからの相対パスで書く（例: `src/app/main.ts`）

### 4-1. 生成 index のリンク形式

本文と `related` のリンク規約は維持したまま、自動生成される `index.md` のリンクだけを `okf.yml` の `index.link_style` で選べる。

| 値 | 起点 | 例 |
|---|---|---|
| `bundle-absolute`（既定） | バンドルルート | `docs/index.md` → `/project/index.md` |
| `relative` | その `index.md` の親ディレクトリ | `docs/index.md` → `./project/index.md`、`docs/backlog/index.md` → `./T-0001.md` |

許容値以外は設定エラーになる。`index --write` / `index --check` / `lint` / `sync` は同じ設定を使う。`Doc.bundle_rel` と `related` のバンドル起点の意味、ラベル・説明・並び順・マーカーは変わらない。生成リンクの空白・括弧・`%` はMarkdown用にエスケープされるため、本文へ手で転記しない。

---

## 5. Backlog Item 専用フィールド

| フィールド | 値 | 意味 |
|---|---|---|
| `state` | `todo` / `doing` / `done` / `dropped` | 進捗 |
| `priority` | `high` / `medium` / `low` | 優先度 |
| `effort` | `S`(数時間) / `M`(1〜3日) / `L`(1週間〜) / `XL`(数週間〜) | 工数 |
| `feasibility` | `A`(◎すぐできる) / `B`(○やればできる) / `C`(△要調査) / `D`(×現状困難) | 実現可能性 |
| `ai` | `full`(🤖) / `assisted`(🤖△) / `manual`(👤) | AI 活用度 |
| `cost` | `true` / `false` | 💰 コスト発生の有無 |
| `created` | `YYYY-MM-DD` | 起票日 |
| `done_at` | `YYYY-MM-DD` / `null` | 完了日。`state: done` なら必須 |

**ユーザーが書くのは本文の `## やりたいこと` の1〜3行だけ**。ID 採番・frontmatter はスクリプトが、背景・進め方・完了条件は LLM が埋める。

---

## 6. `index.md` の書式（自動生成）

OKF v0.2 §8 に従う。**手で編集しない。**

- `index.md` は **frontmatter を持たない**。唯一の例外はバンドルルート `docs/index.md` の `okf_version: "0.2"` のみ
- エントリ形式は `* [Title](path) - description`
- `path` は `index.link_style` に応じたバンドルルート起点または index 親ディレクトリ起点のリンクになる
- `<!-- okf:auto:start -->` 〜 `<!-- okf:auto:end -->` の間だけがスクリプトの管理範囲。**その外側の前文は手書きしてよく、上書きされない**

```markdown
# server ドキュメント

（ここは手書き。自由に書いてよい）

<!-- okf:auto:start -->
## Reference
* [API リファレンス](/server/api.md) - 全エンドポイントの仕様。
<!-- okf:auto:end -->
```

---

## 7. `log.md` の書式（OKF 標準の粒度）

OKF v0.2 §9 に**そのまま従う**。独自の拡張はしない。

### ルール

1. **日付見出しでグループ化**する。見出しは ISO 8601 の `YYYY-MM-DD` のみ（`## 2026-01-01`）
2. **新しい順**に並べる
3. エントリは**散文**（prose）。箇条書き1項目 = 1つの意味のある変更
4. 先頭の太字プレフィックスは **慣例**であり、OKF が挙げる次の3種のみを使う

| プレフィックス | 使う場面 |
|---|---|
| `**Creation**` | 新規の機能・ファイル・エンドポイントの追加 |
| `**Update**` | 既存の変更・改善・**不具合修正**・リファクタリング |
| `**Deprecation**` | 削除・廃止・非推奨化 |

> 「Fix」は OKF の慣例に無いため使わない。**不具合修正は `**Update**` に含める。**

5. 粒度は **「1つの意味のある変更 = 1エントリ」**。既定では PR マージ単位（`git log --first-parent`）で生成する
6. 出典としてコミットハッシュ（と PR 番号）を行末に添える。`okf log` はこれを既出判定に使うため、**削除しない**

### 例

```markdown
# 変更履歴 — client

## 2026-01-01
- **Creation** ユーザー設定画面を追加した。 ([#12](https://github.com/OWNER/REPO/pull/12), `9fab31b`)
- **Deprecation** 旧テーマ切替 API を削除した。
```

### 配置

| ファイル | 記録するもの | 対応するコード |
|---|---|---|
| `docs/log.md` | リリース・大きな節目のみ（自動追記の対象外） | — |
| `docs/cli/log.md` | CLI 本体とサブコマンドの変更 | `src/okf_devkit/cli.py` ほかパッケージ本体 / `tests/**` |
| `docs/render/log.md` | 閲覧用 HTML 生成の変更 | `src/okf_devkit/renderer.py` / `src/okf_devkit/assets/**` / `tests/test_render.py` |
| `docs/scaffold/log.md` | `okf init` が配る雛形と既定設定の変更 | `src/okf_devkit/scaffold/**` / `src/okf_devkit/defaults.yml` / `tests/test_init.py` |

振り分けの正は `okf.yml` の `layer_map`（上から順に最初にマッチした層を採用する）。
この表を変えたら `layer_map` も必ず合わせること。

`docs/**` / `.okf/**` / `.claude/**` の変更は記録しない（ノイズになるため）。
`README.md` や `pyproject.toml` など層に属さないものは `shared` に落ちるが、`shared` は
自動追記の対象外（`log.layers` に含めていない）なので、必要なときに手で書くか
`okf log --layer shared --write` を明示的に実行する。

---

## 8. ファイル命名

| 対象 | 規則 | 例 |
|---|---|---|
| 通常ドキュメント | kebab-case | `deployment-flow.md` |
| ADR | `NNNN-<kebab>.md`（4桁連番） | `0001-use-postgres.md` |
| Backlog | `T-NNNN-<kebab>.md`（4桁連番） | `T-0001-readme-update.md` |
| 予約ファイル | `index.md` / `log.md` のみ | — |

新規Backlogは `okf.yml` の `backlog.prefix: T` に従って採番する。導入前の `B-0001`〜`B-0009` は既存ID・ファイル名・相互参照・進捗を保持し、更新も同じファイルで行う。

`_` で始まるディレクトリ（`_templates/`）は**バンドル対象外**として扱われ、index にも lint にも現れない。

---

## 9. 記述スタイル

- 表・Mermaid 図・コードブロックを積極的に使う
- **推測で書かず、コードから読み取れる事実のみ**書く
- 既存のセクション構成・見出しレベルを勝手に変えない
- 1ファイルが長くなりすぎたら分割し、`related` と `index.md` で繋ぐ

---

## 10. lint ルール

`okf lint` が検証する内容。

| # | ルール | レベル | 根拠 |
|---|---|---|---|
| L1 | 非予約 `.md` にパース可能な frontmatter がある | error | OKF §11 |
| L2 | `type` が非空 | error | OKF §11 |
| L3 | `type` が §2 の語彙表の値 | error | 本規約 |
| L4 | `status` が `draft`/`stable`/`deprecated` | error | OKF §5.4 |
| L5 | `layer` が `okf.yml` の `layers` の値 | error | 本規約 |
| L6 | `generated.by` が Actor 表記 | warn | OKF §7 |
| L7 | `index.md` に frontmatter が無い（ルートの `okf_version` のみ例外） | error | OKF §8 |
| L8 | `log.md` の見出しが ISO 8601 かつ新しい順 | warn | OKF §9 |
| L9 | `description` が一文（句点1つ以内・120字以内） | warn | OKF 推奨 |
| L10 | `code_globs` がリスト型・各要素が非空文字列 | error | 本規約 |
| L10 | コード由来 type（§3）に `code_globs` がある | warn | 本規約 |
| L10 | `code_globs` の glob が1件以上マッチする | warn | 本規約 |
| L11 | `related` のリンク先が存在し、バンドル内に解決される | warn | OKF §11（壊れたリンクで拒否しない） |
| L12 | `Backlog Item` の `state` が語彙内 / `done` なら妥当な `done_at` がある | error | 本規約 |
| L13 | `index.md` が最新（`index --check` 相当）/ マーカーが破損していない | error | 本規約 |
| L14 | `sources` は、ある場合のみリスト型・各要素マップ型・非空 `resource` | warn | OKF §5.1 |

---

## 11. 閲覧用 HTML

- OKF Bundle の正本は常に `.md`。生成された `.html` を手で編集しない
- `okf render` は、除外対象を除く全 `.md` を同じ階層の `.html` に変換する
- 生成HTML内のBundle内リンクは `.html` に変換するが、元Markdownのリンクは変更しない
- 共有アセットは `_assets/` に置く。`_` 始まりなのでBundle、index、lintの対象外
- `*.html`、`_assets/`、公開用の `_site/` はGit管理外の派生物とする
- 公開用にMarkdownと分離した構成が必要な場合だけ `okf render --output _site` を使う
- hookからのHTML生成はローカルコマンドだけで完結させ、モデル継続を指示する終了コード2や `decision: block` を返さない
