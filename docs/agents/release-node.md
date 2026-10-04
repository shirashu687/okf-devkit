---
type: How-To
title: Node.js配布物をDraft Releaseで検査して公開する
description: 配布担当者がレビュー済みmainから固定タグを作り同じ配布物を検証して公開する。
tags: [agents, node, distribution, release, how-to]
status: draft
layer: shared
generated:
  by: codex/gpt-6
  at: 2026-10-04T13:44:39Z
code_globs:
  - .github/workflows/release.yml
  - scripts/release-*.mjs
  - scripts/package-smoke.mjs
  - package.json
  - package-lock.json
  - pyproject.toml
related:
  - /project/decisions/0002-github-node-distribution.md
  - /agents/install-okf.md
  - /project/releases/v0.1.0.md
---

# Node.js配布物をDraft Releaseで検査して公開する

配布担当者向けの手順。利用者repoへの導入・初期化・更新は [導入ガイド](/agents/install-okf.md) を使う。
この手順はmainに統合済みの配布workflowを対象とする。公開予定版は **v0.1.0のPreRelease**。2026-10-04時点では未公開で、v0.1.0タグもReleaseも存在しないことを読み取り確認している。実タグのpush、タグ用Actions、Draft生成、PreRelease公開は今回の準備では実行しない。
日本語の公開予定内容は [v0.1.0リリースノート](/project/releases/v0.1.0.md)。準備PRのレビュー・main統合・その最終SHAのCI成功を済ませ、その後のタグ作成と公開を別途承認された工程として進める。文書の作成や準備PRの成功は公開の許可にならない。

## 1. レビュー済みの版とコミットを選ぶ

配布対象はこのrepoのmainに含まれるレビュー済みコミット。完全SHAとpackage.json、package-lock.jsonのトップレベル・ルートpackage、pyproject.tomlの版を照合する。現在はいずれも0.1.0であり、準備のための版更新は不要。
タグは `v<package version>` と一致させる。workflowはrepo-source、タグが指す実コミット、対象版、origin/mainの祖先であることを検査する。
版を変更するならレビュー用PRでmanifestとlockfileを更新し、必須検証を通してからmainへ統合する。`npm version <新しい版> --no-git-tag-version` 等の版更新はそのPRの工程として扱い、配布作業中に現行0.1.0へ機械的に再適用したり、勝手に版・タグ・コミットを生成しない。

対象mainのCIと変更検査、独立レビュー、Node/共通資産の整合性を確認する。ローカル検証成功をGitHub Actions成功へ読み替えない。
Node.js 22+・npm・Gitと通常のGitHub認可を使い、private repoのアクセス権・可視性・Actions設定を変更して成立させない。新secretの設定は要求しない。

## 2. 人が指定タグだけを作成してpushする

ローカルとremoteに同名タグがないこと、同名Releaseがないことを読み取り確認する。既存タグの移動・削除・force pushはしない。
人が配布対象SHAと版を確認し、認可されたGit操作としてそのタグだけをpushする。`git push --tags` で無関係なタグを送らない。
以下は手順の形を示す未実行例で、VERSION/FULL_COMMIT_SHAを実際の承認済み値へ置き換える。

```text
git ls-remote --tags origin refs/tags/vVERSION
git tag -a vVERSION FULL_COMMIT_SHA -m "Release vVERSION"
git push origin refs/tags/vVERSION:refs/tags/vVERSION
```

workflowは `v*` タグのpushで動く。GITHUB_TOKENによる操作は後続workflowを起動しない場合があるため、CIが自動でタグを作る方式へ置き換えない。
既存タグやReleaseが見つかったら新規配布を停止し、手順5の再開・不一致処理へ進む。

## 3. Actionsの検証と同一配布物を確認する

`Verified GitHub distribution` の対象タグ/SHAを確認する。次の全段階が成功するまで公開しない。

| job | 確認する内容 |
| --- | --- |
| validate | Windows/Ubuntu、Node22/24、対応Pythonでソース同一性、Python全テスト、Node、比較、release guards、docs lint/index/render |
| bundle | 検証済み対象から一度だけnpm packし、tgz・release-manifest.json・SHA256SUMSをartifactへ保存 |
| install | bundleの同じバイト列を4環境（Windows/Ubuntu×Node22/24）で導入・動作確認。再packしない |
| draft | repo-sourceとread-sourceを再確認し、検証した同じ3assetでDraftを作成または安全に再開 |

通常jobの権限はcontents:read、最後のdraft jobだけcontents:write。workflowはnpm publishやRelease公開を行わない。
artifactは `verified-release-bundle` として30日保存される。必要な検査・再開は保存期間内に行い、同名ファイルをローカルで再packして同じ成果と扱わない。

実行されるjobはvalidateの4環境、bundle、installの4環境、draftの計10件。main/準備PRのCIとは別のタグ用runであり、初回の実行結果を対象タグと完全SHAで記録する。ローカルのrelease guardsやpackage検証成功をこの初回runの成功と扱わない。
tgz検査は必須28パスを確認する。このうち共通資産は16パス（defaults1、閲覧assets3、scaffold12）で、ほかにNodeモジュール9とpackage.json・LICENSE・READMEがある。導入検査はローカルdevDependencyと一時的な専用prefixのglobal導入を扱い、実利用者のglobal設定を変更しない。WindowsでもUbuntuのbundle jobが作った同一tgzを使い、Windowsでpackし直さない。
Release assetはNode向けnpm tgzであり、Python wheel/sdistやnpm/PyPI公開物を作る経路ではない。Python版はソース導入と既存CLIの検証対象として継続し、[導入ガイド](/agents/install-okf.md) のPython経路を参照する。

## 4. 全job終了後、Draftを人が検査して公開する

workflow全体が完了し、必要な全jobが成功したことを対象タグ/SHAで確認する。DraftのID・タグ・target_commitishが完全SHAと一致し、assetが期待する次の3個だけであることを確認する。

- `okf-devkit-<version>.tgz`
- `release-manifest.json`（repo・タグ・コミット・版・tgz名/サイズ/SHA-256）
- `SHA256SUMS`（tgzとmanifestのSHA-256）

認可された取得経路でDraftのassetを読み、manifestの対象版、tgzサイズ/hash、SHA256SUMS、Actions artifactとのバイト一致を照合する。checksumと固定SHAは対象・取得バイトの照合手段で、配布者を信頼してよい証明ではない。
private repoの認証情報はURL・文書・ログへ埋め込まない。公開範囲を拡げない。
内容を確認した人が明示的に公開を承認した後、**PreReleaseとして公開し、Latestには設定しない**。Draftは非公開の準備状態、公開済みPreReleaseは利用者が取得する試行版であり、同じ状態ではない。AIがこの手順を読んだことを公開の許可と扱わない。

公開前に、レビュー済みの日本語ノートからRelease本文を準備する。OKF frontmatterは本文へ含めず、予定状態の注記は実際の公開状況と照合する。公開対象の完全SHA・版・検証結果を確認してから、承認された操作として既存Draftだけを変更する。次は未実行の例であり、レビュー済み本文ファイルのパスを指定する。

```text
gh release edit v0.1.0 --repo shirashu687/okf-devkit --verify-tag --draft=false --prerelease --latest=false --notes-file REVIEWED_RELEASE_NOTES
```

この操作でタグ、target、assetを変更・再アップロードしない。直前にDraftのID・タグ・完全SHA・3asset・全job完了を再確認し、公開後は`draft=false`、`prerelease=true`、対象タグ・asset不変を読み取り確認して結果を記録する。承認前はこのコマンドを実行しない。

upload helperは各upload直前にDraft状態・ID・タグ・対象コミット・asset・sourceを再確認する。ただしGitHub APIには「Draftの場合だけuploadする」原子的条件がなく、同時publishとの競合を完全に防止できない。人はworkflow全jobが終了してからassetを確認し、それまではPublishしない。

## 5. 失敗・再実行・既存Release

途中で失敗したDraftは、人が失敗箇所と既存assetを確認する。可能なら同じworkflow runの失敗jobだけを再実行し、保存済みbundle artifactの同じバイト列を利用する。
helperは同名Draft・同じsourceに対し、既存assetの名前・状態・取得バイトを照合し、一致したassetを再利用して不足分だけを追加する。別のasset、重複、サイズ/hash/sourceやバイトの不一致は安全に停止する。
新しいrunがbundleを再作成した場合も、同じ版・タグだけで同一と仮定しない。既存Draftのassetと一致しなければ止め、上書きや削除で通さない。修正が必要ならレビュー済みの新版・新タグとして配布する。
保存済みartifactが失われた場合も、元配布物を再現できると主張しない。
公開済みReleaseは読み取り照合だけ。全assetとsourceが一致すれば既存成果として確認できるが、部分欠落・不一致を公開物の編集で修復しない。immutableな公開物にも同じ境界を適用する。

## 公式資料

- [GitHub Releaseの管理](https://docs.github.com/en/repositories/releasing-projects-on-github/managing-releases-in-a-repository)
- [GitHub CLIのRelease編集・Draft公開・PreRelease指定](https://cli.github.com/manual/gh_release_edit)
- [GITHUB_TOKENからのworkflow起動制約](https://docs.github.com/en/actions/how-tos/writing-workflows/choosing-when-your-workflow-runs/triggering-a-workflow#triggering-a-workflow-from-a-workflow)
