# Issue #12 モジュール分割事前調査

- 状態: 設計調査中、分割実装未着手。
- 独立worktree issue12-design / codex/issue12-module-design。
- 開始SHA: 9d72e0e5798883d81789582d8879f139865d37b5、開始時変更なし。
- 目的: Issue12の可変root・YAML monkeypatch・キャッシュ・再exportを保つ段階案を作り、並行コマンドPRとnpm未統合差分を壊さない。
- 技術判断: 純粋helpers→YAML→Doc/Bundle→Git→commandsの順。rootを明示引数で渡し移行中cliの可変状態adapterを保持。大規模分割は先行PR統合後。
- 証拠: cli.py2922行、ASTroot Name27参照、tests49属性。helpersとtest_yamlの直接代入を現物確認。npm差分は読取のみ。
- 対象外: runtime実装、200行条件達成、配布変更、merge/publish。
- 検証: 未実行（Python全件・OKF・独立review）、CIはDraftPR後確認。
- retro開始: ledger評価5/試行0/採用0、期限付き試行なし。通常の調査と並行分担。最終差分・検証・review照合後判定。
- 次: 調査文書の独立仕様/標準reviewと必須検証を済ませ、部分成果としてDraftPRを作る。Issue12をcloseしない。
