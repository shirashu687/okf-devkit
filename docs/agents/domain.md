---
type: Convention
title: Domain docs
description: single-context のドメイン文書を読む場所と順序を定義する。
tags: [agents, domain]
status: stable
layer: shared
generated:
  by: process:okf-devkit
  at: 2026-09-05T14:17:35+09:00
related:
  - /CONVENTIONS.md
  - /AGENTS.md
---

# Domain docs

このリポジトリは single-context 構成で扱う。

## 読む場所と順序

1. ルートの CONTEXT.md
2. 関係する docs/project/decisions/ の Decision Record
3. ルートの AGENTS.md
4. docs/AGENTS.md と docs/CONVENTIONS.md

CONTEXT.md や Decision Record が存在しない場合は、先に作成を要求せず、そのまま進める。新しい用語や後戻りしにくい判断が必要になったときだけ、既存の配置へ追加する。空の用語集や ADR は作らない。

## 利用規約

- issue、仕様、テスト名で使うドメイン語は CONTEXT.md の表現を優先する。
- 既存の判断と矛盾する場合は、該当する Decision Record を明示して再検討を提案する。
- docs/adr/ ではなく docs/project/decisions/ を Decision Record の配置先とする。
