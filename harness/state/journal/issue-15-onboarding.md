# Issue #15 導入簡略化

- 作業場所: /workspace/okf-devkit、開始SHA: 21829cc（完全SHAは変更宣言参照）、開始時変更なし。
- 依頼: 導入の課題をGitHub Issuesに分割し、各課題を別セッションで検討して方針をコメント後、実装してPRを作成する。MIT表記のユーザー名化も含む。
- 外部操作: shirashu687/okf-devkit に課題・方針コメントを作成し、作業ブランチをpushしてPRを作成する。依頼に含まれる。merge、リリースは含まれない。
- 作業中: 課題の粒度と既存Issueとの重複を確認中。検証とretroゲートは完了時に追記する。

- 作業ブランチ: codex/simplify-onboarding。#47〜#50を起票し、それぞれ独立セッションで方針をIssueに投稿後に変更。#15 に分割先と残る棚卸しの範囲を記録。
- `npm ci --ignore-scripts` 初回は `/home/agent/.npm` を作成できず失敗（exit 254）。`npm_config_cache=/tmp/okf-npm-cache npm ci --ignore-scripts` は成功（exit 0）。
- Node `spawnSync` は標準sandboxで EPERM を再現。network追加権限を指定した同一のプローブは成功。統合テストは同設定で実行する。
- 開始時台帳: 評価中10/10、試行中0/3、採用済みなし。試行期限・採用済み見直し対象なし。

## 判断・レビュー

- #47: README の初回経路を `main` とし、npm lockfile または確認済みSHAで再現。`main` は可変であり、今回の変更はマージされるまで含まれない。v0.1.0のDraft assetは固定された旧版で変更しない。固定SHA 12cdb44の一時導入は別セッションで成功し、今回の変更を含む配布物は下記package testで検証。
- #48: initは3製品の未作成設定・共通advisory adapterを作り、既存設定と.gitignoreはforceでも保持。既存別hookとの重複・製品側の信頼設定を説明。起動前のGit/root/adapter失敗も診断しexit 0とする（シェル自体を起動できない場合は保証外）。
- #49: デフォルトdocs/sharedのまま開始でき、別harnessを必要としない案内へ整理。既定のlog.layersが空である限界を明記し、既存のカスタム設定は維持。
- #50: LICENSEの年とMIT本文を保ち、著作権者だけユーザー名に変更。npm tarballと別環境で作ったPython wheel内のLICENSE一致を個別確認。
- 仕様軸: 開始SHAから変更・未追跡ファイルを確認し、各Issueの方針と受入条件、既存設定保護と公開状態を照合。launcher起動前の失敗境界をreviewで発見し修正、テスト追加。実イベントとWindowsは未確認。
- 標準軸: AGENTS、config、保護対象宣言、配布設定、影響文書、Python/Node整合、diff --checkと索引・lintを照合。README標準のmainは可変と明示。既存のRelease assetは触れない。

## 統合検証（開始SHA上の今回の作業ツリー、Linux）

| 項目 | 結果 | 内容・限界 |
| --- | --- | --- |
| 既存Python | 成功 | `.venv/bin/python tests/run_all.py`: 267件、失敗0、エラー0、skip 5。環境はPOSIX版既存venv。Windows指定の `.venv/Scripts/python.exe` は存在しない |
| Node | 成功 | `npm test`: 31件、成功29、skip 2。`OKF_TEST_PYTHON=$PWD/.venv/bin/python npm run test:compat`: 15件成功 |
| 配布 | 成功 | `npm run test:release` 14件、`npm run test:package` 3件。後者は最終launcher修正後に再実行 |
| OKF | 成功 | index --write / lint (error 0, warn 0) / index --check。affected --baseで影響文書を照合し、現行仕様に関係する導入・操作・Node・scaffoldを更新。歴史的なreleaseやdecisionは旧版の記録として維持 |
| 変更検査 | 成功 | 固定開始SHA、作業ツリー、task / pull-request の両scopeで宣言あり。宣言は意味上の承認を表さない |
| 実AIイベント・Windows | 未実行 | 当該実製品、Windows/PowerShell環境なし。CIの結果とは区別する |
| PR CI | 未実行 | PR作成後に別途確認する |

## retroゲート

依頼・各Issue・全差分・検証再試行・各セッションの引継ぎを照合。起動前失敗の見落としはreviewで発見し修正したためfull retro対象とし、既存IMP-0005の独立事象4に記録。実AIイベント・Windowsの証拠は未取得。次は対象製品の実イベントとCI各OSで確認する。試行や恒久ルールの採用はしていない。

- 実装コミット `7687999` の後、shared / cli / scaffold のlogへ実ハッシュ付きで変更を追記。追記後の索引生成・lint（error 0 / warn 0）・索引確認は成功。実装コードやテストを変更せず、最終の既存Python/互換テストを再実行する。
- 追記後の再検証: Python 267件（失敗0、エラー0、skip5）、Node/Python互換15件成功。Linux、変更はlog/worklogのみ。PR CIと実製品イベントは別途未確認。
