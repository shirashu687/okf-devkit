# 変更履歴 — scaffold

<!-- `okf log --write` が git 履歴からここに追記する。書式は /CONVENTIONS.md §7 を参照。 -->

## 2026-10-04
- **Update** 更新済み親の目的別AI案内を保持し、Git helper分離とinit/scaffoldの生成契約を統合。 (`7171733`)
- **Update** Git helper分離後もinit/scaffold生成入口を維持する記録を更新。 (`d1fd3c9`)
- **Update** mainのAI操作案内・helpとCLI共通helper分離を統合し、双方の仕様・テスト・生成案内・変更履歴を保持した。 (`b0d938c`)
- **Update** 生成するAI向け入口を目的別の短い案内へ整理し、未カバー文書とsync/logの診断、既存ファイル保持を明記した。 (`33b2311`)
- **Update** Extracted pure CLI helpers with stable exception/exports and fixed root/repeated-main Git cache boundaries; updated affected implementation references. (`8981af1`)

## 2026-10-03
- **Creation** 自リポジトリの実装根拠を持つ本文ドキュメントを追加。 (#4, `036d60a`)
- **Update** AI向けに旧HTML整理の計画確認・未知生成物保持・退避復元とignore設定を案内。 (`59a0bb5`)
- **Update** render CLI の既定出力を_siteへ変更し、--outputで従来配置を選べるようにした。check/hook/openとinitのignore案内を新既定に合わせた。 (`bde6d3e`)

- **Creation** new doc に根拠コードの --code-globs 指定を追加し、必須型の生成に要求。relatedを空で生成し、H1直後の空行を保持。 (`be22026`)

- **Update** fix: align init shared log with configured path。 ([#6](https://github.com/shirashu687/okf-devkit/issues/6), `4c951ec`)

## 2026-09-10
- **Update** Merge pull request #3 from shirashu687/codex/node-runtime。 (`2139a79`)
- **Creation** feat: add Python-free Node.js CLI。 (`41f58f1`)

## 2026-09-07
- **Update** 共通ハーネスを導入し、固定配布版へ移行。 ([#2](https://github.com/shirashu687/okf-devkit/pull/2), `c14025a`)

## 2026-08-25
- **Creation** feat: OKF v0.2 バンドル運用CLIとして初期実装。 (`1faf59d`)
