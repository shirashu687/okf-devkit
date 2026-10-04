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
