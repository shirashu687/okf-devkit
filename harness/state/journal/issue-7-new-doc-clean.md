# Issue #7 new doc lint-clean generation

- 開始SHA: 9d72e0e5798883d81789582d8879f139865d37b5、task/issue7、branch codex/issue7-new-doc-clean、開始clean。
- 目的: Issue本文A案を採用し両実装で--code-globs複数指定、4必須型の未指定拒否、related[]、H1空行維持。
- 対象外: lintのプレースホルダ検査緩和、既存Markdownの自動書換え、公開・merge・削除。
- 互換性: Project Overview/Architecture/Reference/How-Toのみ新引数必須。Decision Record/Glossary等任意型とnew backlogの省略維持。既存スクリプトの移行をREADME/生成AGENTSで案内。CLI helpも更新。
- npm未統合差分: cli.pyのinit変更とnewは非重複、scaffold AGENTSテンプレートの既存npmコマンド選択変更とは局所競合する可能性があるが同ブランチ未変更。mainから新規PRとして提出し統合時に保持する。
- 設計: set_fm_field/setFieldはblock list子行も置換し、欠落するtop-level fieldはfrontmatterへ追加。backlogはrelated/code_globsを書換えない。H1置換の空白はspace/tabに限定し、Pythonはlambda置換でタイトルのbackslashをそのまま保持。
- 影響文書: affected出力のNode導入手順、Node ADR更新。docs AGENTSと配布テンプレートの新規doc生成コマンド、READMEの移行案内更新。
- 保護変更: tests/test_new.py、tests/node/native.test.mjs、tests/node/compatibility.test.mjs。既存安全性テストを維持し、必須引数を既存生成プローブへ追加、CLI/生成物境界の回帰検証を追加。
- 開始retro: main台帳の評価中/試行中上限、期限、採用済みを確認。実行対象の試行/採用済みなし。
- 検証・二軸独立レビュー: 実行中。
