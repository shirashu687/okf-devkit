# 変更履歴 — cli

<!-- `okf log --write` が git 履歴からここに追記する。書式は /CONVENTIONS.md §7 を参照。 -->

## 2026-10-03
- **Update** CLI分割の可変状態・互換interfaceと段階的移行を調査した。 ([Issue #12](https://github.com/shirashu687/okf-devkit/issues/12), `2c6eeea`)
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
