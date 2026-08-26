---
type: Backlog Item
title: cli.py をモジュールに分割する
description: 2,885 行の cli.py を責務ごとに分割し、コマンドを足すたびに単一ファイルが膨らむ状態を解消する。
tags: [cli]
status: stable
layer: cli
generated:
  by: "process:okf-cli"
  at: "2026-08-26T13:09:12Z"
state: todo
priority: medium
effort: M
feasibility: B
ai: assisted
cost: false
created: "2026-08-26"
done_at: null
related:
  - /backlog/B-0001-self-hosted-docs.md
---

# cli.py をモジュールに分割する

## やりたいこと

`src/okf_devkit/cli.py`（2,885 行）を、責務ごとのモジュールに分ける。

## 背景・現状

パッケージは実質 2 ファイル。`cli.py` が 2,885 行、`renderer.py` が 470 行。
`cli.py` の内訳（区切りコメント `# ===` ごとの行数）:

| 区分 | 行数 |
|---|---|
| 基本ユーティリティ（原子的置換・glob・日付） | 242 |
| YAML（PyYAML フォールバックと内蔵パーサ、シリアライズ） | 382 |
| frontmatter（`Doc`） | 152 |
| 設定・バンドル走査（`merge_config` / `Bundle`） | 119 |
| git ヘルパー | 206 |
| 各コマンド（index / log / lint / stale / affected / new / status / render / sync / init） | 1,646 |
| 引数パーサとエントリーポイント | 135 |

ファイル内は区切りコメントと docstring で整理されているが、コマンドを 1 つ足すたびに
同じファイルが伸びる。lint 規則（L1〜L14）とコマンド実装が同居しているのも見通しを悪くしている。

**分割時に踏む地雷が 2 つある。先に手当てしないと静かに壊れる。**

1. `REPO_ROOT` はモジュールグローバルで、`main()` が `global REPO_ROOT` として起動時に
   書き換えている（参照 28 箇所）。別モジュールで `from .fsutil import REPO_ROOT` と書くと
   **書き換え前の値のコピー**を掴むため、`--root` / `--config` の指定が効かなくなる。
2. テストは `from okf_devkit import cli as okf` の一本槍で、`okf.<名前>` を約 50 個参照している。
   特に `helpers.py` と `test_yaml.py` は `okf._pyyaml = None` と差し替えて内蔵パーサ経路を
   検証している。`parse_yaml` を別モジュールへ移すと差し替えが効かなくなり、
   **テストは通るのに何も検証しなくなる**。

## 進め方

1. 先に `REPO_ROOT` の参照方法を変える（関数 `repo_root()` か、コンテキストオブジェクト経由）。
   このコミット単体でテストが通ることを確認してから次へ進む。
2. 依存の向き（`fsutil` ← `yamlio` ← `doc` ← `config` ← `gitutil` ← `commands/*` ← `cli`）に沿って、
   下から順に切り出す。

   | 新モジュール | 移すもの |
   |---|---|
   | `fsutil.py` | 原子的置換・glob 照合・日付ユーティリティ |
   | `yamlio.py` | `parse_yaml` / 内蔵パーサ / `yaml_scalar` |
   | `doc.py` | `Doc` |
   | `config.py` | `merge_config` / `load_merged_config` / `Bundle` |
   | `gitutil.py` | git 呼び出しと `-z` 出力の解析 |
   | `commands/*.py` | 各 `cmd_*` と、その補助関数 |
   | `cli.py` | `build_parser` / `resolve_root` / `main` / `run` のみ |

3. テストは移動先モジュールを直接 import する形に直す。`cli.py` からの再エクスポートで
   互換を保つのは構わないが、`_pyyaml` の差し替えだけは移動先を指していないと意味が無い。
4. 1 モジュール切り出すごとに `python tests/run_all.py` を回す（現在 144 件）。
5. 分割後、`okf.yml` の `layer_map`（`src/okf_devkit/**` → `cli`）と、
   [B-0001 okf-devkit 自身の docs バンドルに本文ドキュメントを書く](/backlog/B-0001-self-hosted-docs.md)
   で書くドキュメントの `code_globs` を新しいファイル構成に合わせる。

## 完了条件

- [ ] `cli.py` が 200 行以下（パーサとエントリーポイントのみ）
- [ ] `python tests/run_all.py` が 144 件すべて成功する
- [ ] PyYAML 不在時の経路が実際に検証されている（差し替えが効いている）
- [ ] `okf --root <別ディレクトリ> lint` が動く（`REPO_ROOT` の取り回しが壊れていない）
- [ ] 影響ドキュメントを更新した（`okf affected` の出力）
- [ ] 該当層の `log.md` に追記した
- [ ] 本ファイルの `state` を `done` にし `done_at` を記入した

## 結果

<完了時に記入する。PR / コミットへのリンク、実際に変更したファイル、想定と違った点。>
