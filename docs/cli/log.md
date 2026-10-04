# 変更履歴 — cli

<!-- `okf log --write` が git 履歴からここに追記する。書式は /CONVENTIONS.md §7 を参照。 -->

## 2026-10-04
- **Update** 本体の npm 公開を抑止し、指定版導入と実 tgz 検証・同一配布物の PR CI を追加。CLI 実装と既存テストは保持（Issue #34、`a043c6c2`）。
- **Update** CLI分割設計のmain本文・docs CIとadvisory終了hookの所有境界を補足した。 (`e5ec5a0`)
- **Update** CLI分割設計に、mainの状態別Backlog表示とcleanupの所有境界を補足した。 (`8c5085e`)
- **Update** repo終了hookの実shell起動、入力非実行、実HTML連続生成と不正設定のstrict/advisory終了値を検証する5テストを追加した（Issue #9、`4f2663a`）。
- **Update** Backlogを状態別リスト中心にし、任意カンバンと表示検索・検索前の開閉復元・設定済み補助情報を追加。 (`9e49dba`)

## 2026-10-03
- **Update** CLI分割設計の初回調査SHAを明示し、mainの出力整理module・安全条件・cleanup検証との接続を補足した。 (`b6baac0`)
- **Update** CLI分割の可変状態・互換interfaceと段階的移行を調査した。 ([Issue #12](https://github.com/shirashu687/okf-devkit/issues/12), `2c6eeea`)
- **Update** new doc の4必須型、複数の --code-globs、生成後の本文補完と index → lint の手順を現行仕様へ合わせた。 (`189eae4`)
- **Creation** 自リポジトリの実装根拠を持つ本文ドキュメントを追加。 (#4, `036d60a`)
- **Creation** feat(render): add hierarchical navigation and source metadata。 (`9162553`)
- **Creation** feat(render): show read-only backlog progress overview。 ([#21](https://github.com/shirashu687/okf-devkit/issues/21), `831bb59`)


- **Update** Windowsの旧新出力別名・曖昧パスとmanifest重複を整理前に拒否し、正規化前検査を追加。 (`8359662`)
- **Update** render --cleanup-fromの計画表示・明示整理とhook拒否をPython/Nodeで追加。 (`59a0bb5`)
- **Update** render CLI の既定出力を_siteへ変更し、--outputで従来配置を選べるようにした。check/hook/openとinitのignore案内を新既定に合わせた。 (`bde6d3e`)

- **Creation** render --open を追加。生成先のトップページを開き、check / hook 時は起動しない。 (`a731462`)

- **Creation** new doc に根拠コードの --code-globs 指定を追加し、必須型の生成に要求。relatedを空で生成し、H1直後の空行を保持。 (`be22026`)


## 2026-09-10
- **Creation** feat: add Python-free Node.js CLI。 (`41f58f1`)

## 2026-09-07
- **Update** 共通ハーネスを導入し、固定配布版へ移行。 ([#2](https://github.com/shirashu687/okf-devkit/pull/2), `c14025a`)

## 2026-08-25
- **Creation** feat: OKF v0.2 バンドル運用CLIとして初期実装。 (`1faf59d`)
