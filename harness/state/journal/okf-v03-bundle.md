# OKF v0.3 のバンドル読取と索引

- 開始点は PR #89 の `6ded0fa399c73f8c83f4055621f6f414f192b70d`。独立 worktree `/tmp/okf-v03-bundle` の `codex/okf-v03-bundle` で開始した。作業開始時の追跡差分はなし。
- [#90](https://github.com/shirashu687/okf-devkit/issues/90) の YAML・コンセプト判定・索引の範囲から両 CLI に実装する。上流仕様は `527e81aff55992be21507e97004286789126f88c`。
- ルート index の宣言を優先し、新規生成は既存の `index.okf_version` を使う。既存バンドルには版を自動追記しない。PR #89 の診断・既存 CLI と合わせて検証する。

## 仕様と標準の照合

- 上流 §3・§4・§8・§11・§12 と旧版の挙動を確認した。0.3 で型なし Markdown を索引・HTML から除き、独自規約は `lint --project` で追加検査する。既存の版宣言・YAML・索引の置換領域外を保持する。
- CLI の互換アダプターと既存の index / render / lint を利用し、旧版の YAML 解釈と既定の生成版は従来どおりとした。Astra の方針レビューでルート索引を版の正本とした。
- 比較 fixture の 0.3 の読み込み、索引の再生成、HTML と lint は両実装で成功した。
