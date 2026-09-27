# 作業記録: Issue #14 配布方式の検討

## メタデータ

- 状態: 中断（仕様のIssue反映とローカル実装・検証・二軸review済み、コミット後の記録とコード公開工程が残る）
- 開始・最終更新日: 2026-09-27（Asia/Tokyo）
- 作業場所: C:/Users/rinta/orca/workspaces/okf-devkit/npm
- ブランチ: shirashu687/npm
- 開始SHA / 最新HEAD: 9d72e0e5798883d81789582d8879f139865d37b5
- 作業者: Codex
- 課題: https://github.com/shirashu687/okf-devkit/issues/14

## 目的・範囲

- Pythonを使えない利用環境で、リポジトリ全体のcloneに代わる導入方法を検討する。
- 利用者はnpmレジストリ公開後の運用・保守負担を懸念し、公開に消極的。
- 完了条件はIssue #14を参照。利用者の「okですそのまま進めましょう」で共通理解と実装への移行を確認。実装時点では公開・push・Issueへの投稿を行っていない。後続の明示的なto-spec呼出しにより、既存Issue #14の仕様本文とtriage状態の更新が許可された。コードのcommit/pushは対象外。

## 開始時の状態と今回の変更

- 開始時の `git status --short` は空。既存変更なし。
- 今回の変更: READMEとNode導入手順、既存ADRへの手順参照、Python/Nodeのinit、共有AGENTS/CONVENTIONSテンプレート、両実装のテストと比較テスト、作業記録と保護対象宣言、retroの観測IMP-0006。新しいドメイン語はなくCONTEXTは未変更。配布経路は変更可能なため新規ADRは作らずHow-Toに比較と決定を記録。

## 判断と根拠

- README、package.json、docs/project/decisions/0001-node-runtime.mdを確認。Node.js 22+の独立実装、bin名okf、npm packとローカル導入経路が既存。
- ADR0001はnpmレジストリ公開を別作業とする。公開はNode版を使うための必須条件ではない。
- npm公式資料はtgzとGit由来のインストールを説明する: https://docs.npmjs.com/cli/install/
- 公開後の更新停止は、非推奨化と案内による終了も選べる: https://docs.npmjs.com/deprecating-and-undeprecating-packages-or-package-versions/
- 暫定推奨はレジストリ公開を保留し、既存npm packの成果物を配布する方法を検討すること。依存取得の通信、対応環境、更新手順は別途確認が必要。

## 設計の合意と経緯

第1ラウンドの合意:

1. 本人・少人数向けを対象とする。
2. 主な痛点は毎回のコマンド入力と、AIによる実行時のPATH探索失敗。clone解消だけでは目的を満たさない。
3. Node.js 22+・npmを利用でき、初回導入はオンライン、導入後はローカル実行を前提とする。

第2ラウンドの合意:

4. プロジェクトごとの開発用依存として導入し、package.json/package-lock.jsonを管理する。JavaScript以外のプロジェクトも対象。
5. PATH探索失敗はokfやclone先のスクリプトが対象であり、Node/npm本体ではなかった。

起動方針は `npm run okf -- …` に統一する。推奨する詳細はscriptsから導入済みローカルCLIを明示して呼び、未導入なら失敗させること。利用先向けAGENTSテンプレートと初期化後案内に裸のokfが残っているため、導入方式に合わせた説明の整合も必要。Python利用者の既存案内との共存は実装時に確認する。

`npm run` はローカルのbin探索を支援するが、npm/Node本体のPATH問題までは解決しない。根拠: https://docs.npmjs.com/cli/v11/commands/npm-run/

第3ラウンドの提案（wait-whatによる説明後にすべて合意）:

- 配布経路: 利用者の主な痛点と運用負担への懸念を踏まえ、固定コミットのGitHub直接導入を第一候補とする。初期のtgz推奨から変更した理由は、Release・配布物作成作業を追加せず起動問題を解決できるため。GitとGitHubへのアクセスが必要。tgzは代替候補として維持。どちらも今回の導入smokeは未実施。
- 更新は明示的に固定版とlockfileを変更し、日常の実行で最新版を自動取得しない方針を提案する。定期リリースは約束せず、保守終了時はREADMEに状態を記載する案。
- 新しいclone/worktreeごとに `npm ci` を初回実行し、インストールを共用しない方針を提案する。既存hookは主worktreeの依存も探索するが、通常起動のローカル固定とは区別する。

完了確認案: グローバルokfと元cloneのパスを使わないクリーンな利用先で、合意した導入→npm script設定→init→lintを確認。既存scriptsを壊さないこと、未導入時の明確な失敗、Python向け案内との共存を確認する。

## 摩擦観測とretroゲート

- 開始時台帳: 評価中5/10、試行0/3、採用済み0。期限超過の試行・見直し対象なし。
- 確認範囲: 依頼、既存ADR/README/package設定、今回の記録を照合。調査・質問は通常の設計検討であり、この範囲にfull retroのトリガーなし。
- 既存venvがない点は環境上の検証限界として記録。代替Pythonの導入・検証成功への読み替えはしない。
- 処理済み事象・台帳ID: なし。未確認範囲は実利用環境と配布物の動作。次は利用者回答を反映する。

実装後のretroゲート: 依頼・合意・全差分・検証と再試行を照合。初回smokeの配置誤りによる検証失敗・再試行を対象にfull retroを実施し、症状・原因・対処・確認方法を台帳IMP-0006に記録した。既存IDとは症状と適用範囲が異なるため新規の観測とした。評価中6/10、試行0/3、採用済み0。恒久ルールの追加や採用判断はしていない。製品の他OS/CIは未確認。

## 検証

| 識別子 | 適用 | 結果 | 対象・確認 | 証拠・限界 |
| --- | --- | --- | --- | --- |
| project-required | はい | 実行不能 | 開始SHA + 本記録、`.venv/Scripts/python.exe tests/run_all.py` | 指定venvが存在せず、コマンド未認識で終了1。テスト本体は未起動。既存venvを利用できる環境で再実行が必要 |
| OKF / Node追加検証 | いいえ | — | 管理記録のみ | docs、Node実装、依存、共有資産、hookは未変更 |
| CI | いいえ | — | ローカル対話・記録 | 起動していない |

第2ラウンドの記録更新後も必須コマンドを再試行。同じ指定venv欠落により終了1、実行不能。初回結果と同様、テスト本体は未起動。

第3ラウンドの記録更新後も同じ必須コマンドを実行。指定venv欠落により終了1、実行不能。テスト本体は未起動。

## review

- 比較点: 開始SHA。未追跡の本記録を含む。
- 仕様軸: code-reviewの別エージェントが開始SHAからの全作業差分と未追跡ファイルを確認し、修正必須0件。方式選択、固定導入、ローカル起動、再導入、生成説明、Python維持を確認。正式log追記とIssue更新は未完了との留保。
- 標準軸: 別エージェントがAGENTS/config/requirements/文書規約/writing-for-agentsとsmell baselineを適用し、修正必須0件。設定の読取りのみ、既存設定保持、テンプレート共通化、文書配置を確認。正式log追記とIssue更新は完了扱いしない。

## 実装後の検証と残作業

ローカル環境はWindows、Node v24.21.0 / npm 11.19.0。以下は開始SHAと今回の作業ツリー差分に対する結果。CIや他OSの成功は推定しない。

| 識別子 | 適用 | 結果 | 実行・証拠 | 限界 |
| --- | --- | --- | --- | --- |
| project-required-retry | はい | 成功 | 既存venvへのjunctionを作り、`PYTHONPATH=<このworktree>/src` で `.venv/Scripts/python.exe tests/run_all.py`。171件、失敗0、エラー0、終了0 | main worktreeにあった既存Python 3.14.3を使用。以前の実行不能は保持 |
| node-install | はい | 成功 | `npm ci` 終了0 | このcheckoutの依存 |
| node-native | はい | 成功 | `npm test` 13件、失敗0、終了0 | Python不要の独立テスト |
| node-compat | はい | 成功 | `OKF_TEST_PYTHON=<このworktree>/.venv/Scripts/python.exe` と同じPYTHONPATHで `npm run test:compat`、8件、失敗0、終了0 | 編集中のPythonソースを参照していることを確認 |
| github-install | はい | 成功 | GitHubの開始SHAを空の別フォルダへinstall、scripts設定、init→index→lint、終了0 | 取得できる既存版で配布経路を検証。未公開の今回変更を取得したとは扱わない |
| fresh-lock | はい | 成功 | packageとlockを独立フォルダへコピー、新規cacheでnpm ci→init→index→lint、終了0 | Git/npmのユーザー設定はこのマシンのもの。別PC検証ではない |
| packed-working-tree | はい | 成功 | 今回の `npm pack` から別の空白入りパスへ導入。Pythonと元cloneをPATHから外し、偽okfをPATH先頭へ置いてinit→index→lint、終了0。生成AGENTSのnpm呼出しを確認 | 公開前の変更はローカルtgzで検証 |
| missing-dependency | はい | 成功 | smoke内で導入済みCLIを一時renameしnpm scriptを実行、MODULE_NOT_FOUND・非ゼロ。偽okfの終了93を使わず、元へ復元 | 期待した失敗を検証 |
| docs | はい | 成功 | 指定venvでindex --write / lint / index --check。索引最新、error 0 / warn 0、各終了0 | 文書の最終差分でも再確認する |
| affected | はい | 成功 | 指定venvで開始SHAからaffectedを実行。Node手順とADRを更新し、未カバーのCLI・共有templateを手順のcode_globsへ追加 | 未カバーREADMEと管理記録は直接確認 |
| change-declarations | はい | 成功 | 指定venvでcheck_changes.py --base、保護対象テスト3ファイルを宣言、終了0 | 人の承認や意味上の安全性の保証ではない |
| log-generation | はい | 成功 | `log --range <開始SHA>..HEAD --write` 終了0・追記対象なし | 変更は未コミットのためcli/scaffold logへの正式追記は未完了 |

smoke証拠のローカル保存先は `%TEMP%/okf-issue14-a4cea4c154794c3497a8c21f261ab74d`（初回GitHub導入・tgz）、`%TEMP%/okf-issue14-fresh-88b44a2287d04a8fa3e517f0c59b0ac1`（再導入）、`%TEMP%/okf-issue14-changed package-1f2f358006424fe89ce59beea12a1ec9`（今回変更の導入）。認証情報・ログ全文は保存しない。

検証履歴: 初回の追加smokeを既に初期化したフォルダの子に作ったため、npmとCLIの親探索が働き生成先が親になった。パッケージの不具合とは判定せず、独立した一時フォルダで同じ手順を再実行して成功した。初回の生成案内確認は失敗として保持する。

未完了はコミット後のlog生成とコード公開後のIssue完了条件の更新。仕様本文と現時点の検証結果は後続のto-spec依頼でIssueへ反映済み。コミット前の変更に架空の出典ハッシュを付けない。今回のCLIとテンプレートをGitHubから導入できるのは、変更がpushされた後になる。

次の一手はコミット・公開を依頼された時点で差分を再確認し、実在コミットからcli/scaffoldのlogを生成すること。push後にIssue #14の完了条件と対象版を更新する。コードはローカル変更までであり、Issue全体の完了・コード公開済みとは報告しない。

最終確認: 文書と台帳の差分を含む状態でPython必須テストを再実行し171件成功。index生成・lint（error 0 / warn 0）・index確認・保護対象宣言検査・git diff --checkはすべて終了0。台帳とretro追記の追加標準reviewも指摘0件。残る制約は上記のコミット・公開工程と、未実行のCI/他OS検証。

## to-specによる仕様公開（2026-09-27）

- 依頼: 利用者がto-specを明示。新しい面談はせず、既存の合意を仕様化して課題管理先へ公開する。
- 対象操作: shirashu687/okf-devkitの既存Issue #14の本文を仕様へ更新し、カテゴリenhancementを維持、状態ラベルneeds-triageをready-for-agentへ置換する。Issueはopenを維持。新規Issue・コメント・PR・コード公開は行わない。
- 検証境界: 合意済みの「独立した利用先への導入→初期化→索引生成→lint」と既存Python/Nodeの互換性テストを採用。新しい境界・インターフェースの設計を追加しないため再質問しない。
- 保存先: 仕様の正本はIssue本文。送信用の一時MarkdownだけをOSの一時フォルダに作る。ローカルに別の受付・管理先を設けない。
- 送信内容: 課題、採用方式、利用者ストーリー、実装・検証の判断、対象外、公開状況。認証情報、個人の絶対パス、ログ全文を含めない。既存版のGitHub導入と未公開変更のローカルtgz検証を区別する。
- 公開後は本文・ラベル・open状態を再取得し、送信した仕様との一致を確認する。

結果: to-spec所定の7セクションと24件の利用者ストーリーを含む仕様を、既存Issue #14の本文として公開した。再取得した本文は送信用Markdownと一致し、ラベルはenhancement / ready-for-agentのみ、状態はOPENを確認。元の目的・関連Issue・完了条件を継承し、既存の未コミット実装と検証の限界を明記した。

今回の記録更新に対する必須Pythonテストは171件、失敗0、エラー0、終了0。Nodeコード・依存・共有資産・OKF文書はこのto-spec操作では変更せず、前回の検証結果と区別する。仕様軸は会話合意との一致・追加要件なし・既存検証境界の再利用を確認、標準軸はテンプレート・課題管理先・ラベル排他・外部送信の明示許可・秘密情報非掲載を確認した。追加のretroトリガーなし。仕様公開という今回の依頼は完了し、実装全体の残作業は上記のとおり。

## to-ticketsの分割案（2026-09-27、承認済み）

- 明示依頼されたto-ticketsを適用。Issue #14の最新本文・コメント（0件）と既存open課題を再取得し、重複する子課題がないことを確認した。
- 親Issueは本文・状態・ラベルとも変更しない。チケットは承認後にGitHubへ作成する。今回の草案を独立したローカル課題管理先にしない。
- 既存の未コミット実装と検証結果を引き継ぐ前提。新規に同じ実装を作り直さず、各チケットで対象差分と受入条件を照合する。先行する構造変更は不要。

| 仮番号 | タイトル | 成果と受入条件の要点 | Blocked by |
| --- | --- | --- | --- |
| 1 | 固定版をプロジェクトへ導入し、ローカルCLIで実行・再導入できるようにする | GitHub固定SHAから導入してinit→index→lint。グローバルCLI・元cloneに依存せず、依存欠落時は失敗。新しい作業コピーでlockfileから復元でき、READMEの初回準備・更新・保守範囲の説明も揃う | なし |
| 2 | 初期化したAI向け説明と既存プロジェクトの案内を起動設定に揃える | 設定済みnpm scriptが生成説明・初期化後の案内へ反映され、その案内で実行できる。設定のないPython利用者の従来動作と編集済み文書を保持。既存利用先の移行手順と互換性を確認 | なし |
| 3 | 統合した固定版をGitHubから導入し、再現できる検証結果と履歴を揃える | 1・2を含む実在コミットを対象に、GitHubからの新規導入・再導入・生成案内での実行を確認。必要な既存検証・二軸reviewと影響層の変更履歴を対象版へ対応付ける。npm/PyPI公開や親Issueの更新・クローズは含めない | 1、2 |

1と2は同じ合意済み起動契約をそれぞれ既存CLIと一時プロジェクトで確認できるため、相互の阻害関係を付けない。3だけが両方を含む版を必要とする。コードのcommit/pushはチケット公開の承認と区別し、実施時の権限を確認する。

仕様軸では親仕様の導入・日常実行・再導入・生成説明・既存移行・Python維持・統合確認を3件で覆い、標準軸では縦の利用経路、真の依存だけの辺、GitHubを正本とする配置、親Issue不変更を照合した。次の一手は利用者へ粒度・依存・統合分割の希望を確認し、承認された案だけを起票すること。追加のretroトリガーなし。

検証: 今回の草案記録更新後、既存venvで必須Pythonテスト171件成功（失敗0・エラー0・終了0）。git diff --checkも終了0。製品コード・Node依存・OKF文書に今回の追加変更はなく、それらの追加検証は適用外。親Issueへの書込みと新規起票は未実行。

利用者の「いいですよ」で3件の分割と依存関係を承認済み。対象操作はshirashu687/okf-devkitへの新規Issue3件と、3件目を1・2件目がブロックするGitHub native依存の設定。新規起票時はプロジェクト規約のneeds-triageを付け、承認済み分類としてenhancement / ready-for-agentへ揃える。親#14は本文内の参照だけとし、親を変更するsub-issue登録・本文更新・クローズは行わない。本文に秘密情報・個人の絶対パス・ログ全文を含めず、実装の再作成を避ける引継ぎ情報と受入条件を記載する。

## to-ticketsの公開結果

- [Issue #18](https://github.com/shirashu687/okf-devkit/issues/18): 固定版の導入・ローカル実行・再導入。ブロッカーなし。
- [Issue #19](https://github.com/shirashu687/okf-devkit/issues/19): 起動設定に沿う生成案内と既存移行。ブロッカーなし。
- [Issue #20](https://github.com/shirashu687/okf-devkit/issues/20): 統合した固定版のGitHub導入確認と検証・履歴の対応。#18・#19によるblocked-byをGitHub標準の依存関係として設定。
- 3件ともenhancement / ready-for-agent、OPEN。受入条件・親への参照・既存未コミット実装の引継ぎ注意を記載した。
- 投稿後に各本文と送信用Markdownの一致、ラベル排他、OPEN状態、native依存の正確な集合を再取得して確認。親#14のタイトル・本文・状態・ラベルは実施前と一致し、親へ書込みは行っていない。
- 公開に使ったAPIはGitHub公式のissue dependencies仕様を確認した: https://docs.github.com/en/rest/issues/issue-dependencies
- 記録更新後の必須Pythonテストは171件成功、失敗0・エラー0・終了0。製品コード・Node依存・共有資産・OKF文書への追加変更なし。仕様軸は承認済みの3分割・依存のみで追加スコープがないこと、標準軸はGitHubを正本とする配置・起票時ラベルからの状態遷移・親不変更・外部操作の許可範囲を確認した。追加のretroトリガーなし。
- 承認済みチケットの公開依頼は完了。次に着手可能なのは#18・#19。#20は両件の完了後に進める。コードのcommit/pushや親Issueの完了操作は、この起票作業では行っていない。
