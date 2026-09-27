# 作業記録: issue-18-npm-install

このファイルは1作業1枚の状態記録であり、仕様・チケット・会話全文の複製ではない。配置は [config.md](../../project/config.md) の「作業記録と引継ぎ」に従う。

## メタデータ

| 項目 | 値 |
| --- | --- |
| 課題ID / 作業名 | `issue-18-npm-install`（GitHub Issue #18） |
| 状態 | `完了` |
| 作業場所 | `C:/Users/rinta/orca/workspaces/okf-devkit/issue-18` |
| ブランチ | `shirashu687/npm-issue-18` |
| 開始日時 / 最終更新日時 | 2026-09-27 18:30 Asia/Tokyo / 2026-09-27 19:20 Asia/Tokyo |
| 開始SHA | `2c3050df98422cbf258b7bd093468e338bc10afc`（引継ぎコミット。検査の比較元baseは `9d72e0e5798883d81789582d8879f139865d37b5`） |
| 最新HEAD | 本worklogを含む最終コミット（ブランチ `shirashu687/npm-issue-18` 先端） |
| 作業者 / 製品 / モデル | Orca dispatched worker / Devin / SWE-2 Max |
| 証拠の保存先 | `%TEMP%/okf-i18-5746nLOO/`（gh-proj・packed-proj・fresh・fakebin・existing-script・npmcache）。認証情報・ログ全文は保存しない |

## 目的・範囲

### 目的

Issue #18「固定版をプロジェクトへ導入し、ローカルCLIで実行・再導入できるようにする」の受入条件8項目を、引継ぎコミットの実装・文書・検証記録と照合し、不足を最小限補う。

### 対象

- README.md、docs/cli/node-runtime.md、docs/project/decisions/0001-node-runtime.md の受入条件との照合と最小修正
- 公開済みSHA（9d72e0e）と未公開の対象版（開始SHA=2c3050dの `npm pack` tgz）を区別した導入・起動・再導入のsmoke検証
- 必須検証の実行と本worklogへの記録

### 対象外

- `src/`、`node/`、`tests/`、`package.json`、`package-lock.json`、`CONTEXT.md`、`harness/state/journal/issue-14-distribution.*`（別ワーカー所有・凍結）
- push、GitHub Issueへの投稿、mainへのmerge、npm/PyPI公開
- Issue #19（生成案内の切替）・#20（統合確認）の完了条件

### 完了条件

- Issue #18 の Acceptance criteria 8項目（[Issue #18](https://github.com/shirashu687/okf-devkit/issues/18)）

## 開始時の状態

### 開始時から存在する変更

- なし。`git status` はclean。HEADは引継ぎコミット 2c3050d（実装・文書・テスト・issue-14 worklog込み）。
- 確認方法: `git status`、`git log --oneline -3`
- `.venv` はworktreeに存在しないため、既存venv `C:/Users/rinta/Documents/1_projects/okf-devkit/.venv`（Python 3.14.3）へのjunctionを作成。以後のPythonは `.venv/Scripts/python.exe` に `PYTHONPATH=<このworktree>/src` を付けて実行。

### 今回の変更

- 変更済み: `README.md` — CI例の `pip install okf-devkit` がPyPI公開済みを示唆するため固定SHAのGitHub pip導入へ修正（受入条件6）。`npm install` がpackage.json不在でも依存記録を作る注記を追加（受入条件1・6）
- 変更済み: `docs/cli/node-runtime.md` — 別用途 `scripts.okf` 保持時の別名スクリプト案内を追加（受入条件2の補完。review指摘）
- 未追跡: `harness/state/journal/issue-18-npm-install.md` — 本記録

## 判断と根拠

| 判断 | 根拠 | 影響 |
| --- | --- | --- |
| 実装・文書は引継ぎコミットのものを再作成せず照合 | Issue #18本文「同じ実装を新規に作り直さない」、issue-14 worklogの検証記録 | 変更は文書のみ |
| README CI例を修正 | 受入条件6「未公開のPyPIパッケージを公開済みとして案内しない」。base 9d72e0e 時点の既存文で、対象版でも残存していた | README.md |
| 別名スクリプト案内を追加 | review仕様軸: 受入条件2は確認手順を要求するが、`scripts.okf` が別用途で占有される場合の統合先がなかった。initが `scripts.okf` のみ読むため別名利用時の生成案内の手修正も併記 | docs/cli/node-runtime.md |
| smokeの一時フォルダは `%TEMP%/okf-i18-*` の独立ルート | 台帳 IMP-0006（親にpackage.json/okf.ymlがある場所を避ける） | 検証証拠の保存先 |
| 未公開変更の導入確認は `npm pack` tgz、GitHub公開確認は公開済みSHA 9d72e0e で分離 | Issue #14 Testing Decisions 8、依頼の検証条件 | 検証表の github-install / packed-working-tree |
| 新規changes.jsonは作らない | check_changesで今回の自分の変更はすべて ordinary。保護対象 tests/** の宣言は引継ぎの issue-14-distribution.changes.json が差分内で宣言済み | 宣言ファイルなし |

## 摩擦観測とretroゲート

| 項目 | 記録 |
| --- | --- |
| 確認範囲 | 依頼（Issue #18受入条件8項目）、引継ぎコミット2c3050dの全差分、開始SHA時点の文書、実行した検証と再試行、二軸review結果を照合 |
| 該当条件と根拠または非該当理由 | トリガーなし。README CI例のPyPI示唆は base 時点からの既存文書の不整合であり、本タスクの目的である照合で発見し最小修正した。要件の取りこぼし・検証漏れ・やり直し・同じ探索の反復は発生していない |
| 短い観測メモ | なし（環境差の摩擦なし。venvはjunctionで既存Python 3.14.3を利用） |
| 処理済み事象・台帳ID | なし |
| 未確認範囲と次の一手 | CI・他OS・別PCでの成功は未確認。push後にIssue #20が公開SHAを含む統合確認を行う |
| full retrospective | 不要 |
| 人の判断待ち | なし |

開始時台帳確認: 評価中6/10、試行0/3、採用済み0。期限超過の試行・見直し対象なし（全件 期限未定）。IMP-0006の対処案（独立一時ルート）を今回のsmoke配置に適用。

追記（最終コミット再検証時）: 標準軸reviewで「検証表の対象版と記録時点の最終コミットの対応が識別不能」との指摘を現物と照合し、最終対象版での必須検証が記録から識別できない状態（検証漏れトリガー該当）を確認した。観測を `IMP-0007` として [改善台帳](../../ledger.md) へ登録し、修正として最終コミット `28194f733350df5ee738f1306f248f929e1d573a` への必須検証再実行と「最終コミット再検証」節の追記を行った。この再検証の実施自体に新たな摩擦・失敗・再試行はない。

## 検証

| 識別子 | 適用 | 結果 | 対象版・範囲 | コマンド / 確認方法 | 期待条件 | 証拠 | 理由・限界 / 再試行 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| project-required | はい | 成功 | 開始SHA + README修正、junctionした既存venv 3.14.3 | `PYTHONPATH=<worktree>/src .venv/Scripts/python.exe tests/run_all.py` | 終了0・失敗0・エラー0 | 171件、失敗0、エラー0、終了0 | このworktreeのsrcを参照。別worktree・site-packages非参照をPYTHONPATHで担保 |
| node-install | はい | 成功 | このcheckout | `npm ci` | 終了0 | added 8 packages、終了0 | Node v24.21.0 / npm 11.19.0 |
| node-native | はい | 成功 | 開始SHAのtests/node | `npm test` | 終了0・fail 0 | 13件 pass、fail 0、終了0 | Node実装・依存・共有資産は自分の差分にないが、受入条件の動作確認のため実行 |
| node-compat | はい | 成功 | 同上 | `OKF_TEST_PYTHON=<worktree>/.venv/Scripts/python.exe PYTHONPATH=<worktree>/src npm run test:compat` | 終了0・fail 0 | 8件 pass、fail 0、終了0 | 編集中のPythonソースを参照していることを確認 |
| github-install | はい | 成功 | 公開済みSHA 9d72e0e | 空の `%TEMP%/okf-i18-5746nLOO/gh-proj` で `npm install --save-dev "git+https://github.com/shirashu687/okf-devkit.git#9d72e0e…"` → `npm pkg get scripts.okf`（`{}`）→ pkg set → `npm run okf -- init --layer "app=src/**"` → `index --write` → `lint` | 各終了0 | package.json自動作成、init/index/lint終了0、lint error 0/warn 0 | 公開版の配布経路のみ検証。scripts.okf対応の生成案内はこの版に含まれない |
| packed-working-tree | はい | 成功 | 未公開の開始SHA 2c3050d の `npm pack` tgz | `%TEMP%/okf-i18-5746nLOO/packed-proj` で `npm install --save-dev file:../okf-devkit-0.1.0.tgz` → scripts.okf設定 → PATH先頭に偽okf・pythonをPATHから除外 → init→index→lint | 各終了0・生成案内が `npm run okf --`・偽okf未使用 | lint error 0/warn 0、生成AGENTS.mdが `npm run okf --` 表記、FAKE_OKF_USED出力なし | 未公開変更の検証であり、GitHub公開版の成功ではない。PATH残存は非機能のWindowsApps stubのみ |
| fresh-lock | はい | 成功 | gh-proj の package.json + package-lock.json | 独立した `%TEMP%/okf-i18-5746nLOO/fresh` へ2ファイルをコピー、新規 `--cache` で `npm ci` → init→index→lint | 各終了0 | init/index/lint 終了0、lint error 0/warn 0 | 親ディレクトリにpackage.json/okf.ymlなし。同一マシン上の確認であり別PCではない |
| missing-dependency | はい | 成功 | gh-proj | `node_modules/okf-devkit` を一時rename → `npm run okf -- lint` | 非ゼロ終了 | 終了1・MODULE_NOT_FOUND。確認後に復元し再実行で終了0 | 期待した失敗を検証。PATH上の偽okfへは切り替わらない |
| existing-script-check | はい | 成功 | `%TEMP%/okf-i18-5746nLOO/existing-script` | 既存 `scripts.okf="echo custom-existing"` のpackage.jsonで `npm pkg get scripts.okf` | 既存値が返り手順どおり上書き判断できる | `"echo custom-existing"` を取得 | 手順書の確認工程の動作確認 |
| docs | はい | 成功 | 開始SHA + README修正 | `index --write` / `lint` / `index --check`（指定venv+PYTHONPATH） | 索引最新・error 0/warn 0・各終了0 | index --write「すべて最新」終了0、lint error 0/warn 0、index --check 終了0 | 引継ぎコミットのdocs変更を含む対象版で確認 |
| affected | はい | 成功 | base 9d72e0e からの差分 | `affected --base 9d72e0e…` | 終了0 | 終了0。node-runtime.md・ADR0001が変更コードの対応文書として列挙され内容も更新済み | 未カバーは README.md（今回修正）、harness管理文書（code_globs対象外） |
| change-declarations | はい | 成功 | base 9d72e0e → 作業ツリー | `harness/project/check_changes.py --base 9d72e0e…` | 終了0 | 終了0・result=ok。tests/3件は issue-14-distribution.changes.json が宣言済み | 宣言の存在は承認や意味上の安全の証明ではない |
| CI | いいえ | — | ローカル作業のみ | — | — | — | push・PRを行わないため起動しない |

### 再試行履歴

- なし（初回実行で全て期待条件を満たした）

### 最終コミット再検証（28194f7）

標準軸reviewの指摘（上表の対象版「開始SHA + README修正」と記録時点の最終コミットとの対応付けが不明確で、最終対象版での必須検証が識別できない）への対応として、ブランチ最終コミット `28194f733350df5ee738f1306f248f929e1d573a` のコミット済みツリー（検証時点で作業ツリー差分・未追跡の対象なし）に対し必須検証を再実行した。上表の各行は当時の作業ツリーに対する記録として履歴を保持する。

| 識別子 | 適用 | 結果 | 対象版・範囲 | コマンド / 確認方法 | 期待条件 | 証拠 | 理由・限界 / 再試行 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| project-required-final | はい | 成功 | 最終コミット `28194f733350df5ee738f1306f248f929e1d573a` のコミット済みツリー、junctionした既存venv 3.14.3 | `PYTHONPATH=<worktree>/src .venv/Scripts/python.exe tests/run_all.py` | 終了0・失敗0・エラー0 | 実行171件、失敗0、エラー0、終了0 | このworktreeのsrcを参照。別worktree・site-packages非参照をPYTHONPATHで担保 |
| node-install-final | はい | 成功 | このcheckout | `npm ci` | 終了0 | added 8 packages、終了0 | Node v24.21.0 / npm 11.19.0 |
| node-native-final | はい | 成功 | 最終コミット `28194f733350df5ee738f1306f248f929e1d573a` | `npm test` | 終了0・fail 0 | 13件 pass、fail 0、終了0 | 最終コミットの差分はREADME.md・docs/cli/node-runtime.md・本記録のみで、Node実装・依存・共有資産は開始SHAと同一。任意検証として再実行 |
| node-compat-final | はい | 成功 | 同上 | `OKF_TEST_PYTHON=<worktree>/.venv/Scripts/python.exe PYTHONPATH=<worktree>/src npm run test:compat` | 終了0・fail 0 | 8件 pass、fail 0、終了0 | 同上 |
| docs-final | はい | 成功 | 最終コミット `28194f733350df5ee738f1306f248f929e1d573a` のOKF文書 | `index --write` / `lint` / `index --check`（指定venv+PYTHONPATH） | 索引最新・error 0/warn 0・各終了0 | index --write「すべて最新」終了0、lint error 0/warn 0、index --check 終了0 | node-runtime補完を含む最終版で確認 |
| change-declarations-final | はい | 成功 | base `9d72e0e5798883d81789582d8879f139865d37b5` → 最終コミット `28194f733350df5ee738f1306f248f929e1d573a` のコミット済みツリー | `.venv/Scripts/python.exe harness/project/check_changes.py --base 9d72e0e…` | 終了0 | 終了0・result=ok。tests/3件は issue-14-distribution.changes.json が宣言済み | 宣言の存在は承認や意味上の安全の証明ではない |
| smoke各識別子（github-install / packed-working-tree / fresh-lock / missing-dependency / existing-script-check） | はい | 未実行 | 各識別子の記録対象版は上表のとおり | — | — | — | 最終コミットの差分はREADME.md・docs/cli/node-runtime.md・本記録の文書のみで、導入動作の検証対象（package.json・node/・src/・hook）は開始SHAと同一のため再実行せず未実行として記録 |
| CI | いいえ | — | ローカル作業のみ | — | — | — | push・PRを行わないため起動しない |

## review

- 比較点: `9d72e0e5798883d81789582d8879f139865d37b5`。対象は HEAD=2c3050d のコミット済み差分 + 未コミットの README 修正 + 未追跡の本記録。
- 上流 code-review 手順に従い、仕様軸と標準軸の2サブエージェントを並行実行した。

### 仕様軸

- 比較点: `9d72e0e…`
- 対象: committed diff（2c3050d）+ working tree diff + untracked
- 結果: 8条件すべて対応を確認。指摘2件を修正: (a) 条件2 — `scripts.okf` 占有時の統合先が無かったため別名案内を追加、(b) 条件6/1 — READMEに `npm install` のpackage.json自動作成注記がなく追加。所有範囲外として監督者へ報告: (c) `init` は空でない任意の `scripts.okf` に `npm run okf --` 案内を出す（okf-devkit呼出しか未確認。`src/`/`node/` は #19 担当範囲）、(d) 条件4の「起動対象」を生成hookまで広げて読むとhookの探索順が異なるが、#14仕様のOut of Scope「既存hookの探索方式の変更」とnode-runtimeの記載から起動スクリプトを指す解釈とした。scope creep指摘なし。
- 限界: 仕様軸エージェントはshell/git非搭載で現物ファイルとissue-14記録から差分を再構成した。差分の正確な集合は `check_changes.py` 出力で担保。

### 標準軸

- 比較点: `9d72e0e…`
- 標準: AGENTS / config / requirements / docs規約 / smell baseline
- 結果: 文書標準違反なし（宣言の形式要件、frontmatter、README修正の既存文脈との整合を確認）。smell系の判断留保: Python/Nodeのscripts.okf検出の二重実装はADR0001で文書化済み。所有範囲外として監督者へ報告: `render_hook.sh`/`render_hook.ps1` が従来の `pip install okf-devkit` を案内したまま（base時点からの既存文、src/ は編集禁止）、scaffoldの `templates/log.md`・`backlog-item.md` は裸 `okf` 表記のまま（#19範囲）。cli/scaffoldのlog.md追記は#20の統合工程に属する。
- 限界: 同上（ファイル現物ベースのreview）。

## 受入条件の照合（Issue #18）

| # | 条件 | 判定 | 証拠 |
| --- | --- | --- | --- |
| 1 | 40桁SHAのGitHub版を空の利用先へ開発用依存として導入。npm設定なしでも成立 | 充足 | README・node-runtime手順。github-install: package.jsonなしの空dirでinstall→package.json自動作成、終了0 |
| 2 | 同名起動スクリプトを確認してから設定し、無条件上書きしない | 充足 | README・node-runtimeに `npm pkg get` →条件分岐の手順。existing-script-checkで既存値検出を確認 |
| 3 | プロジェクトルートのnpm起動スクリプトで init→index→lint 成功。Python・グローバルokf・個人clone非依存 | 充足 | github-install・packed-working-treeで終了0。packedではpythonをPATHから除去し偽okf未使用 |
| 4 | 起動対象はローカルCLIに固定。PATH上の別okf不使用・欠落時は非ゼロ・自動取得しない | 充足 | scriptは `node node_modules/…` 固定。missing-dependencyで終了1。README/node-runtimeに自動取得しない旨を記載 |
| 5 | 設定+lockfileを新しい作業コピーへ渡し再導入後に同じ操作が成功 | 充足 | fresh-lock: 2ファイルコピー+新規cache `npm ci` → init→index→lint 終了0。親設定非依存の独立dir |
| 6 | READMEと利用手順で実行場所・初回準備・Git管理設定・依存実体除外・新clone/worktree準備・固定SHA更新を説明。PyPIを公開済みにしない | 充足 | README§インストールに全項目。CI例の `pip install okf-devkit`（PyPI示唆）を固定SHA GitHub導入へ今回修正 |
| 7 | 方式比較と採用理由・保守範囲・保守終了時の案内・npm非公開でも依存保守が残る | 充足 | node-runtime「配布方式の比較と採用理由」表・注記、README「定期リリースは約束しない」「保守終了時はREADMEに明記」 |
| 8 | 公開CLIを使う検証と必須テスト・文書検査を実施し対象版と結果を記録。未公開を公開版と混同しない | 充足 | 検証表で github-install（公開SHA）と packed-working-tree（未公開tgz）を分離して記録。最終コミット `28194f733350df5ee738f1306f248f929e1d573a` への必須検証は「最終コミット再検証」節で完全SHAつきで記録 |

## 残作業・妨げ・再開前提

### 残作業

- なし（本チケット範囲）。push・Issue更新・#20の統合確認は別工程

### 妨げ

- なし

### 再開前提

- 作業場所 `C:/Users/rinta/orca/workspaces/okf-devkit/issue-18`、ブランチ `shirashu687/npm-issue-18`、venv junction作成済み、smoke証拠は `%TEMP%/okf-i18-5746nLOO/`

## 次の一手

ローカルコミットのみ。公開・Issue更新は行わない。

## 完了 / 中断要約

引継ぎコミット2c3050dの実装・文書をIssue #18受入条件8項目と照合し、全項目の充足を対象版で再検証した。不足3件を文書のみで補完: README CI例のPyPI示唆修正、READMEへのpackage.json自動作成注記、node-runtimeへの別名スクリプト案内。必須Python検証171件・Node単独13件・互換8件・文書検査・変更宣言検査すべて終了0。未公開変更は `npm pack` tgzで検証し公開版の結果と区別した。二軸reviewの所有範囲外の指摘（hookのpip案内・scripts.okf非検証・templateの裸okf表記）は監督者へ報告。標準軸reviewの指摘（検証表の対象版と最終コミットの対応付け不明確）を受け、最終コミット `28194f7` のコミット済みツリーへ必須検証を再実行し「最終コミット再検証」節へ完全SHAつきで記録。当該事象は検証漏れトリガーとして IMP-0007 に登録。残存リスクはCI・他OS・別PC未検証と、公開後の統合確認（Issue #20）。
