# 上流スキル採用プロファイル

このファイルは okf-devkit が採用した上流スキルの理由、参照関係、更新方法、検証結果を記録する。上流の SKILL.md、補助ファイル、agents/openai.yaml はインストーラー管理下に置き、ここでは内容を複製しない。導入状態とハッシュは skills-lock.json を正本とする。

## 出所と導入

- 上流: https://github.com/mattpocock/skills
- 取得 ref: main
- 取得確認 commit: 3cca18b368ae95cdbdebbff572ccafa662551015
- 上流 package metadata: 1.2.3（上記 commit の package.json）
- 導入日時: 2026-09-05
- CLI: skills 1.5.23
- 実行コマンド:

~~~
npx skills@latest add mattpocock/skills -a codex -a claude-code --copy --skill ask-matt setup-matt-pocock-skills grill-with-docs grill-me grilling domain-modeling codebase-design handoff prototype research to-spec to-tickets implement tdd code-review diagnosing-bugs improve-codebase-architecture resolving-merge-conflicts triage wayfinder wizard to-questionnaire wait-what teach writing-for-agents
~~~

配置は .agents/skills/（Codex）と .claude/skills/（Claude Code）のコピーである。上流プラグイン mattpocock-skills@claude-plugins-official は user scope に残るが、対象プロジェクトでは .claude/settings.json の false により無効化している。他プロジェクトの user 設定は変更しない。

## 採用プロファイル

初期プロファイルは SPEC §5.2 の engineering-flow とし、ask-matt の全案内先を実在するコピーで閉じるために次の25個だけを導入した。

| 区分 | スキル |
|---|---|
| 明示呼出 14 | ask-matt、setup-matt-pocock-skills、grill-with-docs、grill-me、handoff、to-spec、to-tickets、implement、improve-codebase-architecture、triage、wayfinder、to-questionnaire、wait-what、teach |
| 暗黙呼出 11 | grilling、domain-modeling、codebase-design、prototype、research、tdd、code-review、diagnosing-bugs、resolving-merge-conflicts、wizard、writing-for-agents |

ask-matt の代表ルートは次のとおりである。

- 設計: grill-with-docs → domain-modeling / codebase-design
- 実装: to-spec → to-tickets → implement → tdd → code-review
- 診断: diagnosing-bugs → 必要なら improve-codebase-architecture
- 補助: handoff、prototype、research、to-questionnaire、wizard、wait-what、teach
- 受付: triage、大きな不確実性: wayfinder

上流の agents/openai.yaml と SKILL.md の抑制指定は明示呼出14個で一致する。製品コマンド（例: /clear）や例示パスはスキル依存として数えない。in-progress 配下、名称のない候補外スキル、全件導入は採用しない。

補助ファイルは各採用ディレクトリのコピーに含まれる。ask-matt が案内する24個、各 agents/openai.yaml、補助 Markdown とスクリプトの存在を導入版で検査する。

## 更新・巻戻し・撤去

### 更新

1. git status --short で作業ツリーを確認する。
2. npx skills update を実行する。
3. skills-lock.json、採用名、in-progress 混入、両製品のコピー配置、補助ファイルを確認する。
4. ask-matt の主要ルート、明示・暗黙トリガー、.venv/Scripts/python.exe tests/run_all.py、OKF lint を再検証する。
5. 上流更新だけを一つのコミットにまとめ、問題があればそのコミットを revert する。自前文書の変更とはコミットを分ける。

更新確認では npx skills update が --copy / --agent を明示しないため、両配置を維持するかを一時作業場所で実測する。配置が崩れた場合は、採用名を限定した上記の add ... --copy --skill ... を再適用する。

### 巻戻し・撤去

- 巻戻しは、上流変更だけを含むコミットを revert し、lock、採用名、両配置、上流原文、主要検証を再確認する。
- 撤去は対象名を指定した npx skills remove <skill names> -y を一時作業場所で確認してから、導入した上流ファイルと lock エントリだけを除く。プロジェクト文書は削除しない。
- Claude プラグインの無効化を戻す場合は、.claude/settings.json にこのタスクが追加したキーだけを戻し、user scope は変更しない。

## 検証記録

検証結果は SPEC §8.1 の4値（成功 / 失敗 / 未実行 / 実行不能）だけで記録する。トリガー検査は小さな読み取り専用依頼で行い、外部投稿・commit・上流フロー全体の実装は行わない。

| 識別子 | 結果 | 対象 | 証拠 |
|---|---|---|---|
| dependency-closure | 成功 | 導入版25スキルの参照・補助ファイル | `skills-lock.json` と両製品の25ディレクトリ、必須 `SKILL.md` / `agents/openai.yaml`、ask-matt の24案内先を検査。in-progress は0件。例示パス8件は上流文書のサンプルであり依存ではない。 |
| duplicate-scan | 成功 | repo / user / plugin の実効発見元 | repo 採用名と user 側（`codex-delegate`、`find-skills`、system skills）の衝突0件。`claude plugin list --json` で user scope は有効、対象プロジェクトは `.claude/settings.json` により無効。 |
| trigger-positive | 実行不能 | Codex / Claude Code の明示・暗黙トリガー | Codex の明示14・暗黙11は成功。Claude Code のモデル実行は未ログイン（`Not logged in · Please run /login`）で実行不能。詳細は下表。 |
| trigger-negative | 実行不能 | 明示用代表の不用意な起動抑制 | Codex の非該当11件と明示スキルの自然文抑制は成功。Claude Code の同検査は未ログインで実行不能。 |
| license-provenance | 成功 | commit 固定の LICENSE と出所 | THIRD_PARTY_NOTICES.md |
| minimal-setup | 成功 | 入口から issue tracker / triage / domain docs | 一時場所で既存 `.venv` を使い `new backlog` が `docs/backlog/T-0001-test-item.md`、`new doc` が `docs/project/decisions/0001-test-decision.md` を生成。`AGENTS.md`、`docs/agents/`、`CONTEXT.md` も存在。 |
| context-load | 成功 | 両製品の採用名一覧と description | `claude plugin details` で25スキルを確認。Codex の read-only context probe で暗黙11スキルが常時文脈に入り、明示14は常時投入されず slash 呼出で選択できることを確認。 |
| update-layout | 成功 | 一時場所での update と両製品のコピー配置 | 一時場所で `npx skills update -y` が終了コード0、25件更新、Codex/Claude Code とも25コピー、ask-matt と lock を確認。 |
| project-required | 成功 | 既存テスト、OKF index / lint | 既存 `.venv\Scripts\python.exe tests\run_all.py`（144件、失敗0）、`okf ... index --check`、`okf ... lint`（error 0 / warn 0）。 |

## トリガー検査表

| 製品 | モデル | 開始版 | プロンプト | 期待選択 | 実際の選択 | 結果 | 証拠 |
|---|---|---|---|---|---|---|---|
| Codex | gpt-5.5 | codex-cli 0.153.1 | `/ask-matt このリポジトリで最初に確認すべき導入手順を教えて` | ask-matt | ask-matt | 成功 | 新規 ephemeral / read-only セッション |
| Codex | gpt-5.5 | codex-cli 0.153.1 | 明示14件（`/ask-matt`、`/setup-matt-pocock-skills`、`/grill-with-docs`、`/grill-me`、`/handoff`、`/to-spec`、`/to-tickets`、`/implement`、`/improve-codebase-architecture`、`/triage`、`/wayfinder`、`/to-questionnaire`、`/wait-what`、`/teach`）を各1回 | 各指定名 | 14件すべて指定名 | 成功 | 各応答に `SKILL_TEST` マーカーを確認 |
| Codex | gpt-5.5 | codex-cli 0.153.1 | 暗黙11件の適用質問（下表） | 各対応スキル | 11件すべて対応スキル | 成功 | 各応答に `SKILL_TEST` マーカーを確認 |
| Codex | gpt-5.5 | codex-cli 0.153.1 | 暗黙11件の非該当質問（下表） | none | 11件すべて none | 成功 | 各応答に `SKILL_TEST: none` を確認 |
| Codex | gpt-5.5 | codex-cli 0.153.1 | スキル名なしの実装依頼、および無関係な確認依頼 | `implement` は自動起動しない、無関係依頼は none | 実装依頼は `tdd`、無関係依頼は none | 成功 | 明示専用スキルの抑制を確認 |
| Claude Code | Sonnet | 2.1.201 | `/ask-matt このリポジトリで最初に確認すべき導入手順を教えて` | ask-matt | 未観測（未ログイン） | 実行不能 | `claude -p` が `Not logged in · Please run /login` で終了 |
| Claude Code | Sonnet | 2.1.201 | 暗黙の適用 / 非該当質問 | 対応スキル / none | 未観測（未ログイン） | 実行不能 | モデル起動前に同じログイン要求で終了 |

暗黙トリガーのプロンプト行列（Codex、各プロンプトは適用条件を一つに絞った自然文）:

| スキル | 適用プロンプト（要旨） | 期待 / 実際 | 非該当プロンプト（要旨） | 期待 / 実際 | 結果 |
|---|---|---|---|---|---|
| grilling | 設計案の前提を厳しく質問して見落としを洗い出したい | grilling / grilling | 結論だけ確認したい | none / none | 成功 |
| domain-modeling | この機能のドメインモデルを整理したい | domain-modeling / domain-modeling | 単純な文言修正をしたい | none / none | 成功 |
| codebase-design | 既存コードベースの設計境界を見直したい | codebase-design / codebase-design | 今日の天気を知りたい | none / none | 成功 |
| prototype | このアイデアを小さなプロトタイプで検証したい | prototype / prototype | 完成済み文書を読むだけにしたい | none / none | 成功 |
| research | この技術選定について調査して比較したい | research / research | 既知の値をそのまま転記したい | none / none | 成功 |
| tdd | この変更をテスト駆動で実装したい | tdd / tdd | 既存テストの結果だけ確認したい | none / none | 成功 |
| code-review | この変更のコードレビューをしてほしい | code-review / code-review | 新規実装はせず使い方だけ知りたい | none / none | 成功 |
| diagnosing-bugs | 再現する不具合の原因を診断したい | diagnosing-bugs / diagnosing-bugs | 新機能の名前を考えたい | none / none | 成功 |
| resolving-merge-conflicts | マージコンフリクトの解消を手伝ってほしい | resolving-merge-conflicts / resolving-merge-conflicts | コンフリクトのないファイルを読むだけにしたい | none / none | 成功 |
| wizard | 次に何をすべきか案内してほしい | wizard / wizard | 具体的な作業はなく挨拶だけしたい | none / none | 成功 |
| writing-for-agents | エージェント向けの文書を書きたい | writing-for-agents / writing-for-agents | 通常の利用者向けの短い文章だけ直したい | none / none | 成功 |

補足:

- Claude Code の plugin inventory / details は読み取り可能だったが、モデルの trigger smoke test はログイン状態が必要だった。未観測を成功扱いにはしていない。
- Codex の context probe では上流 metadata の `interface.icon_small` / `icon_large` に対する `..` パス警告が出たが、スキル選択と検査結果には影響しなかった。
