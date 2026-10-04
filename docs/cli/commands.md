---
type: Reference
title: コマンド仕様
description: Python CLI のコマンドごとの入出力と検査モードの仕様。
tags: [cli, implementation]
status: stable
layer: cli
generated:
  by: codex/gpt-6
  at: 2026-10-04T09:27:05Z
code_globs:
  - src/okf_devkit/cli.py
  - src/okf_devkit/yamlio.py
  - .github/workflows/ci.yml
related:
  - /cli/architecture.md
  - /render/architecture.md
  - /scaffold/reference.md
---

# コマンド仕様

純粋helpersの分離後も、この表の引数・終了値・書き込み条件は維持する。連続呼出しや別CWDからの絶対 `--root` / `--config` 指定は対象リポジトリに従い、Git時刻cacheもそのrootへ切り替わる。

共通引数 `--root` / `--config` はサブコマンドの前へ置く。詳細なオプション一覧は `okf <command> --help` を参照する。

| コマンド | 入力・結果 | 書き込み条件 |
|---|---|---|
| init | バンドル、設定、テンプレート、hook を初期配置 | 既存ファイルは `--force` がない限りスキップ |
| index | frontmatter から各階層の目次を計画 | `--write`。`--check` は差分があれば exit 1 |
| log | Git のコミットを層別履歴へ変換 | `--write`。`--range` / `--layer` で範囲を限定 |
| lint | OKF、語彙、リンク、目次等を検査 | なし。error で exit 1、`--strict` は warn も対象 |
| stale | 期日・コード更新・検証状態のレポート | なし。指摘があっても exit 0 |
| affected | `--base` との差分または `--paths` を文書へ逆引き | なし。対応文書と未カバーのパスを表示 |
| new doc | layer/type/title とテンプレートから文書を作る。`--code-globs` は複数指定可 | 新規 Markdown。本文を補完し、`index --write` → `lint` を実行 |
| new backlog | タイトルと優先度等から backlog 文書を作る | 新規 Markdown。このリポジトリの課題管理は GitHub Issues |
| status | backlog の state を集計 | なし。text/json 出力 |
| render | Markdown とアセットから HTML を作る。`--open` は生成先のトップページを開く | 既定は `_site/`。`--output docs` で従来の隣接配置を指定。`--check` / hook 時はブラウザを起動しない |
| sync | index → log → lint → stale をまとめて実行 | index/log 更新。`--gate` は hook 用の差戻し判定 |

## 新規文書の根拠コードと検査

`new doc` の `Project Overview` / `Architecture` / `Reference` / `How-To` は `--code-globs` が必須。その他の型では省略できる。例えば `okf new doc --layer cli --type Reference --title "コマンド仕様" --code-globs "src/okf_devkit/cli.py" "node/cli.mjs"` と指定する。生成後は本文を補完し、目次を更新してから規約検査を実行する。

## 出力先と旧生成物の整理

旧生成物の整理は `render --output _site --cleanup-from docs --check` で計画を確認し、`--check` を外した明示実行だけで行う。通常の render / hook は旧出力を整理しない。hash・manifest で識別できる未編集生成物だけを新出力成功後に退避し、未知・編集済み出力は保持する。receipt と非上書き復元、旧新出力先の安全境界は [生成済みHTMLの整理](/render/output-cleanup.md) を参照する。

## 自リポジトリの CI

`self-check` は完全な Git 履歴を取得して `okf lint`、`okf index --check`、`okf render --check` を実行する。古い index は差分検査で失敗する。`okf stale` は参考レポートとして表示し、指摘件数の閾値を設けない。warn を失敗扱いにする `lint --strict` は採用していない。

`render --check` は全ページとアセットをメモリ内で生成できるかを検証する。既存 HTML との差分を比較するコマンドではなく、HTML 未生成のクリーン checkout でも使える。生成 HTML を Git に追加する必要はない。通常のテスト・一時バンドル smoke と並行して、実際の docs バンドルを検査する。

配布用の変更検査は通常の PR CI でも `npm run test:release` と `npm run test:package` を実行する。GitHub に書き込まない Release ガードと、一時 prefix での実 tgz 導入・復旧を確認する。タグ起点の Draft Release 手順は [GitHub 配布の判断](/project/decisions/0002-github-node-distribution.md) を参照する。

## YAML処理の所有者

設定・frontmatterの解析とnewのscalar/flow生成は `yamlio.py` が所有する。コマンドの引数・終了値・生成文字列は維持し、通常のDoc/Bundleはyamlioの現在backendを読む。旧 `cli.parse_yaml` の直接呼出しは旧backend差替えの互換adapterを通る。YAMLを省略した環境では従来の厳格なsubsetと拒否メッセージを使う。
