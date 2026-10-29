# Issue #47 README整理

- 作業場所: /workspace/okf-issue47。開始SHA 21829cc40e7ed3300ed9ca282b391125424a49bf、開始時の変更なし。PR #51を独立PRへ分割する依頼に基づきREADMEを切り出す。
- Issue #47に独立セッションの方針を記録済み。READMEの導入例はmainを使い、lockfileと固定SHAの重要性、既存Draft配布物との違いを明記。#48/#49未採用でも正しい記述とする。
- 対象repoに作業ブランチをpushしPRを作成する操作はユーザー依頼に含まれる。コミット・push・PR以外の公開、mergeは行わない。
- 既存Pythonテストと手順の実測を確認し、結果は検証後に追記する。
- 検証: Linux既存venvでPython 261件、失敗0・エラー0・skip4。空の一時Git/npm repoでREADMEのmain指定によるinstall→init→index→lint（error0/warn0）→render --check成功。git diff --check成功。実製品の終了イベントは未確認。
- review: 開始SHAからREADMEとworklogを照合。#48未採用時も成立するようhookの生成登録を断定せず、#49の既定log無効を明記。retroは独立分割自体でトリガーなし、元の検証時の観測は元PRの記録を参照。

## npm scriptの導線

- 利用者の追加要望により、#53/#54を含むmain `2d9e5f8c6497f3655f4aa5cfd9f038c7ec0bae1f` を取り込み、導入先に `npm pkg set "scripts.okf=okf"` を1回登録した後 `npm run okf --` で使う手順へ変更。npmインストールは導入先のscriptsを自動登録しない。既存同名スクリプトの上書きとPATH上の別版へのフォールバックに注意を付けた。
- Linuxの一時Git/npm repoでREADMEのmain取得、script設定、help、init、index write/check、lint、render --checkが成功。PATHに失敗する同名コマンドを先置きした環境でも導入済みのローカル版が優先された。PowerShellの実行は未確認。
- 既存venvでPython 267件（失敗0・エラー0・skip5）、diff checkと新baseからのPR変更検査を行う。PR #52 の更新に伴うpushは利用者の依頼範囲。
