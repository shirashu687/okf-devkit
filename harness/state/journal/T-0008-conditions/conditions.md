# T-0008 C2 / B1 条件固定記録

- 固定日: 2026-09-06 Asia/Tokyo
- 製品: `okf-devkit`
- 共通開始SHA: `1a646369621dcdf7c918c04493963784ff95a5cb`
- A clone: `C:/@git_repogitories/ab0f/t0008-runs/c2-a-luna`
- B clone: `C:/@git_repogitories/ab0f/t0008-runs/b1-luna`
- 実装モデル: `gpt-5.6-luna`（A/Bとも同じ指定）
- 確認モデル: `gpt-5.6-sol`（実装前条件確認と実装後reviewに別taskで使用）

依頼本文の製品要件・開始SHA・完了条件・対象外・検証期待はA/Bで同一にした。Aだけが、target入口から必要な手順を読む順と、task worklog/変更宣言/retroの記録接続を明示する。Bからはその接続文・route table・手順テンプレートを除き、リポジトリ現物から自分で経路を決める。ただしBにも、製品の現行入口・保護対象申告・必須検証を省略しないという同じ完了契約を残した。

実装前の独立確認では、両cloneのHEAD、branch、working tree、対象コード・テスト・READMEの同一性、A/B依頼の差分を確認し、差分が上記の接続切断だけであることを判定する。実装担当には相手側のファイル・結果・会話を渡さない。
