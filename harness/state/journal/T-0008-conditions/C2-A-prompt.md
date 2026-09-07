# T-0008 C2-A 実装依頼

これは新規文脈の `gpt-5.6-luna` が、次の隔離cloneだけで実施する試行です。

- 作業場所: `C:/@git_repogitories/ab0f/t0008-runs/c2-a-luna`
- 開始SHA: `1a646369621dcdf7c918c04493963784ff95a5cb`
- 製品: `okf-devkit`
- 本流へのmerge/push、親repoの変更、別試行の閲覧は禁止。
- coordinatorのT-0008評価worklog、B1の依頼・結果・会話、C1/C3の実物は読まない。

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

## A固有の接続

作業開始時に、target入口から `harness/core/policy/requirements.md`、`harness/core/guide.md`、`harness/project/config.md`、`harness/core/procedures/verify-report.md`、`handover.md`、`retrospective.md` の順で必要箇所を読み、開始SHA・working tree・既存差分を照合する。作業の正本を `harness/state/journal/T-0008-c2-a.md` に作り、保護対象の変更があれば同じ比較点の `.changes.json` を用意する。作業前後の検証・review・未確認範囲・次の一手をそのworklogに記録する。

最低限、既存venvの `.venv/Scripts/python.exe tests/run_all.py`、変更時の `harness/project/check_changes.py --base 1a646369621dcdf7c918c04493963784ff95a5cb`、コード変更時の `affected --base` を確認し、文書変更ならconfigが定めるindex/lint/checkも確認する。実行不能ならその値を記録する。

作業終了時に、実際のモデル名、clone、開始/終了SHA、変更ファイル、focused/full tests、変更検査、review所見、未実行範囲を返す。相手の結果を推測・引用しない。
