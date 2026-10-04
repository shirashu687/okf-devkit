# Issue #12 stage2: YAML所有者の分離

- 開始SHA: `5e5dea889920fb56075687d5ade4b01e612648b9`、専用worktree issue12-yaml、branch codex/issue12-yaml、開始時clean。PRは固定stage1 branch codex/issue12-pure-helpersへの依存PRでありmainへ直接出さない。
- 承認範囲: yamlio.pyへ既存parser/serializerを移動。normalDoc/Bundleは実yamlio backend ownerを利用し、legacycli.parse_yamlの旧cli._pyyaml差替えはexplicitbackend adapterで保存。例外classと旧cli名前は同一class/functionの再exportで維持。新機能/削除/公開/実設定/hook変更なし。
- 設計:省略backendはyamlio._pyyaml、明示Noneは内蔵parserを選ぶsentinel。tests/helpers.pyとtest_yaml.pyの差替えを実ownerへ移し、context testsでactualMini構築観測、legacydirectとnormalownerを別検証。python -S新processで実PyYAML import不在のfrontmatter/config/拒否構文を確認。
- stage1 errors.py/fsutil.py/sharedcacheを維持し、Doc/Bundleの本体分離は後段とする。package metadata、Node runtime、#32規約・PR36は変更しない。
- 検証前:元repo既存venvのみ使用しPYTHONPATHを本worktree/srcへ。focus/fullPython、npmci+Node+compat、affected/docs/globs/log/index/lint/render、task/PR宣言と二軸独立reviewを実施して最終freezeSHAを親へ渡す。GitHub操作/pushは担当しない。
- retro開始確認:固定baseledger評価10/10・試行0/3・採用0・確認日2026-10-04、期限付き試行/採用見直しなし。既存history/IDs/countsを保持、新観測・採用を予定しない。未確認の実agentイベントは検証対象外。
- 開始時状態:実装前。保護対象3testファイルを事前task/PR宣言。

## 実装とfocused検証

- 事前宣言後に既存test3を移行し、新owner/default/明示None/explicitbackend/legacyalias/例外identity/normalDoc独立/実import不在の回帰条件を追加。移動前の意図したredはyamlio module未実装によるImportError、`issue12-yaml-red.txt`。予定されたTDD redであり予期しない製品失敗や成功として記録しない。
- parser/serializerの既存blockを構造を変えず移動し、変更はoptionalbackend所有場所、sentinel選択、正常Doc/configの3callsite、旧直接呼出しadapterに限定。旧YAML private helpers/constants/例外・serializerもalias再export。yamlio392行、cli2422行（最終200行条件未達）。
- focused実行: `test_yaml.py` 12件/skip0成功、`test_cli_context.py` 7件/skip0成功。actual `python -S` import不在、Mini constructor観測config/defaults/frontmatter、legacybackend差替えがnormalownerへ干渉しないことを確認。
- affected固定base5e5deaの出力5文書(architecture/commands/module-migration/output-cleanup/scaffoldreference)を本文+UTC時刻+yamlio code_globs更新。bundle外の宣言/worklogは直接確認。stage2は新機能を追加せず、cleanup/renderer/hook/Node/配布設定を変更しない。

## ローカル検証と独立事前review

対象:開始5e5dea+stage2 source/tests/docs作業tree。元repo/既存venvは変更せず、指定pythonとPYTHONPATH=本tree/srcを利用した。

| 状態 | 実コマンド | 結果・証拠 |
| --- | --- | --- |
| 成功 | 指定python `-m unittest discover -s tests -p test_yaml.py -v` / `-p test_cli_context.py -v` | YAML12・context7、skip0。旧既存assertions保持、実backend constructor/safe_loadとactual -S不在の経路を確認。 |
| 成功 | `PYTHONUTF8=1; PYTHONPATH=issue12-yaml/src; <既存venv>/python.exe tests/run_all.py` | 全219件/失敗0/エラー0/skip1（既存Windows symlink制約）。repo外作業workspace `issue12-yaml-python.txt`。baseline213から新owner回帰6件を追加。 |
| 成功 | `npm ci` / `npm test` / `OKF_TEST_PYTHON=<既存venv>/python.exe; npm run test:compat` | npmci8added/9audit/vulnerabilities0、Node30pass/0fail/skip0、互換13pass/0fail/skip0。`issue12-yaml-node.txt` / `issue12-yaml-compat.txt`。 |
| 成功 | Python `affected --base 5e5dea889920fb56075687d5ade4b01e612648b9`, `index --write`, `lint`, `index --check`, `render --check` / Node `lint`,`index --check`,`render --check` | 影響5文書の本文・実UTC・code_globs対応、source未カバー0（bundle外worklog/宣言のみ）。index書込不要、両lint0error/0warn、index最新、render31page/0warn/書込0削除0。 |
| 成功 | task/PR `check_changes.py --base 5e5dea889920fb56075687d5ade4b01e612648b9`（PRは--scope pull-request） / `git diff --check` | 両result=ok、exactprotected3testpaths。startbase/stackPRbaseは固定stage1同SHA、historical stage1宣言は変更しない。 |
| 成功 | 元cliとyamlioの移動function/class AST比較 | parse_yamlのbackend選択以外の12定義がAST同一。serializer/parser subset・例外bodyを変更しない。 |
| 失敗（意図したTDD red、実装後成功） | 移動前新testsのfocused起動 | yamlio未実装ImportError。予測したredであり、製品成功やunexpected失敗として扱わない。 |
| 未実行 | stage2 exactSHA CI/GitHub操作/stackPR作成・push | root担当。ローカル成功をCIへ代用しない。stage1CI状態とstage2の新SHAを区別。 |
| 実行不能 | 必須ローカル検証 | なし。既存symlink skipの環境理由を保持。 |

独立事前review:root割当の仕様investigate・標準cleanup_pythonが全source/test/docs差分を確認し各blocking0と親から受領。実装commitとhash付き層log・最終freeze後の記録差分は親が再確認する。

retro終了判定（今回追加範囲）:要求、固定sourcebase、予定redとfocused/full結果、二軸review、境界・状態を照合。意図したred以外の予期しない失敗/差し戻しなし、fullretro新トリガーなし。処理済みIDなし。ledger評価10/10・試行0/3・採用0を変更せず、過去観測・CI失敗を再加算しない。未確認は実CLIイベント・最終SHA CIであり、次の一手はrootのreview/pushとCI。

## source固定と最終freeze準備

- source commit `e27a64da6b687021579a61b26b7167f89d7d3a25`。以後のsource/tests編集は停止し、CLI層logへ実在hashを添えた。stage2 source変更はsrc/okf_devkit/**とtests/**のCLI分類なので、render/scaffold本文の依存説明もCLI層へ一つの意味単位として記録し、変更していないrenderer/scaffold実装の新logは作らない。
- source commit後の差分はhash付きCLI logと本worklogのみ。最終docsチェックとlog追加後mandatoryfullPythonを同じsourceで完了後、記録commitをfreezeしてstage3子worktreeのbaseを親へ渡す。

## 最終freeze記録

- CLI層log追加後のmandatory full Pythonを完了: `Ran 219 tests in 70.696s` / `OK (skipped=1)`、219件/失敗0/エラー0。sourceは `e27a64da6b687021579a61b26b7167f89d7d3a25` から不変、追加差分はhash付きCLI logとworklogのみ。repo外作業workspace `issue12-yaml-python-final.txt` に実結果。
- 最終Python/Node lintは双方error0/warn0、index最新、rendercheck31page/warn0/書込0削除0。Node30/compat13の既完了検証は同じsource/fixturesを対象にした結果であり、この記録更新を理由に重複実行していない。
- 追加AST照合:移動した7定数・regexも元cliと完全一致。例外12定義のAST一致、旧19名alias再export、normalowner/legacyadapter/実import不在の差替え証拠を維持。
- freeze後は担当source/docs/tests/journalに追加編集しない。親が固定finalHEADのtask/stackPR宣言と記録差分をreviewし、stage3子worktree、DraftPR、push/CIへ進む。後段はDoc/config分離であり、この段階でIssue #12全体をcloseしない。
