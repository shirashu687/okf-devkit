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

## 採用スキル索引

- **明示**: 通常は利用者がスキル名を指定して呼ぶ14個。自然文だけからの自動選択は抑制される。選択済み手順からの呼出指定とは別の区分であり、利用者しか呼べないという意味ではない。
- **自動対象**: 依頼がdescriptionの条件に合えばエージェントが選択できる11個。常時実行や、どの製品でも必ず起動する保証ではない。明示指定もできる。
- **内部**: 選択した上流手順が別スキルを呼ぶ指定。**条件付き内部**は記載条件を満たしたときの呼出。
- **案内**: 状況に応じて次に選ぶ候補。自動的な連続実行を意味しない。「なし」は固定の次スキル指定がない意味。

原文リンクはCodex側の導入コピーを指す。Claude Code側には同内容の `.claude/skills/` コピーがある。起動検証の製品差はskill-profile.mdの検証記録を参照する。

| 名前（原文） | 起動 | 用途 | 対象外・使わない時 | 内部呼出 / 次の案内 |
| --- | --- | --- | --- | --- |
| [ask-matt](../../.agents/skills/ask-matt/SKILL.md) | 明示 | 状況に合うスキルと流れを選ぶ | 使う手順が既に明確 | 案内: 本節の各スキルを条件別に選ぶ |
| [setup-matt-pocock-skills](../../.agents/skills/setup-matt-pocock-skills/SKILL.md) | 明示 | 課題管理・triage・ドメイン文書の初期設定 | 設定済みの通常作業ごとの再実行 | 案内: 設定確認後に選んだengineering flow |
| [grill-with-docs](../../.agents/skills/grill-with-docs/SKILL.md) | 明示 | リポジトリ内の計画・設計を詰め、用語と判断を記録 | 合意済み事項だけの実装 | 内部: grilling、domain-modeling。案内: 必要ならprototype / research、複数セッションならto-spec |
| [grill-me](../../.agents/skills/grill-me/SKILL.md) | 明示 | 文書保存を伴わない計画・設計の問答 | リポジトリで判断を残す作業はgrill-with-docs | 内部: grilling |
| [grilling](../../.agents/skills/grilling/SKILL.md) | 自動対象 | 設計の分岐を質問で確定する問答の基本手順 | 事実の調査だけ、既決事項の再確認だけ | 固定の次スキルなし。呼出元へ判断を返す |
| [domain-modeling](../../.agents/skills/domain-modeling/SKILL.md) | 自動対象 | 用語・概念の曖昧さを解き、用語集やADRを更新 | 用語集を読むだけ、実装メモの置場づくり | 固定の次スキルなし。文書配置はconfig.md |
| [codebase-design](../../.agents/skills/codebase-design/SKILL.md) | 自動対象 | module・interface・seamの設計とテスト可能性を考える | 設計の形に判断がない局所修正 | 案内: 候補探索はimprove-codebase-architecture、振る舞い実装はtdd |
| [handoff](../../.agents/skills/handoff/SKILL.md) | 明示 | 会話を別エージェントへ渡す一時文書にまとめる | 同じ文脈でそのまま続行できる時 | 次の作業に合わせたsuggested skillsを文書へ記す |
| [prototype](../../.agents/skills/prototype/SKILL.md) | 自動対象 | 一つの状態・ロジック・UIの設計疑問を動かして確かめる | 本番実装、会話や資料で解ける疑問 | 案内: 判断を元の設計・実装課題へ戻す。環境をまたぐ場合はhandoff |
| [research](../../.agents/skills/research/SKILL.md) | 自動対象 | 一次資料の調査をバックグラウンドエージェントへ任せ、出典付き文書にする | 既知情報の転記だけ | 案内: 調査結果をgrill-with-docsなどの判断材料へ |
| [to-spec](../../.agents/skills/to-spec/SKILL.md) | 明示 | 話し合い済みの内容を仕様へまとめる | 未整理の論点を新規インタビューする時 | 案内: 分割が必要ならto-tickets。検査境界の確認は原文に従う |
| [to-tickets](../../.agents/skills/to-tickets/SKILL.md) | 明示 | 仕様を検証可能な縦の作業単位と依存関係へ分割 | 小作業に不要なチケットを増やす時 | 案内: 分割の合意後、依存解消済みチケットをimplement |
| [implement](../../.agents/skills/implement/SKILL.md) | 明示 | 仕様・チケットに沿って実装する | 調査・設計の合意だけが目的 | 条件付き内部: 可能な合意済み境界でtdd。内部: 完了時code-review |
| [tdd](../../.agents/skills/tdd/SKILL.md) | 自動対象 | 合意した公開境界で一件ずつred → greenにする | 実装詳細の固定、実装と同じ計算をするテスト | 条件付き内部: moduleの深さ・seamの位置・interfaceの形を検討するならcodebase-design。案内: review段階でcode-review |
| [code-review](../../.agents/skills/code-review/SKILL.md) | 自動対象 | 固定比較点から標準適合と仕様適合を別エージェントで確認 | 比較対象のない説明依頼 | 固定の次スキルなし。各軸の指摘を返す |
| [diagnosing-bugs](../../.agents/skills/diagnosing-bugs/SKILL.md) | 自動対象 | 症状を検出する実行ループを作り、不具合・性能退行を診断する | 不具合のない新機能設計 | 案内: 再発を検査する境界がないならimprove-codebase-architecture |
| [improve-codebase-architecture](../../.agents/skills/improve-codebase-architecture/SKILL.md) | 明示 | 改善候補を調査し、HTMLで示して選んだ案を詰める | 根拠のない一般化、即時の機能実装 | 内部: codebase-design。候補選択後grilling。条件付き内部: 用語・判断更新でdomain-modeling |
| [resolving-merge-conflicts](../../.agents/skills/resolving-merge-conflicts/SKILL.md) | 自動対象 | 進行中のmerge / rebase競合を双方の意図から解消する | 競合が起きていない通常編集 | 固定の次スキルなし。検証後の操作はローカル権限に従う |
| [triage](../../.agents/skills/triage/SKILL.md) | 明示 | 未整理依頼を検証・分類し、実装可能な課題へ整える | 自分で作成済みの実装可能なチケット | 条件付き内部: 詳細化が必要ならgrilling、domain-modeling。案内: ready-for-agent後implement |
| [wayfinder](../../.agents/skills/wayfinder/SKILL.md) | 明示 | 一回で扱えない大きな不確実性を判断チケットの地図にする | 道筋が明確な機能、既定での成果物実装 | 内部: 地図作成時にgrilling、domain-modeling。条件付き内部: research / prototypeチケットでは各同名スキル、grillingチケットではgrillingとdomain-modeling。作業時はNotesの指定も読む。案内: 道筋確定後to-spec |
| [wizard](../../.agents/skills/wizard/SKILL.md) | 自動対象 | 人しか行えない設定・移行操作を対話式bash手順にする | エージェント自身が実行できる操作 | 固定の次スキルなし。人の操作結果を元の作業へ戻す |
| [to-questionnaire](../../.agents/skills/to-questionnaire/SKILL.md) | 明示 | 別の人が持つ知識を得る質問票を作る | 手元の調査で分かる事実、利用者自身への設計問答 | 案内: 回答をgrill-with-docs / to-specへ |
| [wait-what](../../.agents/skills/wait-what/SKILL.md) | 明示 | 直前の説明を背景と共有語彙を添えて説明し直す | 継続的な学習計画、実装作業 | 固定の次スキルなし。元の会話へ戻る |
| [teach](../../.agents/skills/teach/SKILL.md) | 明示 | 学習目的と記録を保ち、複数セッションで概念を学ぶ | 一回の短い言い換え | 固定の次スキルなし。学習用成果物の配置は開始時に確認 |
| [writing-for-agents](../../.agents/skills/writing-for-agents/SKILL.md) | 自動対象 | エージェント向け文書・スキル・入口の構成と参照条件を整える | 通常の利用者向け文章だけの推敲 | 固定の次スキルなし。スキルを書く場合は原文の補助資料も読む |
