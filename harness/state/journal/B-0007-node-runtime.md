# 作業記録: B-0007 Node.js実装

## メタデータ

| 項目 | 値 |
| --- | --- |
| 状態 | 完了 |
| 作業場所 | okf-devkit |
| ブランチ | detached HEAD |
| 開始日時 / 最終更新日時 | 2026-09-10 / 2026-09-10 |
| 開始SHA / 最新HEAD | c14025aea7e7f5e5c40bbe8ee25b37e00cf5d35c |
| 作業者 / 製品 | Codex |

## 目的・範囲

Python未導入の環境で既存CLI相当の機能を使えるNode.js版を追加する。利用者がNode.jsを選択済み。
既存Python実装、共用設定・テンプレート・アセット、Node CLI、互換テスト、hook、利用説明を対象とする。
npm公開・push・製品権限変更は対象外。完了条件は依頼と docs/backlog/B-0007-non-python-runtime.md を参照。

## 開始時の状態

git status --short は変更なし。HEADを比較点として固定。Node v24.13.0 / npm 11.6.2を確認。
指定された .venv/Scripts/python.exe は存在せず、初回起動確認は実行不能。作業フォルダへ `.venv` を作り、既存依存を導入して以後のPython検証はこの実体で実行した。製品のNode実行にはPythonを使わない。

## 判断と根拠

Node実装を追加し、Pythonの起動・取得を利用時に要求しない。B-0007の旧案B非推奨は今回の明示依頼により変更する。
索引・履歴はPython版との比較で互換性を検証する。設定・テンプレート・アセットは既存ファイルを共用する。

追加内容は `node/*.mjs`、`package.json` / lock、`tests/node/*.mjs`、共有hook、Node CI、利用手順・ADR。
詳細な判断の正本は [ADR](../../../docs/project/decisions/0001-node-runtime.md)。Nodeのテストスクリプトとlockも変更宣言の保護対象へ追加した。
既存Python job・必須テスト・R1〜R5を保持し、制約の削除や条件緩和はない。検査器自身も同じ作業ツリーで変更可能であり、独立した改ざん防止の追加とは扱わない。

## 摩擦観測とretroゲート

開始時に ledger を確認。評価中4/10、試行0/3、採用0、期限が設定された試行・見直し対象なし。
依頼・B-0007・全差分・検証/再試行・二軸reviewを照合した。予期しないWindows hook失敗と、reviewで既存Python経路の回帰を検出したためfull retroを実施し、[IMP-0005](../../ledger.md#imp-0005)へ事実・仮説・候補を記録した。
試行・恒久ルールへの採用は行わず、人の採用判断待ちとして作業を止める項目はない。未確認範囲はCI全matrix・macOS・実利用先の既存カスタムhookで、必要なら該当環境で同じテストと差分確認を実行する。

## 検証

| 識別子 | 適用 | 結果 | 対象・方法 | 証拠・限界 |
| --- | --- | --- | --- | --- |
| venv-initial | はい | 実行不能 | .venv/Scripts/python.exe --version | ファイルなし |
| dependency-initial | はい | 実行不能 | npm view / .venvでのpip install | 通常権限のネットワーク制限 |
| dependency-retry | はい | 成功 | npm install --ignore-scripts、.venv/Scripts/python.exe -m pip install -e . | 自動承認された同一目的の再試行。設定・権限の恒久変更なし |
| project-required-initial | はい | 成功 | .venv/Scripts/python.exe tests/run_all.py | 保護範囲回帰テスト追加前、168件・失敗0・エラー0 |
| native-initial | はい | 失敗 | npm test | 9成功/1失敗。PS5.1文字コードによるhook構文エラー |
| native-retry | はい | 失敗 | npm test | 文字コード修正後もnpm symlink起動で出力なし。realpath判定へ修正 |
| compat-initial | はい | 失敗 | npm run test:compat | 2成功/4失敗。コンソールCRLF/LF差。ファイル比較はそのまま維持してコンソールだけ正規化 |
| native-before-final | はい | 成功 | npm test | 11件・失敗0。隠しファイルglobと日時境界を含む |
| compat-before-final | はい | 成功 | npm run test:compat | 6件・失敗0。生成日時以外のscaffold/new、索引2形式、Gitレポート、HTMLの比較 |
| python-hook-regression | はい | 成功 | node --test --test-name-pattern='existing Python install' tests/node/compatibility.test.mjs | 既存Python launcher + 壊れた開発Node候補でPowerShell hook成功/{} |
| project-required-final | はい | 成功 | .venv/Scripts/python.exe tests/run_all.py | 最終作業ツリー、169件・失敗0・エラー0・skip0、終了0 |
| node-final | はい | 成功 | npm ci --offline --ignore-scripts --cache .npm-cache → npm test → npm run test:compat | 最終作業ツリー、Node11件・比較7件、失敗0/skip0、全終了0。Node24.13.0/Windows |
| okf | はい | 成功 | Python index --write / lint / index --check / render --check | lint error0/warn0、29ページ生成可否検証、全終了0 |
| node-real-bundle | はい | 成功 | Node index --check / lint / render --check | 同じ実バンドルでerror0/warn0、29ページ、全終了0 |
| npm-package-smoke | はい | 成功 | npm pack → 別フォルダへoffline install → .bin/okf init/index/lint/render | 最終 `dist/okf-devkit-0.1.0.tgz`、49,611 bytes、26ファイル。最終版も `.npm-cache/final-smoke` へ新規インストールし全終了0・hook出力{} |
| change-declaration | はい | 成功 | check_changes.py --base c14025aea7e7f5e5c40bbe8ee25b37e00cf5d35c | 全10保護対象を宣言、終了0。宣言は人の承認とは別 |
| CI | はい | 未実行 | ローカル結果から推定しない | 外部操作なし |

## review

比較点: c14025aea7e7f5e5c40bbe8ee25b37e00cf5d35c。未追跡ファイルを含む作業ツリー全体を `code-review` の2子エージェントと主担当で確認した。

### 仕様軸

既存Pythonインストールより依存未導入の開発Node候補が先に選ばれるP2を1件検出。開発Node候補を既存Python・PATH候補より後へ移動し、実Python launcherを使う回帰を追加した。再レビューで解消、未解消0件。
主担当はglobの明示dot対応、日時検証、npmリンク経由起動も確認・修正した。全入力での完全同値性は保証せず、YAML重複キー・循環aliasの拒否、JavaScript RegExp、出力先制約の差は利用手順へ記録した。

### 標準軸

AGENTS/config/policy/docs規約とREADMEの書き込み方針を照合。仕様軸と同じhook回帰を1件検出し、修正後の再レビューで解消。未解決の標準指摘0件。
二軸の再レビューは静的確認で、追加テスト実行の証拠は主担当の検証表に分ける。上流スキル・lock・通知は変更していない。

## 残作業・妨げ・再開前提

依頼範囲の残作業・妨げなし。npm公開・commit・pushは実施していない。CIは設定を追加したが実行は未確認。
`okf affected` の影響2文書を更新し、残りの未カバー管理文書・CI・設定は今回の説明と宣言で個別確認した。
`okf log --write` は既存コミット分を3層へ追記。今回の作業は未コミットのため、作業メモを各層へ記録し、実在しないハッシュは記入していない。ハッシュ付きエントリはコミット後の同コマンドで生成する。

## 次の一手

利用する場合はREADMEのNode.js手順、または `dist/okf-devkit-0.1.0.tgz` を導入先でローカルインストールする。

## 完了要約

Node.js 22+向けの独立CLIで既存10コマンドを提供し、Python不要の起動とローカルnpm配布を確認した。
最終の既存169件・Node11件・比較7件、両ランタイムのOKF検査、配布smoke、変更宣言検査は成功。
二軸reviewの同一P2は修正・再確認済み、未解決0件。full retroはIMP-0005へ記録した。
全入力の完全一致、未実行CI/macOS、npmレジストリ公開を成功・完了と推定しない。

## push・マージへの継続（2026-09-10）

利用者がnpm公開は不要と指定し、pushからマージまでを明示依頼した。上記の当初対象外のうちcommit・push・PR作成・マージを今回の対象へ追加する。対象は既存origin `shirashu687/okf-devkit`、作業ブランチ `codex/node-runtime`、統合先 `main`。npm公開とリポジトリ設定・権限変更は行わない。

開始時はdetached HEAD `c14025aea7e7f5e5c40bbe8ee25b37e00cf5d35c`、未コミット差分は本worklogの実装一式。fetch後のorigin/mainも同じSHAで、追加の取り込みは不要。GitHub CLIの通常権限実行は設定の読み取り権限で実行不能となったが、既存認証を使う昇格再試行は成功した。認証情報は記録しない。

同日時点のgh API読み取りで従来型branch protectionは404、active rulesetは `22445153` を確認。設定変更は行わない。PR全体の保護対象10パスと理由は別scopeの `B-0007-node-runtime-pr.changes.json` に記録し、作業開始時のtask宣言は保持する。

再開時の台帳は評価中5/10、試行0/3、採用0、期限・巻戻し競合なし。実装時のreview指摘は解消済み。継続時点では追加のfull retro対象はなく、CI結果・最終差分・マージ結果を続けて確認する。

実装をcommitした後に各層の実ハッシュ付きlogを生成し、文書検証・必須テストを実施する。既存レビュー済み差分と統合記録をpushし、PRの全CI結果を確認してから通常のmerge commitで統合する。最終結果はPRと応答から参照できるようにする。
