# 作業記録: Issue #21 Backlog progress

## メタデータ
- 状態: 進行中
- ブランチ: codex/issue21-backlog-progress
- 開始SHA: 9d72e0e5798883d81789582d8879f139865d37b5
- 作業場所: isolated issue21 worktree
- 開始時の変更: なし（git status確認）
- 作業者: Codex

## 目的・範囲
Issue #21 の読み取り専用状態一覧を既存HTMLへ追加する。Python/Node双方でrootと設定Backlog indexに件数・タイトル・ID・本文リンクを表示。sidebarの検索対象へファイルIDとstateを追加。
対象外: 編集/同期、新規アプリ、公開、merge、Issue tracker移管の取消。
完了条件: https://github.com/shirashu687/okf-devkit/issues/21

## 判断と根拠
main基準。npm未統合差分はrenderer/assetsに変更なく独立可能。既存index/status同様、設定backlog.dir直下を一覧対象としBacklog Itemのみ集計。設定states/state_orderを保持し未知値も隠さない。空一覧はrootにも明示。statusとstateは分離。任意の新規filter UIは初期範囲外、既存sidebar検索でタイトル/ID/stateを検索。
implement skillとcode-review skillを読み適用。保護対象テスト変更はtask/PR各scopeで宣言する。

## 摩擦観測とretroゲート
開始時: ledger 評価中5、試行0、採用0、期限付き試行なし。既存環境のUTF-8出力差は読み取り方法で解消。終了時に差分/検証/review照合。

## 検証
未実行: required Python, npm ci/test/compat, affected, index/lint/check, task/PR declarations, final SHA CI。

## review
未実行: 固定開始SHAで仕様軸・標準軸の独立review。

## 次の一手
実装と混在/空/再生成/設定/readonlyの回帰テスト。

## 検証履歴
- 成功: 初回Python required full 177件、失敗0/error0/skip0（新テストclassが既存fixtureを継承し既存7件も重複実行していたため、fixtureのみの単独classへ変更して最終全件を再実行）。
- 成功: npm ci exit0、初回npm test11件。
- 失敗: 初回compat追加テストはroot index fixture未作成のためENONENT。実装差異ではなくfixture不足。root index作成を両ランタイムに追加し再実行。
- 成功: 最終npm test12件/pass12/fail0、compat8件/pass8/fail0。
- 失敗: 初回OKF lint error0/warn1、generated.by machine:codexはActor語彙外。process:codexへ修正。
- 成功: 修正後index --write/index --check exit0、lint error0/warn0。
- 成功: affected固定開始SHA。node-runtime/ADRを更新しrenderer/assetsの新規影響文書を追加。
- 成功: check_changes task/pull-request 両scope exit0。保護対象testsのみを正確に宣言。検査・CI・制約の変更なし。
- 成功: git diff --check 空白エラーなし。
- 未実行: 最終Python full（実行中）、final SHA CI、独立review。
- 証拠: workspace親のissue21-python.log/issue21-node-final.log/issue21-compat-final.log/issue21-declarations.log（巨大ログはcommitしない）。

## 外部操作
2026-10-03 gh read-only確認: main従来型protection404、ruleset22445153 active、deletion/non_fast_forward/pull_request、bypassなし。設定は変更しない。依頼で新規作業branch push/Draft PR作成は許可済み。npm未統合branchはread-only diff確認のみ。

## full retrospective
トリガー: 新規比較test fixtureがroot indexを作成せず失敗したこと、および初回Actor語彙不適合。症状/根拠は検証履歴。原因仮説: initのみではroot indexを作らない既存契約をfixtureで見落とした。対処は明示fixtureと既存native suiteへのテスト統合。候補分類automated checks/低: fixtureに必要な索引生成を明示し、test scriptの固定対象を確認する。確認方法: required npm test/compatで新test名とpass数を確認。恒久ルール/試行を自動採用しない。既存IMP-0001との契約同期観測の近さを親へ報告し台帳集約を依頼。独立review/CIまでのゲートは継続中。
