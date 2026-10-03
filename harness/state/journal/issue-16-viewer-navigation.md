# 作業記録: Issue16 HTML viewer navigation

## メタデータ
状態: 進行中。開始SHA 7186566009452616d29938cc70435ab15f010698。branch codex/issue16-viewer-navigation、独立issue16 worktree。開始変更なし。PR依存: #26 (Issue21)、PR base codex/issue21-backlog-progress。mainへは#26を先に統合する前提、merge操作は本作業外。

## 目的・判断
Issue16の階層サイドナビ・source filename/path・デザイン調整。既存色/テーマを維持し余白/補助文字とactive位置を改善。ディレクトリごとのnative details/summary、現在ancestorを展開、layers/layer_dirsから順序・表示を生成。全項目にfilename補助表示し元Markdownリンクを本文冒頭へ追加。copy機能は任意案のため追加しない。目次出現閾値は変更しない。

## 規約と依存
Issue21で読んだAGENTS/harness requirements/config/docs規約/implement/code-review skillを適用。npm差分rendererなし。Python/Node両方と共有assetsを同時変更。テスト保護対象はtask/pull-request scopeで開始SHAを宣言。既存Issue21宣言は過去scope/baseとしてそのまま保持。

## 開始retro
ledger評価6/10、試行0、採用0、期限付き試行なし。IMP0012は#21既処理として重複観測しない。

## 検証・review
実装commit9162553のローカル検証と独立review結果は以下を参照。最終SHA CIのみPR作成後に確認。

## 次の一手
階層navとsourceメタ情報を実装してdeep/current/config/searchの回帰確認。

## 検証履歴
- 成功: npm ci exit0。Python全件初回172件/pass172/fail0/error0/skip0。
- 失敗: 初回native13件の追加source assertionが未エンコードhrefを期待して失敗。検証中にsource URIエンコードを追加したため、開始版と完了版が混在した実行。成功へ読み替えず最終固定実装で全件を再実行。
- 成功: 最終Python172件/fail0/error0/skip0。最終npm test14件/pass14/fail0、compat9件/pass9/fail0。既存指定venv、worktree PYTHONPATH使用。
- 成功: shared JSをvmのDOM境界で実行し、検索結果の祖先展開/非該当hidden/0件section hidden/検索解除current祖先復帰を確認。
- 成功: affected開始SHA。node-runtime/ADR/backlog-progress本文更新、新規navigation文書追加、generated.at実UTCに更新。
- 成功: index --write、lint error0/warn0、index --check、task/pull-request scope変更検査（tests3paths exact）。CI/検査/制約は変更なし。
- 成功: Chrome headless1280x1000深いactive頁、層名/dir名/current強調/filename/source metadata/余白・ガイドを目視確認。workspace親issue16-preview.png。
- 未実行: 最終SHA CI（PR作成後確認）。

## 独立review
仕様軸 investigate: base7186566から全差分＋未追跡、Issue16に対して指摘0。階層/current/path/settings/双方実装の対応確認。任意copy/TOC閾値は今回対象外。
標準軸 docs_ci: blocking0、code smells指摘0。generated.at更新P2を実UTCへ修正。共有JS追加挙動はDOM境界回帰テストを追加して検証。完成worklogとhash付logは次commitで追加。

## full retrospective
観測: 初回native verification実行中のsourceリンクURIエンコード追記によりtest開始版の期待値と実装完了版が混在し失敗。原因仮説はmutable worktreeで編集中の全件検証を開始したこと。改善候補coding standards/review、低、検証対象を編集完了後に固定する。確認方法は後続対象変更がある場合final full suite再実行。今回は最終Python/Node/compatで解消し回帰/成功誤報なし。恒久規約は変更せず親から割当されたIMP-0013を観測として記録。評価7/10、試行0/3、採用0。

## 完了前の記録
- 変更履歴: log --write --range7186566..HEADでcli/render層へ9162553を追記、他層への変更なし。
- ローカルcode target9162553、最終full結果Python172/Node14/compat9成功。独立二軸blocking0、timestampP2修正とJS検索追加検証を再報告。
- 保護変更はtests3pathsのみ、task/PRそれぞれのbase7186566009452616d29938cc70435ab15f010698を維持。最終HEADでも変更検査を再確認。
- merge順は#26→本PR、PR baseはcodex/issue21-backlog-progress。#26をmain統合後のbase変更時はpull-request scope宣言を新base/全PR差分へ更新しCI再確認が必要。merge自体は行わない。

## PR conflict adjustment 2026-10-03

- Start: 666e9d729804ebcfec6dc77d85043aa6f2b509d9. Merge adjusted parent 066acc2f9b2e9554e4841edc691d76435a9e51e8 without rewriting history. Preserve hierarchical navigation, backlog progress and shared-log descriptions/tests, plus ledger IMP-0008 / IMP-0012 / IMP-0013. Historical task declaration preserved; PR base remains backlog parent and its declaration tracks the new exact SHA.
- Local verification: Python 173 passed; Node native 15 passed; compatibility 9 passed with worktree src in PYTHONPATH; index --write / lint (error 0, warn 0) / index --check and PR-scope change check passed. git diff --check and conflict-marker scan clean. Independent review / final-SHA CI remain parent-owned and unverified here.
- Retro: existing observations retained; no new policy adopted. No unrelated npm branch, global hook, release, merge or Issue-close operation.

### Concurrent main update and image evidence

- Merge updated backlog parent including main a16842f02e71a26849f5c094a32653c23af22640. Preserve new-doc/backlog/navigation tests and both documentation entries; screenshots and renderer/assets unchanged. Parent final 30dcce718216d8822e9e0e385ba8a2f7cf1c2365 contains subsequent worklog-only corrections; declaration follows that SHA.
- Fixed implementation 910ed29254d57cb0603683e2718a9498105019f1: Python 176 / Node native 16 / compatibility 9 passed; lint error0/warn0, index --check, diffcheck passed. PR check first observed newer parent and rejected stale declaration; updated base and reran successfully separately. Image-only previous checks interrupted, not successful. Node/compat required by adopted runtime changes, performed above.

### Render-open main integration (remaining conflict followup)

- Start ebb3f9c7375d20b68241ea3824d0baad1977ca36, merge adjusted parent including exact main 5ce845a4deb454919fdec92d5cdff2105dcbc7df. ADR, ledger and native conflicts keep both navigation/search and browser-open entries/tests. Implementation merge b8c507b; final parent 3e177b2ab5fc556238315c37a1507704054d2aa3 adds only verification worklog. Historical task declarations and screenshots preserved, PR declaration base updated.
- npm ci / Python 179 / Node native 18 / compatibility 9 succeeded; index --write / lint error0 warn0 / index --check / diffcheck succeeded. Marker/evidence diff and exact-parent PR changecheck verified separately. Parent owns independent review, push and remote final-head CI; none claimed here.
