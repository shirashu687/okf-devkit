# 作業記録: PR / Issue lifecycle

状態: 進行中。開始SHA: `d539e28c51c2a562f9729a07854c0fbf236438d0`。専用ブランチ `codex/pr-issue-lifecycle`、開始時 clean。2026-10-04 08:35 UTC のユーザー依頼により、PR準備状態・Issueラベル更新をルール化する。AGENTS参照変更を事前宣言。

対象: 開発運用文書、既存triage定義の明確化、PR/Issueテンプレート。対象外: 実装・Release設定、GitHub既存labels/Issue/コメント/close、merge/publication、権限Custom Rules。

既存5状態ラベルを再利用し、従来 needs-triage の広い maintainer確認待ちから初期整理未完へ明確化する。ラベルは次の担当、Issue本文は最新進捗の正本。設計/部分PRと全Issue受入を分離し、依存base・最新SHA・独立review・CIをReady判断の根拠にする。監査結果の必要変更一覧は実行せず提案として扱う。

検証: 全Python・docs・変更宣言・独立Standards/Spec・最終SHA CI 未実行。実装を変えないためローカルNode追加検証は適用外、既存PR CIの全11ジョブは確認する。

retroゲート: 通常の要望追加として今回の変更を進める。過去PR/ラベル監査の再読を独立発生として台帳カウントしない。最終差分・検証・review照合後に判定を記録する。次の一手: 文書とテンプレートを統合して検証。

## ラベル監査に基づく変更案（未実行）

親の読み取り専用監査: open6件は全てneeds-triageだが未調査0件。現在のGitHubラベル説明は「maintainer の確認待ち」のまま。文書提案は初期整理未完へ限定し、GitHub説明更新も別途実操作の対象として提案する。

| Issue | 必要な現在状態整理案 |
| --- | --- |
| #8 | enhancement追加候補、ready-for-human。公開先所有権・担当の判断待ち。#28は公開準備のみ |
| #12 | enhancement追加候補。#27設計のみで分割未実装。次の小範囲と受入手順・着手許可を照合し、未承認ならhuman、承認済み実行ならagent |
| #15 | ready-for-human。削除対象の判断待ち |
| #16 | ready-for-human。#33で実装main済み、全受入条件照合待ち |
| #17 | ready-for-human。#31実装main済み、Refsでopen残存、受入条件照合待ち |
| #32 | ready-for-human。具体化済みだが着手合意未確認、#35は日常help本体を含まない |
| #34 | closedのためneeds-triage除去候補、enhancement保持。#35による合意範囲完了と初回Release未実行を区別 |

カテゴリは現在の不足だけ補完し無関係なラベルを保持する。これは操作案であり、既存Issue本文・コメント・ラベル・closeは変更していない。
