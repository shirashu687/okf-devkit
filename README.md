# okf-devkit

**Keep an [OKF](https://github.com/GoogleCloudPlatform/open-knowledge-format) v0.2 documentation bundle in sync with the code it describes.**

`okf-devkit` は、OKF v0.2 バンドルを**ソフトウェア開発リポジトリで運用する**ための CLI。
「ドキュメントを書く」ことではなく、**書いたドキュメントがコードから乖離しないようにする**ことに重心がある。

```bash
pip install okf-devkit
okf init --layer client=src/client/** --layer server=src/server/**
```

---

## なぜ別のツールなのか

OKF には既に良いツールがある。**役割が違うので、併用できる。**

| ツール | 担当 |
|---|---|
| [okfctl](https://github.com/cwest/okfctl) | 汎用の OKF バンドル操作（validate / lint / index / search / graph / migrate） |
| [okf-skills](https://github.com/scaccogatto/okf-skills) | Claude Code から OKF を書く・グラフ可視化する |
| **okf-devkit** | **コードとドキュメントの連動**。リポジトリの git 履歴とソースツリーが入力になる |

okf-devkit だけが持っているのは次の4つ。

| 機能 | 内容 |
|---|---|
| **`affected`** | 変更したソースファイルから、**更新すべきドキュメントを逆引き**する。ドキュメント化漏れのパスも列挙する |
| **`log --write`** | git 履歴から `log.md` を**自動生成**する。層ごとに振り分け、コミットハッシュで冪等 |
| **`stale`** | `generated.at` と**実際のコードの最終コミット日時**を突き合わせ、内容が古くなった文書を検出する |
| **`render`** | バンドル全体を**読み物として読める複数ページ HTML** に変換する（グラフ可視化ではない） |

これを支えるのが独自 frontmatter キー **`code_globs`** ——「この文書はどのコードから導出されたか」の宣言である。

```yaml
code_globs:
  - src/api/*.ts
  - src/db/schema.sql
```

OKF v0.2 §5 は独自キーの追加を明示的に許可しており、consumer は未知キーを保持する。
つまり `code_globs` を付けても**バンドルは他の OKF ツールと互換のまま**である。

---

## インストール

```bash
pip install okf-devkit
```

Python 3.11+ / Windows・macOS・Linux 対応。依存は `markdown-it-py` と `PyYAML` のみ。

## クイックスタート

```bash
okf init --site-name "My Project" --layer client=src/client/** --layer server=src/server/**
```

生成されるもの:

| パス | 中身 |
|---|---|
| `okf.yml` | このリポジトリ固有の設定（層・パス対応・log 出力先） |
| `docs/AGENTS.md` | **LLM 向けの入口**。作業手順と「完了の定義」 |
| `docs/CONVENTIONS.md` | 語彙・書式の唯一の基準。lint が強制する内容の人間向け説明 |
| `docs/_templates/` | type ごとのテンプレート |
| `docs/<layer>/log.md` | 層ごとの変更履歴（空） |
| `.okf/hooks/` | エージェントの Stop hook 用ラッパー |

続けて:

```bash
okf index --write   # 目次を生成
okf lint            # 規約違反の確認（init 直後は 0 件）
okf render          # 閲覧用 HTML を生成してブラウザで開く
```

## コマンド

| コマンド | 役割 |
|---|---|
| `init` | リポジトリに OKF バンドルと設定一式を生成する |
| `index` | 各ディレクトリの `index.md` を frontmatter から再生成する |
| `log` | git 履歴から各層の `log.md` に追記する（冪等） |
| `lint` | OKF 適合 + 語彙の検証（L1〜L14） |
| `stale` | 陳腐化レポート（expired / orphan / outdated / unverified / draft-stale） |
| `affected` | 変更パスから更新すべきドキュメントを列挙する |
| `new` | backlog / doc の雛形を生成する（ID 採番込み） |
| `status` | backlog の集計を表示する |
| `render` | バンドルの Markdown を閲覧用 HTML に変換する |
| `sync` | `index` → `log` → `lint` → `stale` を一括実行する |

共通オプション: `--root <dir>`（プロジェクトルート）、`--config <path>`（設定ファイル）。
どちらも省略時は、CWD から上に遡って `okf.yml` を探し、無ければ git のトップレベルを使う。

### 開発中の典型的な流れ

```bash
# 1. コードを変更したあと ── 探索せず、対象をスクリプトに聞く
okf affected --base main

# 2. 出力されたファイルだけを開いて本文と generated.at を更新する

# 3. まとめて整合させる
okf sync
```

## 設定

設定は **「パッケージ同梱の `defaults.yml`」＋「プロジェクトルートの `okf.yml`」** のマージで決まる。

- `types` / `statuses` / `kind_rules` / `backlog` の語彙、`index` のマーカーとリンク形式といった**普遍的な設定は同梱側**にある
- `okf.yml` には**このリポジトリ固有の設定だけ**を書けばよい（`bundle_root` / `layers` / `layer_map` / `log.paths` / `log.baseline` / `site_name`）
- マージ規則: **dict は再帰的にマージし、リストとスカラーは丸ごと置換**する

生成 `index.md` のリンク形式は `index.link_style` で選ぶ。既定は既存互換の `bundle-absolute`、このリポジトリはObsidianで階層をそのまま辿れる `relative` を明示している。

```yaml
index:
  link_style: relative  # bundle-absolute（既定）または relative
```

`relative` は各 `index.md` の親ディレクトリから解決される（例: `docs/index.md` から `./project/index.md`）。`index --write`、`index --check`、`lint`、`sync` で同じ設定が使われ、不正値は索引を書き込まずにエラーになる。

### 既存リポジトリへの導入

`log.md` に手書きの既存エントリがある状態で `okf log --write` を実行すると二重追記になる。
`okf.yml` の `log.baseline` に**移行済みの最後のコミット SHA** を入れること
（未設定かつハッシュ無しエントリがある場合、`okf` は書き込みを拒否する）。

## Obsidianでの閲覧

Obsidianでは、このリポジトリのルートフォルダをそのままVaultとして開く。Markdown、YAML frontmatter、生成 `index.md`、`harness/` のworklog・台帳を同じファイルとして検索・閲覧し、内容・差分・履歴の正本はGitに置く。別Vault、専用コピー、community plugin、自動同期・公開は作らない。

主な入口と役割対応は [プロジェクト設定](harness/project/config.md) にまとめている。frontmatterのネストした値は平坦化せず、必要ならPropertiesのソース表示で確認する。リンクの自動更新で生成indexやMarkdownを変更せず、移動・改名は既存の編集手順と `okf index --write` で扱う。

`.obsidian/` は個人の画面状態としてGit管理外にする。GitのignoreはObsidianの表示・検索を制御する機能ではない。OKFを採用しないリポジトリでは、同じハーネスのMarkdown + Git、役割対応表、検証契約を使い、OKF CLIの導入を必須にしない。

## エージェント連携

`okf init` が `.okf/hooks/render_hook.sh` / `.ps1` を置く。Stop hook から呼ぶと、
作業終了時に閲覧用 HTML が自動で再生成される。

**Claude Code** — `.claude/settings.json`:

```json
{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "sh \"$(git rev-parse --show-toplevel)/.okf/hooks/render_hook.sh\"",
            "shell": "bash",
            "timeout": 30,
            "statusMessage": "OKFドキュメントのHTMLを生成中"
          }
        ]
      }
    ]
  }
}
```

**Codex** — `.codex/hooks.json`:

```json
{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "sh \"$(git rev-parse --show-toplevel)/.okf/hooks/render_hook.sh\"",
            "commandWindows": "powershell -NoProfile -ExecutionPolicy Bypass -Command \"& (Join-Path (git rev-parse --show-toplevel) '.okf/hooks/render_hook.ps1')\"",
            "timeout": 30
          }
        ]
      }
    ]
  }
}
```

`render --hook` は成功時に `{}`、失敗時に終了コード 1 を返す。**終了コード 2 や `decision: block` は返さない**ため、
HTML 生成を理由にモデルの継続実行が発生することはない。

### `sync --gate`

LLM に差し戻したい場合は別コマンドの `okf sync --gate` を使う。機械的に直せるものは自動修正し、
残った lint error は stderr に修正指示を出して **exit 2** を返す。
同じ error 集合に対して 2 回目は警告のみで exit 0 にするため、無限ループにはならない。

## CI

```yaml
- run: pip install okf-devkit
- run: okf lint
- run: okf index --check
- run: okf render --check
```

## 開発

```bash
python -m venv .venv
.venv/Scripts/python -m pip install -e .   # POSIX: .venv/bin/python
python tests/run_all.py                    # 標準ライブラリの unittest のみ
```

テストは実バンドルに触れず、一時ディレクトリ上のバンドルと一時 git リポジトリで完結する。

| ファイル | 内容 |
|---|---|
| `test_init.py` | 設定マージ、ルート探索、`init` の生成物と入力検証 |
| `test_index.py` | index の golden test、冪等性、マーカー破損時の非書き込み |
| `test_log.py` | log の冪等性、baseline、層のルーティング |
| `test_yaml.py` | PyYAML 有無での同値性、曖昧構文の拒否 |
| `test_lint.py` | L4〜L12 の見逃し防止 |
| `test_git.py` | rename / 非 ASCII パス / shallow / detached HEAD / コミット 0 件 |
| `test_gate.py` | finding 指紋ごとの回数管理、fail-closed、stdin のハング防止 |
| `test_atomic.py` | 書き込み失敗時に元ファイルが壊れないこと |
| `test_render.py` | リンク書き換え、冪等性、hook の非ブロッキング契約 |
| `test_new.py` | YAML 安全性、`..` / 絶対パスの拒否、連番採番 |

## 設計方針

- **決定的にできることは全部スクリプトに寄せる。** LLM のクレジットは「文章の中身を書く」非決定的な作業だけに使う
- すべてのファイル書き込みは一時ファイル + `fsync` + `os.replace()` による**原子的置換**
- **内容が変わらなければ書き込まない**（hook から連打しても安全）
- 読み書きは UTF-8 / LF 固定
- PyYAML が無い環境では内蔵の**厳格な**簡易 YAML パーサへフォールバックする。曖昧な構文は黙って誤読せず必ずエラーにする

## ライセンス

MIT
