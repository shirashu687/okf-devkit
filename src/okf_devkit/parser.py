"""Argument parsing and help without project state or file writes."""
from __future__ import annotations

import argparse
from .config import CONFIG_FILENAME


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="okf", description="OKF v0.2 バンドルを開発リポジトリで運用する CLI"
    )
    parser.add_argument(
        "--config", help=f"設定ファイルのパス（既定: プロジェクトルートの {CONFIG_FILENAME}）"
    )
    parser.add_argument(
        "--root", help="プロジェクトルート（既定: okf.yml を持つ最も近い祖先 / git トップ）"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_init = sub.add_parser("init", help="OKF バンドルと設定一式を生成する")
    p_init.add_argument("--bundle-root", default="docs", help="バンドルのルート（既定: docs）")
    p_init.add_argument("--site-name", help="ドキュメントの表示名（既定: ルートのディレクトリ名）")
    p_init.add_argument(
        "--layer", action="append", metavar="NAME=GLOB[:DIR]",
        help="層とコード配置の対応（例: client=src/client/**）。複数指定可",
    )
    p_init.add_argument("--force", action="store_true", help="既存ファイルを上書きする")

    p_index = sub.add_parser("index", help="index.md を再生成する")
    p_index.add_argument("--write", action="store_true", help="実際に書き込む")
    p_index.add_argument("--check", action="store_true", help="差分があれば exit 1（CI 用）")
    p_index.add_argument("--quiet", action="store_true", help="変更が無いときは何も出力しない")

    p_log = sub.add_parser("log", help="git 履歴から log.md に追記する")
    p_log.add_argument("--write", action="store_true", help="実際に書き込む")
    p_log.add_argument("--range", help="git のリビジョン範囲（例: A..B）")
    p_log.add_argument("--layer", help="対象の層を限定する")
    p_log.add_argument("--dry-run", action="store_true", help="書き込まずに内容を表示する")

    p_lint = sub.add_parser("lint", help="OKF 適合 + 語彙の検証")
    p_lint.add_argument("--strict", action="store_true", help="warn も exit 1 の対象にする")

    p_stale = sub.add_parser("stale", help="陳腐化レポート")
    p_stale.add_argument("--format", choices=["text", "json"], default="text", help="出力形式: text / json（既定: text）")

    p_affected = sub.add_parser("affected", help="更新すべきドキュメントを列挙する")
    p_affected.add_argument("--base", default="main", help="比較対象のブランチ（既定: main）")
    p_affected.add_argument("--paths", nargs="+", help="変更パスを直接指定する")

    p_new = sub.add_parser("new", help="雛形を生成する")
    new_sub = p_new.add_subparsers(dest="kind", required=True)

    p_new_backlog = new_sub.add_parser("backlog", help="backlog アイテムを作る")
    p_new_backlog.add_argument("--title", required=True, help="アイテムのタイトル")
    p_new_backlog.add_argument("--layer", default="shared", help="設定済みのレイヤー（既定: shared）")
    p_new_backlog.add_argument("--priority", default="medium", help="設定済みの優先度（既定: medium）")
    p_new_backlog.add_argument("--effort", default="M", help="設定済みの工数（既定: M）")
    p_new_backlog.add_argument("--slug", help="ファイル名の slug（日本語タイトル時に指定する）")

    p_new_doc = new_sub.add_parser("doc", help="通常ドキュメントを作る")
    p_new_doc.add_argument("--layer", required=True, help="設定済みのレイヤー")
    p_new_doc.add_argument("--type", required=True, help="設定済みのドキュメント型")
    p_new_doc.add_argument("--title", required=True, help="ドキュメントのタイトル")
    p_new_doc.add_argument("--dir", help="層ディレクトリ配下のサブディレクトリ")
    p_new_doc.add_argument("--code-globs", nargs="+", help="根拠コードのパス/glob（複数可、コード由来の型では必須）")
    p_new_doc.add_argument("--slug", help="ファイル名の slug")

    p_status = sub.add_parser("status", help="backlog の集計")
    p_status.add_argument("--format", choices=["text", "json"], default="text", help="出力形式: text / json（既定: text）")

    p_render = sub.add_parser("render", help="Bundle の Markdown を閲覧用 HTML に変換する")
    p_render.add_argument("--output", help="出力先（既定: _site。旧配置は bundle_root を指定（例: docs））")
    p_render.add_argument("--open", action="store_true", help="生成後にトップページをブラウザで開く（check / hook 時は無効）")
    p_render.add_argument("--check", action="store_true", help="書き込まず、全ページを生成できるか検証する")
    p_render.add_argument("--hook", action="store_true", help="Stop hook 用。成功時は空の JSON だけを返す")

    p_render.add_argument("--cleanup-from", metavar="OLD", help="Move verified old renderer artifacts to backups; --check prints the plan")
    p_sync = sub.add_parser("sync", help="index → log → lint → stale を一括実行する")
    p_sync.add_argument("--gate", action="store_true", help="hook 専用。error の初回は exit 2、同じ error の2回目は exit 0")
    p_sync.add_argument("--session-id", help="gate のセッション識別子（既定: 環境変数 / stdin JSON）")

    examples = {
        "init": "okf init --site-name MyProject",
        "index": "okf index --check",
        "log": "okf log --dry-run",
        "lint": "okf lint --strict",
        "stale": "okf stale --format json",
        "affected": "okf affected --base main",
        "new": "okf new doc --help / okf new backlog --help",
        "new doc": 'okf new doc --layer shared --type "Reference" --title "Guide" --code-globs "src/**"',
        "new backlog": 'okf new backlog --title "Follow-up"',
        "status": "okf status --format json",
        "render": "okf render --check",
        "sync": "okf sync",
    }
    common = ("共通オプション（サブコマンドの前に指定）:\n"
              "  --root DIR     プロジェクトルート\n"
              "  --config FILE  設定ファイルのパス")

    def describe(command_parser, command_actions, prefix=""):
        for action in command_actions:
            name = f"{prefix}{action.dest}"
            child = command_parser.choices[action.dest]
            child.description = action.help
            child.formatter_class = argparse.RawDescriptionHelpFormatter
            child.epilog = f"{common}\n\n例: {examples[name]}"
            for nested in child._actions:
                if isinstance(nested, argparse._SubParsersAction):
                    describe(nested, nested._choices_actions, f"{name} ")

    describe(sub, sub._choices_actions)
    return parser
