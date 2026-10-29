# AIへの導入依頼をREADMEから渡せるようにする

## 目的・比較点・操作範囲

- 利用者の依頼: README等の案内をAIへ渡して導入からセットアップまで依頼できるようにし、その変更のPRを作成する。
- 作業者: codex/gpt-6。元の作業場所は `/workspace/okf-devkit`、開始SHAは `2d9e5f8c6497f3655f4aa5cfd9f038c7ec0bae1f`。開始時の利用者変更はなし。
- PR作成時に最新main `db2fe13970213f29653f2a061e0c0624077a2add` を確認。README整理と実装移動を保持し、今回の文書差分だけを同版へ統合した。
- ローカルGit通信はproxy接続に失敗したため、GitHub連携で最新mainのtree・blob・commitを取得し、各SHAを照合した `/tmp/okf-agent-setup-pr` で検証する。元の作業ツリーは保持する。
- 利用者のPR作成依頼に基づき、`shirashu687/okf-devkit` の `codex/agent-install-setup-guide` に今回の文書変更を公開し、main向けPRを作成する。

## 変更と完了条件

READMEに外部ガイドURL付きの依頼文を置き、導入ガイドへ初期配置・AI向け入口の接続・検証の手順と完了条件を追加する。既存の利用者編集、パッケージ管理、実CLIの由来を確認する規約を保持する。agentsの索引はCLIで生成する。

## 検証

初回の作業版では既存venvのPythonテスト267件中262件成功・5件skip、失敗0・error0。index生成、lint error0/warn0、index確認、render確認、変更検査、diff検査も成功した。
最新mainへ統合した版の結果は以下へ記録する。既存venvを使用し、文書CLIにはこの作業場所のsrcをPYTHONPATHで指定する。

| 結果 | 対象・コマンド | 証拠・限界 |
| --- | --- | --- |
| 成功 | 最新mainへ今回の3文書差分を統合した版で `.venv/bin/python tests/run_all.py` | 273件中268件成功・5件skip、失敗0・error0、exit0。証拠は `/tmp/okf-agent-setup-pr-python-tests.log` |
| 成功 | `index --write`、`lint`、`index --check`、`render --check` | 索引は最新、lint error0/warn0、HTML検証35ページ・書込0・削除0・warn0、すべてexit0 |
| 成功 | 最新main SHAをbaseとしたtask/PR両scopeの変更検査、`git diff --check` | 保護対象・上流対象の変更なし、検査exit0。最終公開前に記録を含む4ファイルを再照合する |
| 未実行 | このPRのCI、別AIによるconsumer導入、実AI終了イベント | ローカル結果から成功を推定しない。CIはPR作成後に確認できる |

今回の変更は文書のみで、実装・依存・共有資産・hookの条件付きNodeテストは適用外。以前の267件の結果を、最新mainの273件の結果と混同しない。

## レビュー

- 仕様軸: 初回導入先にガイドを事前配置する必要がなく、依頼文が初期化とAI向け入口整備まで明示している。セットアップ済みrepoでは既存編集を保持し、固定版と実CLIの検証を要求する。
- 標準軸: docsのfrontmatter・関連リンク・生成索引を照合し、最新mainのREADME簡素化・src/nodeへの移動を保持する。実装・テスト・CI・保護対象・上流管理ファイルの変更は含めない。
- レビュー担当は同一エージェント。独立レビューや実際の別AIによるconsumer導入の成功は主張しない。

## retroゲート・残る確認

最新台帳は評価中10件・試行0件・採用0件で、期限付き試行・採用見直しの対象はない。依頼・既存変更・差分・検証・レビューを照合する。外部通信の代替手段とmainへの統合は本作業の記録として保持し、恒久ルールや改善効果の採用は行わない。
PRのCI、実AIイベント、公開URLからの新ガイド取得はローカル検証と区別する。
最終の仕様軸・標準軸レビューに未解消の指摘はない。通信エラーは利用可能な連携への切替で解消し、最新mainへの統合と再検証も完了した。要件取りこぼし・回帰・誤成功・反復手戻りのトリガーはなく、full retrospectiveと台帳更新は不要。次は同じ4ファイルのtree照合後にブランチとPRを作成する。
