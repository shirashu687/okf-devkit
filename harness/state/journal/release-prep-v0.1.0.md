# v0.1.0 日本語PreRelease準備

開始・task/PR比較SHA: `6335d0d1d562cd033a2a7e4a734482e2b7743884`。main CI37206077913の全11job成功は親からの引継ぎであり、このPRの最終CIとは区別する。

## 目的・範囲・権限

既存main配布workflowの採用済み時制、公開予定v0.1.0の日本語ノートを整える。公開意図はpublished PreRelease、現在未公開。準備PRのレビュー/main統合/最終CIの後、タグ、初回タグworkflow、同一bundle Draft検査、別承認の公開を分ける。既存安全手順・3asset同一バイト・Ubuntuのみpack・private/npmPyPI非公開方針を保持する。

変更はrelease-node手順、v0.1.0ノート、install案内リンク、CLI生成indexes、限定shared log、作業記録。全4版値0.1.0/private trueを読み取り確認。コード/依存/保護対象/検証政策/設定は変更しないのでchanges宣言の対象はない。元repo/venvと実利用者global設定は変更しない。外部push/DraftPR/CIはroot担当、準備PR merge/tag/GitHubRelease書込み/公開は対象外。

## 設計・検証計画

既存release-node手順を更新し、実装owner/配布scriptに新Referenceのcode_globsを紐付ける。preparedノートを実配布/初回run成功の証拠と呼ばない。16共通資産=defaults1+assets3+scaffold12、required28全体=資産16+Node9+package/LICENSE/README3。Node archiveとPython sourceを区別。公式gh release edit(2026-10-04読取)のdraft=false/prerelease/latest=false/notes-file操作形は未実行例として記載。

全Python/Node/compat/releaseguards/package/docs/固定SHA差分検査と独立仕様・標準review、hash log後の最終Python/HEAD記録をfreezeする。CI/タグrun/実Draft/実公開は未実行。失敗・実行不能は成功へ読み替えない。

## 初期調査の修正

author補助scriptの版照合はpyproject.toml読取でWindows既定cp932を使いUnicodeDecodeErrorとなった。製品/テストの失敗ではなく調査scriptの誤りである。全read_textにUTF-8を明示し、4版値とprivate trueを再照合して成功。文書3件更新は途中まで完了していたため差分を確認して継続し、重複変更/製品修正はない。index2件生成、lint0error/0warn。retroで原因・影響・記録を照合する。

## source固定と実測検証

文書source commit `c4b453f545584b5855d471f0b2b621322c6a7dbb`、開始main6335d0dを対象に、既存venvと本tree絶対PYTHONPATHで検証。source後の製品文書変更はactualhash付きshared節目logだけで、runtime/tests/manifests/workflowは不変。親割当独立Spec/Standardsはsource全差分findings0/blocking0。

| 結果 | 対象・実コマンド | 証拠 |
| --- | --- | --- |
| 成功 | PYTHONUTF8=1; PYTHONPATH=C:/Users/rinta/Documents/Codex/2026-10-03/task/release-prep-v0.1.0/src; C:/Users/rinta/Documents/1_projects/okf-devkit/.venv/Scripts/python.exe tests/run_all.py | 261件/失敗0/error0/skip1(既存Windows symlink)。repo外workspace release-prep-python.txt。 |
| 成功 | npm ci; npm test; OKF_TEST_PYTHON=同じ絶対venv; npm run test:compat; npm run test:release; npm run test:package | npmci8packages/audit9/vuln0、Node31/compat14/guards14/package3成功skip0。release-prep-{node,compat,releaseguards,package}.txt。 |
| 成功 | Python index --write/lint/index --check/render --check; Node lint/index --check/render --check | index2件生成、双方lint error0/warn0・最新index、HTML34pages/書込0/削除0/warn0。main32pagesから新notes+indexの2page追加。 |
| 成功 | Python affected --base 6335d0d1d562cd033a2a7e4a734482e2b7743884; check_changes.py同base; git diff --check | docs-onlyのためaffected文書なし、未カバーはbundle外journalだけ。全6差分の本文/関連/実owner globs/日時/生成indexesを直接review。保護対象0なので宣言不要、checker0。 |
| 失敗 | 初期のauthor版照合補助script | pyproject読取defaultcp932でUnicodeDecodeError。UTF-8明示に修正して再照合成功。製品/mandatorytest不良なし、失敗を消去せず前節に記録。 |
| 未実行 | 本PR最終SHA CI、tag用workflow、実Draft生成、PreRelease公開 | rootが準備PR/push/CI担当。このPRのmerge/tag/Release書込/公開は未許可・未実行。main受入を当該PR/初回release成功へ転用しない。 |
| 実行不能 | 必須ローカル検査 | なし。 |

## 摩擦観測とretroゲート

照合範囲:依頼/許可境界、planned six-file source差分、版read-only照合、全部local結果、二軸review、引継ぎ。初期補助scriptの単発encodingエラーは少量の再読取で回復し、製品不適合・検証漏れ・誤成功報告・要件の修正・反復手戻り・大きな環境摩擦は観測しない。失敗は記録したが、§2のfull retro triggerの大きな摩擦等には単独で該当しないと判断する。処理済み事象:補助script encoding、台帳ID更新なし。ledger評価10/試行0/採用0と履歴/回数は変更しない。未確認は最終PR CIと初回実タグrun/Draft/公開、次の一手はrootによるexactSHA PR検証と将来別承認工程。新規採用/効果を作らない。

shared節目logは新ノートと公開準備の一つの意味単位、実sourcehashc4b453fでCreationを追記した。CLI/render/scaffold実装logへ架空の変更を作らない。log後必須Pythonを同じruntime sourceで再実行し、製品文書を固定してjournal結果のみ追記する。

## 最終freezeのローカル証拠

shared log追加後の必須Python全suite完了:261件/失敗0/error0/skip1、exit0。実証拠 `C:/Users/rinta/Documents/Codex/2026-10-03/task/release-prep-python-final.txt`。テスト実行時はsourcec4b453f+finalsharedlog/journal、実装・テスト・依存・設定は開始mainから不変。初回fullも成功として残し、最終製品文書treeの証拠はfinal logを正とする。

最終文書検査はPython/Nodeともlint0/0、index最新、render34pages/書込0/削除0/warn0。Node31/compat14/guards14/package3の証拠は同じruntime/sourceを検証した結果として有効。再検証を未実行CIへ読み替えない。保護/上流管理パス0、宣言の追加なし。全committed差分とgit diff --check、exacttask/PRbase6335のHEAD検査はcommit後に保存して親へ渡す。

この記録commit後は編集を凍結する。独立finalmetadataレビュー・push/DraftPR・CIはroot担当。日本語PR本文はrepo外workspace `release-prep-pr-body.md` に保存済み。authorによる外部変更はなし。準備PR merge、タグ、Release書込み・公開は依然対象外で、将来工程の未実行コマンドを実行しない。
