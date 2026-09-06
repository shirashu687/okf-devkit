# T-0008 B1 比較実装依頼

これは新規文脈の `gpt-5.6-luna` が、次の隔離cloneだけで実施する比較試行です。

- 作業場所: `C:/@git_repogitories/ab0f/t0008-runs/b1-luna`
- 開始SHA: `1a646369621dcdf7c918c04493963784ff95a5cb`
- 製品: `okf-devkit`
- 本流へのmerge/push、親repoの変更、別試行の閲覧は禁止。
- 他試行の依頼・結果・会話や評価worklogは読まない。

## 依頼

既存の `okf affected` に `--format text|json` を追加する通常規模の機能追加を行う。現行の既定text出力は後方互換で維持し、json指定時は内部のaffected mappingとuncovered pathsを機械可読な安定JSONとして出力する。`--base`、`--paths`、layer skip、既存の終了コードを壊さないこと。既存の `compute_affected()` の結果を使い、新しい解析源や外部依存は導入しない。

根拠はリポジトリ内の `AGENTS.md`、`docs/AGENTS.md`、`docs/CONVENTIONS.md` がコード変更後の `okf affected --base <固定点>` を標準導線としていること、現行 `compute_affected()` がmapping/uncoveredを構造化して返す一方で `cmd_affected()` がtextのみであること、同じCLIの `status` と `stale` が既に `--format json` を持つことである。

## 完了条件

1. textの既存出力を維持する。
2. jsonがmapping/uncoveredを返す。
3. no paths、`--base`、`--paths`、mappingあり/なし/uncoveredありを回帰検証する。
4. 利用者向けCLI案内を必要な範囲で更新する。
5. 固定SHAから仕様軸・標準軸のreviewを行い、必要な必須検証を実行する。
6. 失敗・未実行・実行不能・残存リスクは成功と読み替えず、実際のモデルと実行コマンドを報告する。

## 実行条件

リポジトリの既存入口・制約・設定とコード/テストを読み、必要な作業経路を自分で定める。プロジェクトが要求する検証・保護対象の申告・文書の整合性を省略しない。coordinatorは作業手順、route table、worklog/retroの案内やテンプレートを提供しない。別試行の結果や会話を参照せず、必要な記録と検証はリポジトリの現行指示から判断する。

作業終了時に、実際のモデル名、clone、開始/終了SHA、変更ファイル、focused/full tests、変更検査、review所見、未実行範囲を返す。相手の結果を推測・引用しない。
