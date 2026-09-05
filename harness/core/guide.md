# 日本語作業ガイド

依頼に合う手順を選ぶための案内。選んだスキルのリンク先で英語原文と必要な補助資料を読む。全スキルをまとめて読み込む必要はない。

着手前に [config.md](../project/config.md) で実際の配置・コマンド・上流との読み替えを、[requirements.md](policy/requirements.md) で守る制約・確認方法・強制の限界を確認する。採用名と更新方法は [skill-profile.md](../project/skill-profile.md) を参照する。通常・大の作業、または中断して引き継ぐ作業では、[作業記録テンプレート](templates/worklog.md)を使う。

## 作業の重さを選ぶ

| 区分 | 判断の目安 | 流れ |
| --- | --- | --- |
| 小 | 目的・変更箇所・期待結果が明確で、影響が局所的 | 適切な実装スキルまたは直接実装 → 必須検証 → 短い報告 |
| 通常 | 複数の判断、振る舞い変更、通常の不具合修正・機能追加 | 判断が残る場合に grill-with-docs → 実装 / TDD → review → 必須検証・報告 → retroゲート |
| 大 | 複数セッション、複数チケット、設計上の不確実性が高い | grilling → 必要なら prototype / research → to-spec → to-tickets → チケット単位の実装・review → 統合検証 → retroゲート |

通常作業の計画は作業記録の目的・対象外・完了条件で足りる。調査で判明する事実は調べ、既決事項を再質問せず、残った判断だけを質問する。TDDは振る舞いを固定できる境界で使う。通常・大・高リスクの変更は比較点を固定し、仕様とリポジトリ標準を分けてreviewする。

検証・報告・引継ぎの共通手順は設置済みだが、retroの詳細手順は未設置である。検証コマンドと制約は上記2文書を正本とし、retroが未設置であることを完了報告で区別する。

## 検証・報告・引継ぎ

区分を選んだ後、適用する検証を [検証・完了報告手順](procedures/verify-report.md) で選び、結果を4値で記録する。プロジェクト固有のコマンド、実行場所、前提条件は [config.md](../project/config.md) を参照し、共通手順へ埋め込まない。

通常・大・高リスクの変更では、着手時に固定した比較点から仕様軸と標準軸を分けてreviewする。コミット済み差分だけを扱う上流reviewを使う場合も、未コミット・未追跡の対象変更を同じ比較点から補完する。

作業を中断する場合は、規模にかかわらず同じ [worklog](templates/worklog.md) に最新の検証、妨げ、前提、具体的な次の一手を残す。[引継ぎ・再開手順](procedures/handover.md) は別セッションや別担当へ渡すときに読む。小作業は中断しない限りworklogを省略できるが、必須検証と短い報告は省略しない。

retroの実行条件は仕様で定めるが、自前の詳細手順はまだ設置していない。トリガーがある場合は、未設置であることと必要な次の一手を報告する。

## 用途から選ぶ

以下は条件に応じて選ぶルートであり、列挙順の一括実行指示ではない。名前に対応する原文リンクと起動区分は次節にある。

| 状況 | 入口と次の候補 |
| --- | --- |
| どのスキルが合うか迷う | ask-matt |
| リポジトリ内で設計を詰める | grill-with-docs。実行して確かめる疑問は prototype、一次資料で確かめる疑問は research |
| 仕様・分割・実装を進める | 複数セッションなら to-spec → to-tickets → 各チケットで implement。単一セッションなら implement。小作業は直接実装も選べる |
| 不具合・性能退行の原因が分からない | diagnosing-bugs。検証する境界が不足するなら improve-codebase-architecture を検討 |
| 大きすぎて道筋が見えない | wayfinder で判断を整理。見通しがついたら to-spec → to-tickets。範囲が明確な機能には使わない |
| 未整理の外部依頼を受けた | triage。to-ticketsで作成済みの実装可能なチケットを再triageしない |
| アーキテクチャを改善する | improve-codebase-architecture で候補を選び、codebase-designで形を詰める |
| 別の環境・ディレクトリ・人へ引き継ぐ | handoff。単に同じ作業を続けるための必須ステップではない |
| 他者だけが知る情報が必要 | to-questionnaire。人しか実行できない操作が必要なら wizard |
| 説明が分からない / 継続して学びたい | 直前の説明は wait-what、複数回の学習は teach |

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

## ローカル運用と更新

上流の例示パスや課題管理先はconfig.mdの役割対応で読み替える。commit・push・外部送信などを含む手順は、requirements.mdと利用者の依頼範囲で実行する。スキルを選んだだけで実行権限が増えるわけではない。

上流の名前・description・呼出関係が変わったときは、skill-profile.mdの更新確認と併せてこの案内を見直す。英語原文はインストーラー管理下に保ち、日本語説明だけをここで更新する。
