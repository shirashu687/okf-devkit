# 変更履歴 — render

<!-- `okf log --write` が git 履歴からここに追記する。書式は /CONVENTIONS.md §7 を参照。 -->

## 2026-10-04
- **Update** 更新済み親とのGit分離統合でもrender/cleanupと文書root/projectroot境界を保持。 (`7171733`)
- **Update** Git helper分離後もrender/cleanup所有境界とroot区別を維持する記録を更新。 (`d1fd3c9`)
- **Update** Extracted pure CLI helpers with stable exception/exports and fixed root/repeated-main Git cache boundaries; updated affected implementation references. (`8981af1`)
- **Update** レンダラーAPIの隣接配置とCLIの_site既定を出力境界の説明でも区別した。 (`20ff40d`)
- **Update** Backlogを状態別リスト中心にし、任意カンバンと表示検索・検索前の開閉復元・設定済み補助情報を追加。 (`9e49dba`)

## 2026-10-03
- **Creation** 自リポジトリの実装根拠を持つ本文ドキュメントを追加。 (#4, `036d60a`)
- **Creation** feat(render): add hierarchical navigation and source metadata。 (`9162553`)
- **Creation** feat(render): show read-only backlog progress overview。 ([#21](https://github.com/shirashu687/okf-devkit/issues/21), `831bb59`)


- **Update** Windowsの旧新出力別名・曖昧パスとmanifest重複を整理前に拒否し、正規化前検査を追加。 (`8359662`)
- **Update** hash/manifestで確認した未編集旧生成物を新出力成功後に退避し、receiptと非上書き復元で故障境界を保護。 (`59a0bb5`)
- **Update** render CLI の既定出力を_siteへ変更し、--outputで従来配置を選べるようにした。check/hook/openとinitのignore案内を新既定に合わせた。 (`bde6d3e`)

- **Creation** render --open を追加。生成先のトップページを開き、check / hook 時は起動しない。 (`a731462`)


## 2026-09-10
- **Creation** feat: add Python-free Node.js CLI。 (`41f58f1`)

## 2026-09-07
- **Update** 共通ハーネスを導入し、固定配布版へ移行。 ([#2](https://github.com/shirashu687/okf-devkit/pull/2), `c14025a`)

## 2026-08-25
- **Creation** feat: OKF v0.2 バンドル運用CLIとして初期実装。 (`1faf59d`)
