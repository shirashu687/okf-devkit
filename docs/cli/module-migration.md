---
type: Architecture
title: CLI 分割の移行設計
description: Python CLI の可変状態とテスト互換性を守る段階的なモジュール分割案。
tags: [cli, migration]
status: draft
layer: cli
generated:
  by: codex/gpt-6
  at: 2026-10-04T10:49:10Z
code_globs:
  - src/okf_devkit/commands/__init__.py
  - src/okf_devkit/commands/index.py
  - src/okf_devkit/commands/log.py
  - src/okf_devkit/commands/lint.py
  - tests/test_commands_context.py
  - src/okf_devkit/gitutil.py
  - tests/test_gitutil.py
  - tests/test_config.py
  - tests/test_doc.py
  - src/okf_devkit/config.py
  - src/okf_devkit/doc.py
  - src/okf_devkit/cli.py
  - src/okf_devkit/yamlio.py
  - src/okf_devkit/errors.py
  - src/okf_devkit/fsutil.py
  - tests/test_cli_context.py
  - tests/test_fsutil.py
  - src/okf_devkit/renderer.py
  - src/okf_devkit/render_cleanup.py
  - tests/test_render_cleanup.py
  - tests/helpers.py
  - tests/test_yaml.py
related:
  - /cli/node-runtime.md
---

# CLI 分割の移行設計

第5a段階では index、log、lint の実装と専用helpersを `commands/index.py`、`commands/log.py`、`commands/lint.py` へ分離した。canonical commandはBundleの `.repo_root` を使い、CLIや可変rootをimportしない。予約文書のDoc構築にもrootを明示する。旧CLI入口は現在のrootと必要なwriter/Git/resource/index/linter callbackを渡す薄いadapterで保持する。残る7コマンドと引数入口は未分離で、Issue #12全体の200行以下という条件はまだ満たしていない。

第4段階の現況（更新済み親の統合後も保持）: 実装は `gitutil.py` を所有者とし、rootと時刻cacheを明示する。`CommitTimesCache` はrootが変わると再計算し、同root内の更新は呼出元がmappingをNoneへ戻して無効化する。旧cliのroot・git runner・時刻map/reset adapterと同一Commit/parser exportを保持する。実2repo・特殊名・runner失敗・resource glob・gateを新所有者で検証する。全コマンドの分離完了と200行以下の入口はまだ未完了。
第3段階時点の記録: `doc.Doc(path, bundle_root, *, repo_root)` と `config.Bundle(config_path=None, *, repo_root)` を追加した。Bundleは `.repo_root` と文書 `.root` を区別し、Doc生成にも保存済みrootを渡す。旧CLIは薄いDoc/Bundle subclassで直接root注入と従来constructorを保持する。CLI生成Docの型は `cli.Doc` のまま、canonicalモデルはCLI/Gitへ依存しない。当時は段階4以降のGit・commands移行とcli 200行以下が未完了だった。現在のGit移行は上記第4段階の記録を参照し、commandsとcli 200行以下は未完了である。


この文書は Issue #12 の事前調査・技術設計と段階別の実装記録であり、Issue全体の実装完了を表さない。CLI の引数・終了値・生成結果と Python/Node の互換性を維持し、純粋な処理から順に移す。

段階0/1ではroot・反復main・YAML backendの回帰条件を固定し、`errors.py` と `fsutil.py` を分離する。元のCLI exportは同じ関数・例外class・glob cacheを参照し、YAML切替えは実際のcli所有者と内蔵パーサ呼出しを観測する。Git時刻cacheのroot切替え漏れを二つの実Gitリポジトリで確認し、現在のrootに紐付けて再取得する。この記録は段階0/1時点の状態である。後続の段階4実装は冒頭の現況を参照し、commandsと200行以下の入口は未完了である。

## 現状の依存とテスト面

調査対象 main の `9d72e0e5798883d81789582d8879f139865d37b5` では cli.py は2922行。ASTで `REPO_ROOT` の Name 参照を27件、tests/*.py の `okf.<名前>` を49種類確認した。件数はこの版の測定値であり、分割の完了判定はIssueの行数と振る舞い条件を使う。

| 可変状態 | 現在の所有者・呼出し | 分割で守ること |
|---|---|---|
| REPO_ROOT | cli.main が確定し、helpers が直接代入・復元 | 別モジュールへの値コピーを禁止し、現在のルートを明示的に渡す |
| _pyyaml | cli.parse_yaml が参照、helpers/test_yaml が差替え | パーサ実行時の所有者を差し替え、内蔵経路が実際に走ることを確認 |
| _PATH_TIME_MAP | Git履歴時刻のキャッシュ、helpers が None に戻す | 根の切替えで前リポジトリのキャッシュを引き継がない |
| _GLOB_CACHE | glob変換キャッシュ、helpers が clear | 移動先の同じオブジェクトを参照し、コピーを作らない |
| DEFAULTS_PATH / SCAFFOLD_DIR | 同梱素材の絶対位置 | CWDや利用者ルートではなくパッケージ位置から解決 |

Doc/Bundle は単なるデータではなく設定・ファイル読取・YAML処理に依存する。Git helpers はルートと時刻キャッシュに依存する。Issueの依存図を形式的な一列として実装せず、モデルとGit処理を相互importさせない。

## 小さい変更単位

| 段階 | 新しい module / interface | 単独で確認する結果 |
|---|---|---|
| 0 | 現在のcliのまま、根指定とYAML切替えの回帰条件を固定 | 二つの異なる一時ルート、非CWDからの--root/--config、連続main呼出しが対象を取り違えない |
| 1 | errors.py と純粋fsutil。日付・glob・atomic writeはpathを受ける | 同じ例外classをcliから再export。write-if-changedとWindows共有違反処理を維持 |
| 2 | yamlio.py、parse_yaml(text, source)、yaml_scalar(value) | test_yamlの差替えをyamlioへ移し、同じ入力で両backend一致と内蔵の拒否経路を確認 |
| 3 | doc.py / config.py。Bundleへrootを渡す | プロジェクト設定、素材位置、除外、frontmatter、予約文書を維持 |
| 4 | gitutil.py。rootと必要なcacheを呼出しから渡す | log/stale/affectedの結果・時刻・rename/特殊名解析を維持 |
| 5 | commands/index, log, lint, stale, affected, new, status, render, sync, init | 一コマンドずつ移し、同じCLI出力・終了値・ファイル差分を確認 |
| 6 | cli.py は引数解釈と入口、互換exportのみ | 200行以下、Python全件とNode互換、根指定・YAML不在経路を最終確認 |

各段階は独立commit/PRで必要テストを通してから次へ進む。初回から大量のシンボルを移動したり、共通contextへすべての設定を詰め込んだりしない。CLIの公開入口 `main` / `run` と既存の呼出し用シンボルの再exportを維持する。

## ルートと互換exportの移行

`from module import REPO_ROOT` による参照は採用しない。初回はルート所有者をcliに残し、切り出し側へ `Path` を引数で渡す。Bundleはrootを保持し、その操作はBundleのrootに従う。rootを必要とする既存cli関数は、現在の `cli.REPO_ROOT` を読み、移動先へ渡す薄い互換adapterとして一時的に残す。これによりhelpersの `okf.REPO_ROOT = ...` が突然無効になることを防ぐ。

commands移動時は `main` が解決したrootをBundle/必要なinterfaceへ渡す。キャッシュはroot別、またはroot変更時に確実に初期化し、二つのルートの連続処理で検証する。最終的な所有場所の変更は互換adapterとテスト移行を同じ変更単位にする。入口の200行条件はparserとexportの実測により確認し、行数だけを減らす圧縮はしない。

## YAMLの差替えが空振りしない確認

yamlioへ移した関数のglobalsはyamlioを指す。cliから関数を再exportするだけでは `okf._pyyaml = None` は効かない。テストは実行する所有者 `yamlio._pyyaml` を差し替える。Doc/config経由のlintも同じ所有者を使うようにする。

移行中に旧cli経由の直接呼出しを残す場合、互換 `cli.parse_yaml` は旧 `_pyyaml` の値を明示してparserへ渡すadapterとし、通常経路とtest seamを区別する。Doc/Bundleのテストは移動先所有者を差し替える。backendとして明示した None と省略（既定backend）を区別するsentinelが必要になる場合だけ導入する。

差替え確認では内蔵経路の呼出し観測も行い、単に期待結果が一致するだけで成功としない。PyYAMLが実際にない環境でも同じ拒否構文・frontmatter処理を確認する。例外の型とメッセージが呼出し先ごとに変わらないことも確認する。

## 先行変更との統合順

以下の先行変更・npm差分の記述は調査対象 `9d72e0e5798883d81789582d8879f139865d37b5` のスナップショットであり、現在のmainの未統合状態を示すものではない。

未統合 `origin/shirashu687/npm` はmainより14commit先でcli/initとscaffold、testsへ変更を持つ。#6/#7/#11/#17 のコマンド変更と #4 の実装本文も進行している。大きいcommands移動はこれらの統合順が確定した後に行う。純粋helpersの先行切出しでも、開始時に最新baseとnpm差分を再確認する。

この設計段階では実行コード・配布設定・公開方針・hook設定を変更しない。Node移植は行わず、Python移動後も既存の `npm run test:compat` で対応出力を確認する。新ファイルは現行 `src/okf_devkit/**` → cli のlayer_mapで分類できる。分割ごとに `okf affected` の結果を更新し、#4の本文code_globsへ移動先を加え、層ログを残す。

## main の出力整理 module との接続

統合対象 `50380b3d3a22507b2bd2e329e1d206141ce2432e` はCLIの既定出力を `_site/` に変更し、`render --cleanup-from` と `src/okf_devkit/render_cleanup.py` を追加している。最初の調査の行数・参照数は再測定値へ上書きせず、上記固定SHAの根拠として保持する。

既に分離されたcleanup moduleはstage5のcommands/renderへ戻して同居させない。renderの入口は既存moduleの計画、範囲検証、manifest記録、退避実行を呼ぶinterfaceとして扱う。cleanupのチェック非書込み、hookとの併用拒否、旧新範囲・曖昧Windowsパス・manifest重複の拒否、編集済み/手書き出力の保持、退避/復旧の安全条件を移動後も維持する。ライブラリrenderの既定とCLIの `_site` 既定も区別する。

分割の検証には従来のPython全件に `tests/test_render_cleanup.py`、Nodeの `npm test` にrender-cleanup、`npm run test:compat` にcleanup-compatibilityが含まれる現行scriptを使う。commandsを移す直前に採用済みmainとまだ未統合の変更を再確認し、この文書の初回の先行Issue一覧だけを実装順の根拠にしない。

## 状態別 Backlog 表示との接続

統合対象 `c09c6eea9756c05904c6dc2f27f3f832d28e283f` はHTMLの状態別リスト、任意カンバン、表示検索と開閉復元をPython/Node共通資産へ追加している。この表示処理はrendererと共有assetsが所有し、CLIのmodule分割時にcommands/statusへ移さない。ファイル型Backlogの集計とHTMLの表示interfaceを区別し、読み取り専用、設定語彙/順序、本文リンク、検索前の開閉復元、JavaScriptなしのリスト表示を維持する。

分割後も現行Python renderテスト、Node nativeとcompat、およびcleanup suiteをすべて実行する。表示だけの操作でMarkdownやcleanup manifestを変更しない契約は、既存の共通資産側で保つ。ここでのmain統合は分割実装の完了を示さず、最初の調査SHAの測定値は保持する。

## 自リポジトリ本文・終了 hook との接続

統合対象 `fc84eaa47d601cbfab3241fa5e61a600508a516d` では#4の実装本文と#5の自リポジトリdocs CIがmainにある。以後の分割は [CLI の処理構造](/cli/architecture.md) と [コマンド仕様](/cli/commands.md) の根拠コードを移動先へ合わせ、self-checkのlint/index/render検査を維持する。初回調査の先行Issue記述は当時のスナップショットとして扱う。

Copilot/Codex/Claudeの終了hookは共通advisory adapterを経由し、手動のstrict renderとは終了値の契約が異なる。CLIの移動でadapter/hookの振る舞いを統合・削除せず、入力を実行しない、失敗時にエージェントをブロックしない、実HTMLの連続生成、strict/advisoryの違いを既存の `tests/test_repo_hooks.py` と関連Nodeテストで維持する。実エージェントイベントの観測とローカルadapterテストは区別する。

## 実装済み段階1・2と残る移行（段階2時点の記録）

以下の2節は YAML作者版 `111f04ea2ee827e6c6652d24775fbb5c450d4227` とその親統合時点の履歴を保持する。現在の段階3では上部に記載したDoc/config分離が実装済みであり、以下の「未実装」「subsequent」は段階2時点を指す。現在の第5a段階ではindex/log/lintの3コマンドを分離済みで、残る7コマンドと200行以下の入口は後続作業である。

固定stage1 `5e5dea889920fb56075687d5ade4b01e612648b9` から第2段階として `yamlio.py` を切り出す。errors/fsutilとroot/cache互換性を保持し、Doc/config本体やcommandsの分離はまだ実装していない。cliは引数入口だけの200行以下という最終条件には未達で、この変更をIssue #12全体の完了として扱わない。

`yamlio.parse_yaml(text, source)` は省略backendなら実owner `yamlio._pyyaml` を使い、keyword backendの明示Noneは内蔵parserを選ぶ。旧 `cli.parse_yaml` は旧 `cli._pyyaml` を明示して渡す薄いadapterとして残す。通常Doc/Bundleはこの旧aliasに依存せずyamlioを直接利用する。helpersの保存・復元とYaml/context testsは実ownerへ移行し、内蔵constructorとPyYAML.safe_loadの呼出しを観測する。`python -S` の新processでsite-packagesを外し、PyYAMLのimportが実際に利用できない状態で同じconfig/frontmatterと拒否構文を確認する。

## Updated-parent integration for YAML phase

The YAML author snapshot `111f04ea2ee827e6c6652d24775fbb5c450d4227` is integrated with the pure-helper parent `aa398085622bd0a4396b03b8c46ff1d6f645fcb9`. The original stage1 measurement and stage2 backend contracts above remain historical evidence. This integration preserves the incoming AI operations guide, command help, shared errors/fsutil/root cache ownership, and the YAML owner/legacy adapter distinction. Doc/config and command extraction remain subsequent stages.
