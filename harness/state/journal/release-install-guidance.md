# 初回Release導入案内の修正

開始/実PR比較base `12cdb44c2876b50bd7337a5ea20f7744a27d7802`。fresh remote main同SHAを確認。user承認は不足時の日本語最小修正PRまでで、merge/tag移動/asset差替え/公開は対象外。rootはDraft403054686、tagv0.1.0対象12c、タグrun全10成功/3asset検証済み、現在未公開、repo publicを観測。canonical asset URLとPyPI本体はHTTP404、公開後の実取得成功は主張しない。

READMEの古いDraftPR時制と未公開PyPI取得例2箇所を修正。既存GitHub配布物の3asset取得予定URL、manifest/repository/tag/version/commit/size/hash/SHA256SUMS照合、local/global明示選択、固定ソースPython、initforce禁止/lockfile復旧を案内。guideは以前195252導入実測の履歴を保持し、現在12cとの区別と未実施consumerを明記。既存検証済みtgz同梱READMEは旧版のままで、今回の変更はそのバイトへ反映されない。タグ移動/再pack/asset更新で修復しない。rootがこの差と案内優先を説明する。

runtime/workflow/tests/version/政策/保護対象は変更しない。元repo/venv/global設定を変更しない。authorは編集commit/freezeのみ、rootがDraftPR/push/CI/独立レビュー。source固定後fullPython/Nodecompat/releaseguards/package/docs/affected/checker、hashlog後必須Pythonを実行し、未実行CI/公開と区別する。

追加許容範囲:READMEのリンク先notesとrelease手順に残った未タグ/未Draftの現在時制だけを更新、実物検証済みDraftと未公開/未consumerを区別した。新機能や公開操作なし。sourcee234d78+a2720edの実hashでshared節目logを先に記録する。全製品文書固定後にmandatoryfullを1回実行し、最後はjournal結果のみ。

## 最終source検証

対象固定source `e80fbc0822daed99a3815b3365f28f3513c08d2b`（全製品文書と実hash付きsharedlog含む）。その後の変更は本journal結果のみ。実行環境は既存 `C:/Users/rinta/Documents/1_projects/okf-devkit/.venv/Scripts/python.exe`、PYTHONUTF8=1、絶対PYTHONPATH=`C:/Users/rinta/Documents/Codex/2026-10-03/task/release-install-guidance/src`、互換は同じOKF_TEST_PYTHON。

| 結果 | 実コマンド | 対象・証拠 |
| --- | --- | --- |
| 成功 | 既存venv tests/run_all.py | 全261件、失敗0/error0/skip1（既存Windows symlink）。repo外workspace release-guidance-python.txt。 |
| 成功 | npm ci; npm test; npm run test:compat; npm run test:release; npm run test:package | npmci8/audit9/vuln0。Node31/compat14/guards14/package3、全失敗0/skip0。release-guidance-{node,compat,guards,package}.txt。packageテストは一時的な検証物で、既存Releaseの再pack/差替えではない。 |
| 成功 | Python index --write/lint/index --check/render --check; Node lint/index --check/render --check | index変更不要、双方lint0error/0warn、index最新、render34pages/書込0/削除0/warn0。 |
| 成功 | affected --base12c; check_changes.py --base12c --headsource（task/PR両scope）; git diff --check | docs-only影響文書なし、未カバーREADME/journalを直接確認。保護対象0、宣言不要、両checker0/diff0。最終HEAD証拠はcommit後にrepo外保存。 |
| 失敗 | 今回authorの必須検証 | なし。既存案内の問題は修正対象として記録、非公開URL404は既知の状態確認で導入成功ではない。 |
| 未実行 | consumer導入、公開後URL取得、実agentStop、PR最終CI、PRmerge/tag移動/asset差替え/公開 | consumer以降は未許可の別工程。rootがDraftPR/CI担当。ローカル成功と既存tagrun10成功は本PRCIを意味しない。 |
| 実行不能 | 必須ローカル検査 | なし。 |

retroゲート照合範囲:条件付き公開の依頼/不足時の最小PR範囲、元README2PyPI誤例と旧時制、immutable配布物の差、source全差分、既存成功証拠/新source全local結果/引継ぎ。調査で見つけた既存不足を計画どおり修正しており、今回authorの要件取りこぼし、回帰、誤成功、反復手戻り、重大環境摩擦はない。台帳採用/新候補/回数更新なし。独立Spec/Standardsはroot割当で最終報告待ち、journalが判定の不足を成功扱いしない。次はrootの二軸review/exactSHA DraftPRCI。重大な未解消差は既存tgz同梱README旧版であり、今回文書PRでは直らない。追加PRmerge/新タグ・新配布物/現Draft公開の判断はユーザーの承認範囲と照合して親が報告する。

authorは記録commit後全編集をfreezeし、cleanHEADと日本語PR本文外稿を親へ渡す。実装・workflow・版・テスト規約は開始mainと同一。
