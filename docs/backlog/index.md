# backlog ドキュメント

<!-- okf:auto:start -->
| state | 件数 |
|---|---|
| doing | 0 |
| todo | 9 |
| done | 0 |
| dropped | 0 |

## todo
* [CI で自リポジトリの docs バンドルを検証する](/backlog/B-0002-ci-self-lint.md) - `high` `S` - CI で自リポジトリの docs バンドルを検証し、ドキュメントの更新漏れをプルリクで落とせるようにする。
* [okf init が作る shared 層 log.md の位置を設定と一致させる](/backlog/B-0003-fix-shared-log-path.md) - `high` `S` - okf init が作る shared 層の log.md が設定の指す場所と食い違い、履歴が二か所に割れるのを直す。
* [okf-devkit 自身の docs バンドルに本文ドキュメントを書く](/backlog/B-0001-self-hosted-docs.md) - `high` `L` - okf-devkit 自身のコードを対象に本文ドキュメントを書き、affected と stale が実際に効く状態にする。
* [PyPI 公開の準備をする](/backlog/B-0005-pypi-release.md) - `medium` `M` - README が案内している pip install okf-devkit を実際に成立させるため、メタデータを直して公開手順を決める。
* [Python 以外の実行環境からも使えるようにする](/backlog/B-0007-non-python-runtime.md) - `medium` `L` - Python が入っていないリポジトリでも okf を使えるよう、配布方式を決めて用意する。
* [cli.py をモジュールに分割する](/backlog/B-0009-split-cli-module.md) - `medium` `M` - 2,885 行の cli.py を責務ごとに分割し、コマンドを足すたびに単一ファイルが膨らむ状態を解消する。
* [okf new doc 直後に lint の warn が出ないようにする](/backlog/B-0004-new-doc-placeholder.md) - `medium` `M` - okf new doc が置くプレースホルダがそのまま lint の warn になるため、生成直後のファイルが規約を満たさない。
* [生成した HTML をコマンド一発で開けるようにする](/backlog/B-0008-render-open.md) - `medium` `S` - render した HTML を開く手段が無く README の説明とも食い違うため、開くコマンドを用意する。
* [エージェントの Stop hook を自リポジトリに設定する](/backlog/B-0006-agent-hook-setup.md) - `low` `S` - README が勧めている Stop hook をこのリポジトリ自身に設定し、hook の契約を日常的に検証する。
<!-- okf:auto:end -->
