#!/usr/bin/env python3
"""OKF v0.2 バンドルを開発リポジトリで運用するための CLI（okf-devkit）。

決定的に処理できることはすべてこのスクリプトに寄せ、LLM のクレジットは
「文章の中身を書く」非決定的な作業にだけ使う、という方針で作られている。

    okf <command> [options]

    init      リポジトリに OKF バンドルと設定一式を生成する
    index     各ディレクトリの index.md を frontmatter から再生成する
    log       git 履歴から各層の log.md に追記する（冪等）
    lint      OKF 適合 + 独自語彙の検証（CONVENTIONS.md §10 の L1〜L13）
    stale     陳腐化レポート（expired / orphan / outdated / unverified / draft-stale）
    affected  変更パスから更新すべきドキュメントを列挙する
    new       backlog / doc の雛形を生成する（ID 採番込み）
    status    backlog の集計を表示する
    render    バンドルの Markdown を閲覧用 HTML に変換する
    sync      index → log → lint → stale を一括実行する

設定は「パッケージ同梱の defaults.yml」＋「プロジェクトルートの okf.yml」を
マージして決まる。普遍的な語彙は defaults.yml 側にあるので、各リポジトリの
okf.yml には固有の設定（bundle_root / layer / log 出力先）だけを書けばよい。

依存は markdown-it-py（render のみ）と PyYAML。PyYAML が無い環境では内蔵の
厳格な簡易 YAML パーサにフォールバックする（frontmatter のサブセットのみ
対応。曖昧な構文は黙って誤読せず、明確なエラーにする）。

安全性に関する設計方針:

* すべてのファイル書き込みは同一ディレクトリの一時ファイル + fsync +
  ``os.replace()`` による**原子的置換**で行う（中断・容量不足・Windows の
  共有違反で壊れたファイルを残さない）。
* ``index`` は自動生成マーカーの個数・順序を書き込み**前**に検証し、
  1 箇所でも壊れていればどのファイルも書かずに停止する。
* ``log`` は ``config.yml`` の ``log.baseline`` より後のコミットだけを対象にする。
  baseline 未設定でハッシュ無しの既存エントリがある場合は書き込みを拒否する。
* ``sync --gate`` は「同じ lint error 集合に対して exit 2 を返した回数」を
  数える（正常終了や別のエラーではリセットされる）。
"""

from __future__ import annotations

import argparse
import datetime as _dt
import glob as _glob
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path, PurePosixPath

try:  # PyYAML があれば使う
    import yaml as _pyyaml
except Exception:  # pragma: no cover - 環境依存
    _pyyaml = None


# =============================================================================
# 基本ユーティリティ
# =============================================================================

PACKAGE_DIR = Path(__file__).resolve().parent
DEFAULTS_PATH = PACKAGE_DIR / "defaults.yml"
SCAFFOLD_DIR = PACKAGE_DIR / "scaffold"

#: プロジェクト設定のファイル名。この存在がプロジェクトルートの定義になる。
CONFIG_FILENAME = "okf.yml"

#: プロジェクトルート。``main()`` が起動時に確定させる。
#: モジュール読み込み時のパスに依存させないため、既定は CWD にしておく
#: （インストール済みパッケージは自分の位置からリポジトリを推測できない）。
REPO_ROOT = Path.cwd()


def find_project_root(start: Path | None = None) -> Path:
    """``okf.yml`` を持つ最も近い祖先ディレクトリを返す。

    見つからない場合は git のトップレベルへフォールバックし、それも無ければ
    起点をそのまま返す（``init`` は設定が無い状態から動く必要があるため、
    ここでは例外にしない）。
    """
    here = (start or Path.cwd()).resolve()
    for candidate in (here, *here.parents):
        if (candidate / CONFIG_FILENAME).is_file():
            return candidate
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=str(here), capture_output=True, text=True, check=True,
        ).stdout.strip()
        if out:
            return Path(out).resolve()
    except Exception:
        pass
    return here

RESERVED_DEFAULT = ("index.md", "log.md")

# `code_globs`（更新検知の起点）を必須とする type。
# コードから導出されるドキュメントのみ対象で、Convention / Glossary /
# Decision Record / Backlog Item は対象外。`status: deprecated` も除外される。
CODE_GLOBS_REQUIRED_TYPES = ("Project Overview", "Architecture", "Reference", "How-To")


class OkfError(Exception):
    """CLI が利用者に見せる想定のエラー。"""


class MarkerError(OkfError):
    """index.md の自動生成マーカーが壊れている。"""


def rel_posix(path: Path, base: Path) -> str:
    """base からの相対パスを常に `/` 区切りの文字列で返す。"""
    return PurePosixPath(Path(path).resolve().relative_to(Path(base).resolve()).as_posix()).as_posix()


def read_text(path: Path) -> str:
    """UTF-8 で読み、改行を LF に正規化して返す。"""
    data = path.read_bytes()
    if data.startswith(b"\xef\xbb\xbf"):  # BOM 付きでも読めるようにする
        data = data[3:]
    return data.decode("utf-8").replace("\r\n", "\n").replace("\r", "\n")


def atomic_write_bytes(path: Path, data: bytes, retries: int = 5) -> None:
    """同一ディレクトリの一時ファイル経由で原子的に書き込む。

    flush + fsync の後に ``os.replace()`` するため、途中で落ちても対象ファイルは
    「元のまま」か「新しい内容」のどちらかにしかならない。Windows で置換が
    共有違反になる場合は短くリトライし、それでも駄目なら元ファイルを残したまま
    ``OkfError`` を送出する。
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix="." + path.name + ".", suffix=".okftmp", dir=str(path.parent))
    tmp = Path(tmp_name)
    try:
        with os.fdopen(fd, "wb") as fh:
            fh.write(data)
            fh.flush()
            os.fsync(fh.fileno())
        last: Exception | None = None
        for attempt in range(max(1, retries)):
            try:
                os.replace(str(tmp), str(path))
                tmp = None  # type: ignore[assignment]
                return
            except PermissionError as exc:  # Windows の共有違反
                last = exc
                time.sleep(0.05 * (attempt + 1))
        raise OkfError(
            f"書き込みに失敗しました（ファイルがロックされています）: "
            f"{path} ({last})"
        )
    finally:
        if tmp is not None:
            try:
                tmp.unlink()
            except OSError:  # pragma: no cover - 後始末なので握る
                pass


def write_if_changed(path: Path, content: str) -> bool:
    """内容が変わるときだけ UTF-8 / LF で原子的に書き込む。書いたら True。"""
    new = content.replace("\r\n", "\n").encode("utf-8")
    if path.exists():
        try:
            if path.read_bytes() == new:
                return False
        except OSError:
            pass
    atomic_write_bytes(path, new)
    return True


def today() -> _dt.date:
    return _dt.date.today()


def now_iso() -> str:
    """現在時刻を ISO 8601 (UTC) で返す。"""
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def is_iso_date(value) -> bool:
    """`YYYY-MM-DD` として完全一致し、かつ実在する日付か。"""
    if not isinstance(value, str) or not ISO_DATE_RE.match(value):
        return False
    try:
        _dt.date.fromisoformat(value)
    except ValueError:
        return False
    return True


def extract_date(value) -> str | None:
    """任意の値から `YYYY-MM-DD` を抜き出す（PyYAML が date 型にした場合も吸収）。"""
    if value is None:
        return None
    m = re.search(r"\d{4}-\d{2}-\d{2}", str(value))
    if not m:
        return None
    return m.group(0) if is_iso_date(m.group(0)) else None


def parse_datetime(value) -> tuple[_dt.datetime | None, bool]:
    """ISO 8601 文字列を (datetime, 時刻を含むか) に変換する。

    タイムゾーンが無い場合は UTC とみなす。解釈できなければ (None, False)。
    """
    if value is None:
        return None, False
    text = str(value).strip()
    if not text:
        return None, False
    if ISO_DATE_RE.match(text):
        try:
            d = _dt.date.fromisoformat(text)
        except ValueError:
            return None, False
        return _dt.datetime(d.year, d.month, d.day, tzinfo=_dt.timezone.utc), False
    norm = text.replace("Z", "+00:00").replace("z", "+00:00").replace(" ", "T", 1)
    try:
        parsed = _dt.datetime.fromisoformat(norm)
    except ValueError:
        return None, False
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=_dt.timezone.utc)
    return parsed, True


def glob_to_regex(pattern: str) -> re.Pattern:
    """glob 文字列をパス照合用の正規表現に変換する（`**` は `/` を跨ぐ）。

    `*` / `?` / `[...]`（`[!...]` の否定も含む）に対応する。この関数が
    リポジトリ内での glob 解釈の**唯一の実装**であり、`resolve_resource()` も
    最終的にここを通して結果を絞り込む。
    """
    out: list[str] = []
    i = 0
    n = len(pattern)
    while i < n:
        c = pattern[i]
        if c == "*":
            if pattern.startswith("**/", i):
                out.append("(?:.*/)?")
                i += 3
                continue
            if pattern.startswith("**", i):
                out.append(".*")
                i += 2
                continue
            out.append("[^/]*")
            i += 1
            continue
        if c == "?":
            out.append("[^/]")
            i += 1
            continue
        if c == "[":
            j = i + 1
            if j < n and pattern[j] in "!^":
                j += 1
            if j < n and pattern[j] == "]":
                j += 1
            while j < n and pattern[j] != "]":
                j += 1
            if j >= n:  # 閉じていない `[` はリテラル扱い
                out.append(re.escape(c))
                i += 1
                continue
            inner = pattern[i + 1:j]
            if inner[:1] in ("!", "^"):
                inner = "^" + inner[1:]
            inner = inner.replace("\\", "\\\\")
            out.append("[" + inner + "]")
            i = j + 1
            continue
        out.append(re.escape(c))
        i += 1
    return re.compile("^" + "".join(out) + "$")


_GLOB_CACHE: dict[str, re.Pattern] = {}


def path_matches(path: str, pattern: str) -> bool:
    """`/` 区切りのパスが glob にマッチするか。"""
    rx = _GLOB_CACHE.get(pattern)
    if rx is None:
        rx = glob_to_regex(pattern)
        _GLOB_CACHE[pattern] = rx
    return bool(rx.match(path))


# =============================================================================
# YAML（PyYAML があれば PyYAML、無ければ内蔵の厳格な簡易パーサ）
# =============================================================================


class YamlSubsetError(OkfError):
    """内蔵パーサが対応していない YAML 構文に当たった。"""


def _normalize(value):
    """date / datetime を文字列に落とし、PyYAML と内蔵パーサの結果を揃える。"""
    if isinstance(value, dict):
        return {str(k): _normalize(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_normalize(v) for v in value]
    if isinstance(value, _dt.datetime):
        if value.tzinfo is not None:
            value = value.astimezone(_dt.timezone.utc)
        return value.strftime("%Y-%m-%dT%H:%M:%SZ")
    if isinstance(value, _dt.date):
        return value.isoformat()
    return value


def parse_yaml(text: str, source: str = "<yaml>"):
    """YAML を dict / list に変換する。PyYAML 優先、無ければ内蔵パーサ。"""
    if _pyyaml is not None:
        try:
            return _normalize(_pyyaml.safe_load(text))
        except Exception as exc:  # YAMLError 以外も握る
            raise OkfError(f"{source}: YAML のパースに失敗しました: {exc}") from exc
    return _normalize(_MiniYaml(text, source).parse())


# --- 内蔵の簡易 YAML パーサ ------------------------------------------------
#
# 対応範囲: スカラー / 文字列リスト / ネストしたマップ / マップのリスト /
#           フロー表記 `[a, b]` `{k: v}` / コメント。
#
# 方針: PyYAML と結果が食い違う可能性のある構文は、黙って誤読せず必ず
#       YamlSubsetError にする。具体的には次を拒否する。
#         - plain scalar 中の `: `（`title: foo: bar` など）
#         - 引用符内のエスケープ（`"a\nb"`、`'it''s'`）
#         - アンカー / エイリアス / タグ（`&a` `*a` `!!str`）
#         - ブロックスカラー（`|` `>`）
#       真偽値は YAML 1.1（PyYAML safe_load）に合わせ yes/no/on/off も解釈し、
#       タイムスタンプは PyYAML と同じ正規化（UTC の `...Z`）を行う。

_MINI_BOOL_TRUE = {"true", "True", "TRUE", "yes", "Yes", "YES", "on", "On", "ON"}
_MINI_BOOL_FALSE = {"false", "False", "FALSE", "no", "No", "NO", "off", "Off", "OFF"}
_MINI_NULL = {"", "null", "Null", "NULL", "~"}
_MINI_INT_RE = re.compile(r"^[-+]?[0-9]+$")
_MINI_FLOAT_RE = re.compile(r"^[-+]?(?:[0-9]+\.[0-9]*|\.[0-9]+|[0-9]+)(?:[eE][-+]?[0-9]+)?$")
_MINI_TS_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2}"
    r"(?:[Tt ]\d{2}:\d{2}:\d{2}(?:\.\d+)?"
    r"(?:\s*(?:Z|z|[+-]\d{1,2}(?::?\d{2})?))?)?$"
)


def _mini_timestamp(t: str):
    """PyYAML と同じ正規化結果（date は ISO、datetime は UTC の `...Z`）を返す。"""
    if ISO_DATE_RE.match(t):
        try:
            return _dt.date.fromisoformat(t).isoformat()
        except ValueError:
            return None
    norm = t.strip().replace("t", "T", 1) if t[:1].isdigit() else t
    norm = re.sub(r"[Tt ]", "T", norm, count=1)
    norm = re.sub(r"\s*[Zz]$", "+00:00", norm)
    norm = re.sub(r"([+-]\d{2})$", r"\1:00", norm)
    norm = re.sub(r"([+-])(\d):", r"\g<1>0\2:", norm)
    try:
        parsed = _dt.datetime.fromisoformat(norm)
    except ValueError:
        return None
    if parsed.tzinfo is not None:
        parsed = parsed.astimezone(_dt.timezone.utc)
    return parsed.strftime("%Y-%m-%dT%H:%M:%SZ")


def _mini_scalar(token: str, source: str = "<yaml>", line_no: int = 0):
    """1 つのスカラーを厳格に解釈する。曖昧なものは例外にする。"""
    t = token.strip()
    if t == "":
        return None
    if t[0] in "\"'":
        quote = t[0]
        if len(t) < 2 or t[-1] != quote:
            raise YamlSubsetError(f"{source}:{line_no}: 引用符が閉じていません: {t!r}")
        inner = t[1:-1]
        if quote == '"':
            if "\\" in inner:
                raise YamlSubsetError(
                    f"{source}:{line_no}: 引用符内のエスケープは非対応です。"
                    " PyYAML をインストールしてください（pip install pyyaml）"
                )
            if '"' in inner:
                raise YamlSubsetError(f"{source}:{line_no}: 二重引用符が入れ子になっています: {t!r}")
        else:
            if "'" in inner:
                raise YamlSubsetError(
                    f"{source}:{line_no}: 単一引用符のエスケープ（''）は非対応です。PyYAML をインストールしてください"
                )
        return inner
    if t[0] in "&*!":
        raise YamlSubsetError(
            f"{source}:{line_no}: アンカー/エイリアス/タグは非対応です。PyYAML をインストールしてください"
        )
    if t in ("|", ">", "|-", ">-", "|+", ">+"):
        raise YamlSubsetError(
            f"{source}:{line_no}: ブロックスカラー（{t}）は非対応です。PyYAML をインストールしてください"
        )
    if ": " in t or t.endswith(":"):
        raise YamlSubsetError(
            f"{source}:{line_no}: plain scalar に `: ` は書けません（引用符で囲んでください）: {t!r}"
        )
    if t in _MINI_NULL:
        return None
    if t in _MINI_BOOL_TRUE:
        return True
    if t in _MINI_BOOL_FALSE:
        return False
    if _MINI_TS_RE.match(t):
        ts = _mini_timestamp(t)
        if ts is None:
            raise YamlSubsetError(f"{source}:{line_no}: 日付/時刻として解釈できません: {t!r}")
        return ts
    if _MINI_INT_RE.match(t):
        return int(t)
    if _MINI_FLOAT_RE.match(t) and ("." in t or "e" in t or "E" in t):
        return float(t)
    return t


def _strip_inline_comment(line: str) -> str:
    """引用符の外にある ` #` 以降をコメントとして落とす。"""
    out = []
    quote = None
    for i, ch in enumerate(line):
        if quote:
            out.append(ch)
            if ch == quote:
                quote = None
            continue
        if ch in "\"'":
            quote = ch
            out.append(ch)
            continue
        if ch == "#" and (i == 0 or line[i - 1] in " \t"):
            break
        out.append(ch)
    return "".join(out).rstrip()


class _MiniYaml:
    """frontmatter / config.yml のサブセットだけを扱う厳格な簡易パーサ。"""

    KEY_RE = re.compile(r'^(?:"([^"]*)"|\'([^\']*)\'|([^:#]+?))\s*:\s*(.*)$')

    def __init__(self, text: str, source: str = "<yaml>"):
        self.source = source
        self.lines: list[list] = []  # [indent, content, 元の行番号]
        for no, raw in enumerate(text.split("\n"), start=1):
            if not raw.strip() or raw.lstrip().startswith("#"):
                continue
            if raw.strip() in ("---", "..."):
                continue
            content = _strip_inline_comment(raw)
            if not content.strip():
                continue
            indent = len(content) - len(content.lstrip(" "))
            if "\t" in content[:indent]:
                raise YamlSubsetError(f"{self.source}:{no}: タブによるインデントは非対応です")
            self.lines.append([indent, content.strip(), no])

    def parse(self):
        if not self.lines:
            return {}
        value, idx = self._block(0, self.lines[0][0])
        if idx != len(self.lines):
            no = self.lines[idx][2]
            raise YamlSubsetError(f"{self.source}:{no}: インデント構造を解釈できませんでした")
        return value

    # -- ブロック ----------------------------------------------------------
    def _block(self, i: int, indent: int):
        if self.lines[i][1].startswith("-"):
            return self._seq(i, indent)
        return self._map(i, indent)

    def _seq(self, i: int, indent: int):
        items = []
        while i < len(self.lines) and self.lines[i][0] == indent:
            content = self.lines[i][1]
            no = self.lines[i][2]
            m = re.match(r"^-(\s+|$)", content)
            if not m:
                break
            rest = content[m.end():]
            offset = m.end()
            if rest == "":
                # `-` のみ。次の行から入れ子のブロックを読む
                if i + 1 < len(self.lines) and self.lines[i + 1][0] > indent:
                    value, i = self._block(i + 1, self.lines[i + 1][0])
                else:
                    value, i = None, i + 1
                items.append(value)
                continue
            if rest[0] in "[{":
                items.append(_parse_flow(rest, self.source, no))
                i += 1
                continue
            if self.KEY_RE.match(rest) and not rest.startswith(("http://", "https://")):
                # `- key: value` 形式。マップとして読み直す
                child_indent = indent + offset
                self.lines[i] = [child_indent, rest, no]
                value, i = self._map(i, child_indent)
                items.append(value)
                continue
            items.append(_mini_scalar(rest, self.source, no))
            i += 1
        return items, i

    def _map(self, i: int, indent: int):
        result: dict = {}
        while i < len(self.lines) and self.lines[i][0] == indent:
            content = self.lines[i][1]
            no = self.lines[i][2]
            if content.startswith("-"):
                break
            m = self.KEY_RE.match(content)
            if not m:
                raise YamlSubsetError(
                    f"{self.source}:{no}: `key: value` として解釈できません: {content!r}"
                )
            key = m.group(1) or m.group(2) or (m.group(3) or "").strip()
            if key.startswith(("&", "*", "!")):
                raise YamlSubsetError(
                    f"{self.source}:{no}: アンカー/エイリアス/タグは非対応です。PyYAML をインストールしてください"
                )
            rest = m.group(4).strip()
            if rest == "":
                nxt = i + 1
                if nxt < len(self.lines) and (
                    self.lines[nxt][0] > indent
                    or (self.lines[nxt][0] == indent and self.lines[nxt][1].startswith("-"))
                ):
                    value, i = self._block(nxt, self.lines[nxt][0])
                else:
                    value, i = None, i + 1
            elif rest[0] in "[{":
                value = _parse_flow(rest, self.source, no)
                i += 1
            else:
                value = _mini_scalar(rest, self.source, no)
                i += 1
            if key in result:
                raise YamlSubsetError(f"{self.source}:{no}: キーが重複しています: {key!r}")
            result[key] = value
        return result, i


def _parse_flow(text: str, source: str, line_no: int):
    """`[a, b]` / `{k: v}` のフロー表記をパースする。"""
    value, idx = _flow_value(text, 0, source, line_no)
    if text[idx:].strip():
        raise YamlSubsetError(f"{source}:{line_no}: フロー表記の後に余分な文字があります")
    return value


def _flow_skip(text: str, i: int) -> int:
    while i < len(text) and text[i] in " \t":
        i += 1
    return i


def _flow_value(text: str, i: int, source: str, line_no: int):
    i = _flow_skip(text, i)
    if i >= len(text):
        return None, i
    if text[i] in "&*!":
        raise YamlSubsetError(
            f"{source}:{line_no}: アンカー/エイリアス/タグは非対応です。PyYAML をインストールしてください"
        )
    if text[i] == "[":
        i += 1
        arr = []
        while True:
            i = _flow_skip(text, i)
            if i >= len(text):
                raise YamlSubsetError(f"{source}:{line_no}: `]` が閉じていません")
            if text[i] == "]":
                return arr, i + 1
            value, i = _flow_value(text, i, source, line_no)
            arr.append(value)
            i = _flow_skip(text, i)
            if i < len(text) and text[i] == ",":
                i += 1
    if text[i] == "{":
        i += 1
        obj: dict = {}
        while True:
            i = _flow_skip(text, i)
            if i >= len(text):
                raise YamlSubsetError(f"{source}:{line_no}: `}}` が閉じていません")
            if text[i] == "}":
                return obj, i + 1
            key, i = _flow_scalar(text, i, ":,}]", source, line_no)
            i = _flow_skip(text, i)
            if i >= len(text) or text[i] != ":":
                raise YamlSubsetError(f"{source}:{line_no}: フローマップの `:` がありません")
            i += 1
            value, i = _flow_value(text, i, source, line_no)
            obj[str(key)] = value
            i = _flow_skip(text, i)
            if i < len(text) and text[i] == ",":
                i += 1
    return _flow_scalar(text, i, ",}]", source, line_no)


def _flow_scalar(text: str, i: int, stops: str, source: str, line_no: int):
    i = _flow_skip(text, i)
    if i < len(text) and text[i] in "\"'":
        quote = text[i]
        j = text.find(quote, i + 1)
        if j < 0:
            raise YamlSubsetError(f"{source}:{line_no}: 引用符が閉じていません")
        inner = text[i + 1:j]
        if quote == '"' and "\\" in inner:
            raise YamlSubsetError(
                f"{source}:{line_no}: 引用符内のエスケープは非対応です。PyYAML をインストールしてください"
            )
        return inner, j + 1
    j = i
    while j < len(text) and text[j] not in stops:
        j += 1
    return _mini_scalar(text[i:j], source, line_no), j


# =============================================================================
# YAML シリアライズ（new コマンド用）
# =============================================================================

_YAML_PLAIN_SAFE_RE = re.compile(r"^[^\s\"'#&*!|>%@`\[\]{},:][^:#]*$")


def yaml_scalar(value) -> str:
    """frontmatter に埋め込める安全な YAML スカラー文字列を返す。"""
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int) and not isinstance(value, bool):
        return str(value)
    text = str(value)
    if "\n" in text or "\r" in text:
        raise OkfError("frontmatter の値に改行は使えません")
    if text == "":
        return '""'
    ambiguous = (
        not _YAML_PLAIN_SAFE_RE.match(text)
        or text != text.strip()
        or ": " in text
        or text.endswith(":")
        or " #" in text
        or text in _MINI_NULL
        or text in _MINI_BOOL_TRUE
        or text in _MINI_BOOL_FALSE
        or bool(_MINI_INT_RE.match(text))
        or bool(_MINI_FLOAT_RE.match(text))
        or bool(_MINI_TS_RE.match(text))
    )
    if ambiguous:
        return '"' + text.replace("\\", "\\\\").replace('"', '\\"') + '"'
    return text


def yaml_flow_list(values) -> str:
    return "[" + ", ".join(yaml_scalar(v) for v in values) + "]"


# =============================================================================
# frontmatter
# =============================================================================


class Doc:
    """バンドル内の 1 ファイルを表す。"""

    def __init__(self, path: Path, bundle_root: Path):
        self.path = path
        self.repo_rel = rel_posix(path, REPO_ROOT)
        self.bundle_rel = "/" + rel_posix(path, bundle_root)
        self.name = path.name
        self.text = read_text(path)
        self.fm: dict = {}
        self.fm_error: str | None = None
        self.has_fm = False
        self.fm_opened = False  # 先頭が `---` だったか（終端欠落の判定用）
        self.body = self.text
        self._fm_lines: list[str] = []
        self._parse()

    def _parse(self) -> None:
        lines = self.text.split("\n")
        if not lines or lines[0].strip() != "---":
            return
        self.fm_opened = True
        end = None
        for idx in range(1, len(lines)):
            if lines[idx].strip() in ("---", "..."):
                end = idx
                break
        if end is None:
            self.fm_error = "frontmatter の終端 `---` がありません"
            return
        self.has_fm = True
        self._fm_lines = lines[1:end]
        self.body = "\n".join(lines[end + 1:])
        try:
            data = parse_yaml("\n".join(self._fm_lines), self.repo_rel)
        except OkfError as exc:
            self.fm_error = str(exc)
            return
        if data is None:
            data = {}
        if not isinstance(data, dict):
            self.fm_error = "frontmatter がマップではありません"
            return
        self.fm = data

    # -- 参照系 ------------------------------------------------------------
    def get(self, key, default=None):
        value = self.fm.get(key, default)
        return default if value is None else value

    def key_line(self, key: str) -> int | None:
        """frontmatter 内のトップレベルキーの行番号（1 始まり）。"""
        for idx, line in enumerate(self._fm_lines):
            if re.match(rf"^{re.escape(key)}\s*:", line):
                return idx + 2  # `---` の分
        return None

    @property
    def h1(self) -> str | None:
        for line in self.body.split("\n"):
            m = re.match(r"^#\s+(.+?)\s*$", line)
            if m:
                return m.group(1)
        return None

    @property
    def title(self) -> str:
        title = self.fm.get("title")
        if isinstance(title, str) and title.strip():
            return title.strip()
        if self.h1:
            return self.h1
        return self.path.stem.replace("-", " ").replace("_", " ")

    @property
    def description(self) -> str:
        desc = self.fm.get("description")
        return desc.strip() if isinstance(desc, str) else ""

    @property
    def type(self) -> str:
        value = self.fm.get("type")
        return value.strip() if isinstance(value, str) else ""

    @property
    def status(self) -> str:
        value = self.fm.get("status")
        return value.strip() if isinstance(value, str) else "stable"

    def code_globs(self) -> list[str]:
        """`code_globs` の一覧（正しい形式のものだけ）。更新検知の起点。

        OKF 標準の `sources` は出典（provenance）専用なので、変更監視用の
        glob はこの独自キーに分離している。
        """
        out = []
        raw = self.fm.get("code_globs")
        if isinstance(raw, list):
            for item in raw:
                if isinstance(item, str) and item.strip():
                    out.append(item.strip().replace("\\", "/"))
        return out

    def code_globs_problems(self) -> list[str]:
        """`code_globs` の形式上の問題を返す。

        欠如が問題かどうかは type / status に依存するため、ここでは
        「書かれている場合の形式」だけを検査する。
        """
        problems: list[str] = []
        raw = self.fm.get("code_globs")
        if raw is None:
            return problems
        if not isinstance(raw, list):
            return [f"`code_globs` はリストである必要があります（現在: {type(raw).__name__}）"]
        for pos, item in enumerate(raw, start=1):
            if not isinstance(item, str) or not item.strip():
                problems.append(f"`code_globs[{pos}]` が空、または文字列ではありません")
        return problems

    def requires_code_globs(self) -> bool:
        """このドキュメントが `code_globs` を必須とするか。

        コードから導出される type のみ必須。`status: deprecated` は除外する。
        """
        if self.status == "deprecated":
            return False
        return self.type in CODE_GLOBS_REQUIRED_TYPES

    def source_problems(self) -> list[str]:
        """`sources`（OKF 標準の provenance）の形式上の問題を返す。欠如は問題としない。"""
        problems: list[str] = []
        raw = self.fm.get("sources")
        if raw is None:
            return problems
        if not isinstance(raw, list):
            return [f"`sources` はリストである必要があります（現在: {type(raw).__name__}）"]
        for pos, item in enumerate(raw, start=1):
            if not isinstance(item, dict):
                problems.append(f"`sources[{pos}]` はマップ（`- resource: ...`）である必要があります")
                continue
            resource = item.get("resource")
            if not isinstance(resource, str) or not resource.strip():
                problems.append(f"`sources[{pos}].resource` が空、または文字列ではありません")
        return problems


# =============================================================================
# 設定・バンドル走査
# =============================================================================


def merge_config(base: dict, override: dict) -> dict:
    """``base`` に ``override`` を重ねた新しい dict を返す。

    dict は再帰的にマージし、**リストとスカラーは丸ごと置換**する。
    リストを追記扱いにすると「既定の語彙を減らせない」ため、
    プロジェクト側が ``types`` を書いたらその内容が唯一の正になる。
    """
    out = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(out.get(key), dict):
            out[key] = merge_config(out[key], value)
        else:
            out[key] = value
    return out


def load_merged_config(cfg_path: Path) -> dict:
    """同梱の ``defaults.yml`` にプロジェクトの ``okf.yml`` を重ねて返す。"""
    if not DEFAULTS_PATH.exists():  # pragma: no cover - 壊れたインストール向け
        raise OkfError(f"同梱の既定設定が見つかりません: {DEFAULTS_PATH}")
    defaults = parse_yaml(read_text(DEFAULTS_PATH), str(DEFAULTS_PATH))
    if not isinstance(defaults, dict):  # pragma: no cover
        raise OkfError(f"既定設定の形式が不正です: {DEFAULTS_PATH}")

    project = parse_yaml(read_text(cfg_path), str(cfg_path))
    if project is None:
        project = {}
    if not isinstance(project, dict):
        raise OkfError(f"設定ファイルの形式が不正です: {cfg_path}")
    return merge_config(defaults, project)


class Bundle:
    """docs/ バンドル全体と設定を保持する。"""

    def __init__(self, config_path: Path | None = None):
        cfg_path = config_path or (REPO_ROOT / CONFIG_FILENAME)
        if not cfg_path.exists():
            raise OkfError(
                f"設定ファイルが見つかりません: {cfg_path}\n"
                "  `okf init` で生成するか、--config でパスを指定してください。"
            )
        cfg = load_merged_config(cfg_path)
        self.cfg = cfg
        self.config_path = cfg_path
        self.root = (REPO_ROOT / str(cfg.get("bundle_root", "docs"))).resolve()
        self.exclude = list(cfg.get("exclude") or [])
        self.reserved = tuple(cfg.get("reserved") or RESERVED_DEFAULT)
        self.types = list(cfg.get("types") or [])
        self.statuses = list(cfg.get("statuses") or ["draft", "stable", "deprecated"])
        self.site_name = str(cfg.get("site_name") or REPO_ROOT.name)
        self.layers = list(cfg.get("layers") or [])
        self.index_cfg = dict(cfg.get("index") or {})
        self.backlog_cfg = dict(cfg.get("backlog") or {})
        self.log_cfg = dict(cfg.get("log") or {})
        self._docs: list[Doc] | None = None

    # -- パス判定 ----------------------------------------------------------
    def is_excluded(self, path: Path) -> bool:
        try:
            rel = rel_posix(path, self.root)
        except ValueError:
            return True
        return any(path_matches(rel, pat) for pat in self.exclude)

    def dirs(self) -> list[Path]:
        """index 生成対象のディレクトリ（バンドルルート含む）を昇順で返す。"""
        found = [self.root]
        for dirpath, dirnames, _files in os.walk(self.root):
            dirnames[:] = sorted(
                d for d in dirnames
                if not d.startswith(("_", "."))
                and not self.is_excluded(Path(dirpath) / d)
            )
            for d in dirnames:
                found.append(Path(dirpath) / d)
        return sorted(set(found), key=lambda p: rel_posix(p, self.root) if p != self.root else "")

    def md_files(self, include_reserved: bool = False) -> list[Path]:
        out = []
        for d in self.dirs():
            for p in sorted(d.iterdir()):
                if p.is_file() and p.suffix == ".md" and not self.is_excluded(p):
                    if not include_reserved and p.name in self.reserved:
                        continue
                    out.append(p)
        return out

    def docs(self) -> list[Doc]:
        """非予約ファイルの Doc 一覧（キャッシュ付き）。"""
        if self._docs is None:
            self._docs = [Doc(p, self.root) for p in self.md_files()]
        return self._docs

    def backlog_dir(self) -> Path:
        return self.root / str(self.backlog_cfg.get("dir", "backlog"))

    # -- log の出力先 ------------------------------------------------------
    def log_layers(self) -> list[str]:
        """自動追記の対象になる層。"""
        value = self.log_cfg.get("layers")
        if value is None:
            return list(self.layers)
        return [str(v) for v in value]

    def log_path(self, layer: str) -> Path:
        """層 → log.md のパス（`log.paths` で層ごとに差し替え可能）。"""
        paths = self.log_cfg.get("paths") or {}
        rel = paths.get(layer) if isinstance(paths, dict) else None
        if rel:
            return (self.root / str(rel)).resolve()
        return (self.root / layer / "log.md").resolve()


# =============================================================================
# git ヘルパー
# =============================================================================


def git(*args: str, cwd: Path | None = None) -> tuple[int, str]:
    """git を実行して (returncode, stdout) を返す。失敗しても例外にしない。"""
    try:
        proc = subprocess.run(
            ["git", *args],
            cwd=str(cwd or REPO_ROOT),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
    except FileNotFoundError:
        return 127, ""
    return proc.returncode, proc.stdout or ""


def git_available() -> bool:
    code, _ = git("rev-parse", "--git-dir")
    return code == 0


def has_commits() -> bool:
    """1 つ以上のコミットがあるか（初回コミット前は False）。"""
    code, _ = git("rev-parse", "--verify", "--quiet", "HEAD")
    return code == 0


def is_shallow() -> bool:
    code, out = git("rev-parse", "--is-shallow-repository")
    return code == 0 and out.strip() == "true"


def repo_web_url() -> str | None:
    """origin の URL から GitHub の https URL を導出する。"""
    code, out = git("remote", "get-url", "origin")
    if code != 0 or not out.strip():
        return None
    url = out.strip()
    m = re.match(r"^git@([^:]+):(.+?)(?:\.git)?$", url)
    if m:
        return f"https://{m.group(1)}/{m.group(2)}"
    m = re.match(r"^(https?://[^\s]+?)(?:\.git)?$", url)
    if m:
        return m.group(1)
    return None


def resolve_ref(ref: str) -> str | None:
    """ref を解決できれば ref 名を返す（`<ref>` → `origin/<ref>` の順）。"""
    for candidate in (ref, f"origin/{ref}"):
        code, _ = git("rev-parse", "--verify", "--quiet", f"{candidate}^{{commit}}")
        if code == 0:
            return candidate
    return None


def resolve_commit(ref: str) -> str | None:
    """ref を full SHA に解決する。"""
    code, out = git("rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}")
    if code != 0:
        return None
    return out.strip() or None


# --- git log / status の -z 解析 -------------------------------------------


def _parse_log_z(out: str, field_count: int) -> list[tuple[list[str], list[tuple[str, str]]]]:
    """`-z` + `--name-status` の出力を [(ヘッダ項目, [(status, path), ...])] にする。"""
    tokens = out.split("\0")
    records: list[tuple[list[str], list[tuple[str, str]]]] = []
    current: tuple[list[str], list[tuple[str, str]]] | None = None
    i = 0
    while i < len(tokens):
        tok = tokens[i]
        if tok == "":
            i += 1
            continue
        if tok.startswith("@@@"):
            head, nl, rest = tok.partition("\n")
            fields = head[3:].split("\t", field_count - 1)
            while len(fields) < field_count:
                fields.append("")
            current = (fields, [])
            records.append(current)
            if nl and rest:
                tokens[i] = rest  # 先頭のステータス/パスとして読み直す
                continue
            i += 1
            continue
        if current is None:
            i += 1
            continue
        i = _consume_change(tokens, i, current[1])
    return records


def _consume_change(tokens: list[str], i: int, out: list[tuple[str, str]]) -> int:
    status = tokens[i]
    if status[:1] in ("R", "C"):
        old = tokens[i + 1] if i + 1 < len(tokens) else ""
        new = tokens[i + 2] if i + 2 < len(tokens) else ""
        for p in (old, new):
            if p:
                out.append((status, p.replace("\\", "/")))
        return i + 3
    path = tokens[i + 1] if i + 1 < len(tokens) else ""
    if path:
        out.append((status, path.replace("\\", "/")))
    return i + 2


def parse_porcelain_z(out: str) -> list[str]:
    """`git status --porcelain -z` を解析する（rename は新旧の両方を返す）。"""
    tokens = out.split("\0")
    paths: list[str] = []
    i = 0
    while i < len(tokens):
        rec = tokens[i]
        if not rec:
            i += 1
            continue
        xy = rec[:2]
        path = rec[3:] if len(rec) > 3 else ""
        if path:
            paths.append(path.replace("\\", "/"))
        if "R" in xy or "C" in xy:
            if i + 1 < len(tokens) and tokens[i + 1]:
                paths.append(tokens[i + 1].replace("\\", "/"))
            i += 2
        else:
            i += 1
    return paths


_PATH_TIME_MAP: dict[str, str] | None = None


def path_commit_times() -> dict[str, str]:
    """全履歴を 1 回だけ走査して path → 最終コミット日時（ISO 8601）を作る。

    `git log -1 -- <paths>` をパス集合ごとに呼ぶ方式だと、パス数が増えるほど
    git プロセスが増え、引数上限で切り捨てる必要も出てくる。ここでは
    1 回の `git log --name-only -z` から全件の対応表を作る。
    """
    global _PATH_TIME_MAP
    if _PATH_TIME_MAP is not None:
        return _PATH_TIME_MAP
    mapping: dict[str, str] = {}
    if has_commits():
        code, out = git("log", "-z", "--pretty=format:@@@%cI", "--name-status")
        if code == 0:
            for fields, changes in _parse_log_z(out, 1):
                when = fields[0].strip()
                if not when:
                    continue
                for _status, path in changes:
                    mapping.setdefault(path, when)  # 新しい順なので最初の 1 件が最新
    _PATH_TIME_MAP = mapping
    return mapping


def last_commit_time(paths: list[str]) -> str | None:
    """指定パス群の最終コミット日時（ISO 8601 文字列）。"""
    mapping = path_commit_times()
    best: str | None = None
    best_dt: _dt.datetime | None = None
    for path in paths:
        raw = mapping.get(path)
        if not raw:
            continue
        parsed, _ = parse_datetime(raw)
        if parsed is None:
            continue
        if best_dt is None or parsed > best_dt:
            best_dt, best = parsed, raw
    return best


def resolve_resource(resource: str) -> list[str]:
    """sources[].resource（パス or glob）を実ファイルのリストに解決する。

    列挙は標準の :mod:`glob` で行い、最終的な採否は ``path_matches()``
    （= `glob_to_regex`）で決める。これにより lint / stale / affected の
    glob 解釈が 1 実装に揃う。
    """
    pattern = resource.replace("\\", "/").lstrip("/")
    if not pattern:
        return []
    if not any(ch in pattern for ch in "*?["):
        p = REPO_ROOT / pattern
        return [pattern] if p.is_file() else []
    matched = _glob.glob(pattern, root_dir=str(REPO_ROOT), recursive=True)
    out = []
    for rel in matched:
        rel = rel.replace("\\", "/")
        if (REPO_ROOT / rel).is_file() and path_matches(rel, pattern):
            out.append(rel)
    return sorted(out)


# =============================================================================
# index コマンド
# =============================================================================


def md_escape_label(text: str) -> str:
    """Markdown のリンクラベルとして安全な文字列にする。"""
    cleaned = re.sub(r"\s*[\r\n]+\s*", " ", str(text)).strip()
    return cleaned.replace("\\", "\\\\").replace("[", "\\[").replace("]", "\\]")


def md_escape_link(link: str) -> str:
    """Markdown のリンク先として安全な文字列にする。"""
    cleaned = re.sub(r"\s*[\r\n]+\s*", "", str(link)).strip()
    return (
        cleaned.replace("%", "%25")
        .replace("(", "%28")
        .replace(")", "%29")
        .replace(" ", "%20")
    )


def md_escape_text(text: str) -> str:
    """説明文として安全な 1 行文字列にする。"""
    return re.sub(r"\s*[\r\n]+\s*", " ", str(text)).strip()


def _entry_line(title: str, link: str, description: str, extra: str = "") -> str:
    parts = f"* [{md_escape_label(title)}]({md_escape_link(link)})"
    tail = " - ".join(md_escape_text(x) for x in (extra, description) if x)
    return f"{parts} - {tail}" if tail else parts


def _display_title(doc: Doc) -> str:
    title = doc.title
    if doc.status == "draft":
        title += " (draft)"
    return title


def build_index_block(bundle: Bundle, directory: Path) -> str:
    """1 ディレクトリ分の自動生成ブロック（マーカーの内側）を作る。"""
    if directory.resolve() == bundle.backlog_dir().resolve():
        return build_backlog_block(bundle, directory)

    icfg = bundle.index_cfg
    sections: list[tuple[str, list[str]]] = []

    # サブディレクトリ（その index.md を 1 エントリとして表現する＝段階的開示）
    subdir_lines = []
    for sub in sorted(p for p in directory.iterdir() if p.is_dir()):
        if sub.name.startswith(("_", ".")) or bundle.is_excluded(sub):
            continue
        idx = sub / "index.md"
        # index.md が未生成でも同じ結果になるよう、既定値は render_index の見出しと揃える
        title = f"{sub.name}{icfg.get('heading_suffix', ' ドキュメント')}"
        if idx.exists():
            doc = Doc(idx, bundle.root)
            title = doc.h1 or title
        link = "/" + rel_posix(idx, bundle.root)
        subdir_lines.append(_entry_line(title, link, ""))
    if subdir_lines:
        sections.append((str(icfg.get("subdir_section", "ディレクトリ")), sorted(subdir_lines)))

    # 直下の非予約ファイル
    docs: list[Doc] = []
    for p in sorted(directory.iterdir()):
        if not (p.is_file() and p.suffix == ".md"):
            continue
        if p.name in bundle.reserved or bundle.is_excluded(p):
            continue
        docs.append(Doc(p, bundle.root))

    deprecated = [d for d in docs if d.status == "deprecated"]
    active = [d for d in docs if d.status != "deprecated"]

    def lines_for(items: list[Doc]) -> list[str]:
        items = sorted(items, key=lambda d: (d.title, d.bundle_rel))
        return [_entry_line(_display_title(d), d.bundle_rel, d.description) for d in items]

    for type_name in bundle.types:
        group = [d for d in active if d.type == type_name]
        if group:
            sections.append((type_name, lines_for(group)))

    others = [d for d in active if d.type not in bundle.types]
    if others:
        sections.append((str(icfg.get("other_section", "その他")), lines_for(others)))

    if deprecated:
        sections.append((str(icfg.get("deprecated_section", "非推奨")), lines_for(deprecated)))

    if not sections:
        return ""
    blocks = [f"## {name}\n" + "\n".join(lines) for name, lines in sections]
    return "\n\n".join(blocks) + "\n"


def build_backlog_block(bundle: Bundle, directory: Path) -> str:
    """backlog/index.md 用のブロック（state でグルーピング + 件数サマリ）。"""
    bcfg = bundle.backlog_cfg
    state_order = list(bcfg.get("state_order") or ["doing", "todo", "done", "dropped"])
    prio_order = list(bcfg.get("priorities") or ["high", "medium", "low"])

    docs = [
        Doc(p, bundle.root)
        for p in sorted(directory.iterdir())
        if p.is_file() and p.suffix == ".md" and p.name not in bundle.reserved and not bundle.is_excluded(p)
    ]

    by_state: dict[str, list[Doc]] = {s: [] for s in state_order}
    for d in docs:
        state = str(d.fm.get("state") or "todo")
        by_state.setdefault(state, []).append(d)

    # 件数サマリ表（doing / todo / done / dropped の順）
    summary = ["| state | 件数 |", "|---|---|"]
    for state in state_order:
        summary.append(f"| {state} | {len(by_state.get(state, []))} |")
    for state in sorted(by_state):
        if state not in state_order:
            summary.append(f"| {state} | {len(by_state[state])} |")

    def prio_key(d: Doc) -> tuple:
        prio = str(d.fm.get("priority") or "")
        rank = prio_order.index(prio) if prio in prio_order else len(prio_order)
        return (rank, d.title, d.bundle_rel)

    def meta(d: Doc) -> str:
        chips = [f"`{d.fm[k]}`" for k in ("priority", "effort") if d.fm.get(k)]
        return " ".join(chips)

    sections: list[str] = ["\n".join(summary)]
    for state in state_order + sorted(s for s in by_state if s not in state_order):
        items = by_state.get(state) or []
        if not items:
            continue
        if state == "done":
            items = sorted(
                items,
                key=lambda d: (extract_date(d.fm.get("done_at")) or "", d.title),
                reverse=True,
            )
            lines = [
                _entry_line(
                    _display_title(d),
                    d.bundle_rel,
                    d.description,
                    f"{extract_date(d.fm.get('done_at')) or '日付不明'} 完了",
                )
                for d in items
            ]
        else:
            items = sorted(items, key=prio_key)
            lines = [_entry_line(_display_title(d), d.bundle_rel, d.description, meta(d)) for d in items]
        sections.append(f"## {state}\n" + "\n".join(lines))

    return "\n\n".join(sections) + "\n"


def split_markers(text: str, start: str, end: str, where: str) -> tuple[str, str] | None:
    """自動生成マーカーを検証し、(前文, 後文) を返す。マーカーが無ければ None。

    許可するのは次の 2 通りだけ。それ以外は ``MarkerError`` にして
    **一切書き込まない**（壊れたまま実行し続けると内容が増殖するため）。

    * start / end がどちらも 0 個 → 末尾に新規追加（None を返す）
    * start / end がちょうど 1 個ずつで start が end より前 → その間を置換
    """
    n_start = text.count(start)
    n_end = text.count(end)
    if n_start == 0 and n_end == 0:
        return None
    if n_start == 1 and n_end == 1:
        i_start = text.index(start)
        i_end = text.index(end)
        if i_start < i_end:
            return text[:i_start], text[i_end + len(end):]
        raise MarkerError(
            f"{where}: 自動生成マーカーの順序が逆です（`{end}` が `{start}` より前にあります）。"
            " 手で修正してから再実行してください。"
        )
    if n_start == 0 or n_end == 0:
        missing, present = (start, end) if n_start == 0 else (end, start)
        raise MarkerError(
            f"{where}: 自動生成マーカー `{missing}` がありません（`{present}` は {max(n_start, n_end)} 個あります）。"
            " 片方だけのマーカーは自動修復できません。手で修正してから再実行してください。"
        )
    raise MarkerError(
        f"{where}: 自動生成マーカーが重複しています（start {n_start} 個 / end {n_end} 個）。"
        " 1 組だけ残るように手で修正してから再実行してください。"
    )


def render_index(bundle: Bundle, directory: Path, block: str) -> str:
    """既存 index.md のマーカー間だけを置換した全文を返す。"""
    icfg = bundle.index_cfg
    start = str(icfg.get("start_marker", "<!-- okf:auto:start -->"))
    end = str(icfg.get("end_marker", "<!-- okf:auto:end -->"))
    auto = f"{start}\n{block}{end}\n"

    index_path = directory / "index.md"
    is_root = directory.resolve() == bundle.root.resolve()

    if not index_path.exists():
        head = ""
        if is_root:
            head = f'---\nokf_version: "{icfg.get("okf_version", "0.2")}"\n---\n\n'
            heading = str(icfg.get("root_heading", "ドキュメント"))
        else:
            heading = f"{directory.name}{icfg.get('heading_suffix', ' ドキュメント')}"
        return f"{head}# {heading}\n\n{auto}"

    text = read_text(index_path)
    where = rel_posix(index_path, REPO_ROOT)
    parts = split_markers(text, start, end, where)
    if parts is not None:
        pre, post = parts
        return f"{pre}{auto[:-1]}{post}"
    # マーカーが無ければ末尾に追加する
    return text.rstrip("\n") + "\n\n" + auto


def _plan_index(bundle: Bundle) -> tuple[list[tuple[Path, str]], list[MarkerError]]:
    """全ディレクトリ分の生成結果と、マーカー破損エラーをまとめて返す。"""
    plan: list[tuple[Path, str]] = []
    errors: list[MarkerError] = []
    for directory in bundle.dirs():
        try:
            block = build_index_block(bundle, directory)
            content = render_index(bundle, directory, block)
        except MarkerError as exc:
            errors.append(exc)
            continue
        plan.append((directory / "index.md", content))
    return plan, errors


def cmd_index(bundle: Bundle, args) -> int:
    plan, marker_errors = _plan_index(bundle)
    if marker_errors:
        # 1 件でも壊れていたら「どのファイルも書かない」。
        print("index.md の自動生成マーカーが壊れています。書き込みを中止しました:", file=sys.stderr)
        for exc in marker_errors:
            print(f"  {exc}", file=sys.stderr)
        return 1

    changed: list[str] = []
    for index_path, content in plan:
        current = read_text(index_path) if index_path.exists() else None
        if current == content:
            continue
        changed.append(rel_posix(index_path, REPO_ROOT))
        if args.write:
            write_if_changed(index_path, content)

    if args.check:
        if changed:
            print("index.md が最新ではありません:")
            for path in changed:
                print(f"  {path}")
            return 1
        if not args.quiet:
            print("index.md はすべて最新です。")
        return 0

    if changed:
        verb = "更新しました" if args.write else "更新が必要です（--write で書き込み）"
        print(f"index.md を {len(changed)} 件 {verb}:")
        for path in changed:
            print(f"  {path}")
    elif not args.quiet:
        print("index.md はすべて最新です。")
    return 0


# =============================================================================
# log コマンド
# =============================================================================


class Commit:
    def __init__(self, sha: str, short: str, date: str, subject: str, paths: list[str]):
        self.sha = sha          # full SHA（既出判定に使う）
        self.short = short      # 短縮ハッシュ（log.md への出力に使う）
        self.date = date
        self.subject = subject
        self.paths = paths


def collect_commits(rev_range: str | None, exclude: str | None = None) -> list[Commit]:
    """git 履歴からコミットを収集する。

    既定では `--first-parent`。これは「マージコミットを 1 件に畳む」という意味で
    あって「PR 単位」を保証するものではない（main への直接コミットもそのまま
    1 件として現れる）。
    """
    if not git_available():
        raise OkfError("git リポジトリが見つかりません。リポジトリ内で実行してください。")
    if not has_commits():
        return []
    args = [
        "log",
        "--first-parent",
        "-z",
        "--pretty=format:@@@%H\t%h\t%cs\t%s",
        "--name-status",
    ]
    # 除外だけを渡すと git は「positive ref なし」とみなして何も返さないため、
    # 範囲未指定のときは明示的に HEAD を positive ref にする。
    args.append(rev_range if rev_range else "HEAD")
    if exclude:
        args.append(f"^{exclude}")
    code, out = git(*args)
    if code != 0:
        raise OkfError(
            "git log の実行に失敗しました"
            + (f"（範囲: {rev_range}）" if rev_range else "")
            + "。リビジョン指定と git リポジトリの状態を確認してください。"
        )
    commits: list[Commit] = []
    for fields, changes in _parse_log_z(out, 4):
        sha, short, date, subject = fields[0], fields[1], fields[2], fields[3]
        if not sha:
            continue
        paths = [p for _status, p in changes]
        commits.append(Commit(sha, short, date, subject, paths))
    return commits


def layer_of(bundle: Bundle, path: str) -> str | None:
    """変更パスから層を判定する。skip / 未マッチは None。"""
    for rule in bundle.cfg.get("layer_map") or []:
        if not isinstance(rule, dict):
            continue
        if path_matches(path, str(rule.get("glob", ""))):
            layer = str(rule.get("layer", ""))
            return None if layer == "skip" else layer
    return None


def kind_of(bundle: Bundle, subject: str) -> str:
    """コミット subject から log.md のプレフィックスを推定する。"""
    for rule in bundle.cfg.get("kind_rules") or []:
        if not isinstance(rule, dict):
            continue
        if re.search(str(rule.get("pattern", "")), subject, re.IGNORECASE):
            return str(rule.get("kind", "**Update**"))
    return "**Update**"


def format_log_line(bundle: Bundle, commit: Commit, web_url: str | None) -> str:
    """OKF v0.2 §9 準拠の 1 エントリを組み立てる。"""
    subject = commit.subject.strip()
    pr = None
    m = re.search(r"\s*\(#(\d+)\)\s*$", subject)
    if m:
        pr = m.group(1)
        subject = subject[: m.start()].strip()
    if subject and subject[-1] not in "。．.!?！？":
        subject += "。"
    refs = []
    if pr and web_url:
        refs.append(f"[#{pr}]({web_url}/pull/{pr})")
    elif pr:
        refs.append(f"#{pr}")
    refs.append(f"`{commit.short or commit.sha[:7]}`")
    return f"- {kind_of(bundle, subject)} {subject} ({', '.join(refs)})"


ENTRY_RE = re.compile(r"^\s*-\s+\S")
HASH_RE = re.compile(r"`([0-9a-f]{7,40})`")


def recorded_hashes(text: str) -> set[str]:
    return set(HASH_RE.findall(text))


def hashless_entries(text: str) -> list[str]:
    """コミットハッシュを持たない既存エントリ行を返す（移行済みの手書き分）。"""
    out = []
    for line in text.split("\n"):
        if ENTRY_RE.match(line) and not HASH_RE.search(line):
            out.append(line.strip())
    return out


def insert_log_entries(text: str, entries_by_date: dict[str, list[str]]) -> str:
    """日付見出し（新しい順）を保ちながらエントリを差し込む。"""
    lines = text.split("\n")
    heading_re = re.compile(r"^##\s+(\d{4}-\d{2}-\d{2})\s*$")
    for date in sorted(entries_by_date, reverse=True):
        block = entries_by_date[date]
        pos = None
        for i, line in enumerate(lines):
            m = heading_re.match(line)
            if m and m.group(1) == date:
                pos = i + 1
                break
        if pos is not None:
            lines[pos:pos] = block  # 同一日付の先頭に追記
            continue
        insert_at = None
        for i, line in enumerate(lines):
            m = heading_re.match(line)
            if m and m.group(1) < date:
                insert_at = i
                break
        new_block = [f"## {date}", *block, ""]
        if insert_at is None:
            while lines and lines[-1].strip() == "":
                lines.pop()
            lines.extend(["", *new_block[:-1]])
        else:
            lines[insert_at:insert_at] = new_block
    out = "\n".join(lines).rstrip("\n") + "\n"
    return out


def log_baseline_sha(bundle: Bundle) -> str | None:
    """`log.baseline` を full SHA に解決する。未設定なら None。"""
    raw = bundle.log_cfg.get("baseline")
    if raw is None:
        return None
    ref = str(raw).strip()
    if not ref:
        return None
    sha = resolve_commit(ref)
    if sha is None:
        raise OkfError(
            f"config.yml の log.baseline を解決できません: {ref}"
            "（既存のコミットを指定するか、値を空にしてください）"
        )
    return sha


def cmd_log(bundle: Bundle, args) -> int:
    if not git_available():
        raise OkfError("git リポジトリが見つかりません。リポジトリ内で実行してください。")
    if not has_commits():
        print("コミットがまだありません（log.md には何も追記しません）。")
        return 0
    if is_shallow():
        print(
            "[okf log] 警告: shallow clone です。取得済みの範囲しか走査できないため、"
            "古いコミットが log.md に反映されない可能性があります"
            "（`git fetch --unshallow` を検討してください）。",
            file=sys.stderr,
        )

    baseline = log_baseline_sha(bundle)
    web_url = repo_web_url()
    commits = collect_commits(args.range, exclude=baseline)
    target_layers = [args.layer] if args.layer else bundle.log_layers()
    if args.layer and args.layer not in bundle.layers:
        raise OkfError(f"`--layer {args.layer}` は語彙表にありません（{', '.join(bundle.layers)}）")

    # baseline 未設定でハッシュ無しの既存エントリがあると、移行済みの内容を
    # 二重に追記してしまう。--write は拒否し、まず --dry-run を促す。
    if args.write and baseline is None:
        blockers: list[str] = []
        for layer in target_layers:
            log_path = bundle.log_path(layer)
            if not log_path.exists():
                continue
            leftovers = hashless_entries(read_text(log_path))
            if leftovers:
                blockers.append(f"{rel_posix(log_path, REPO_ROOT)}（{len(leftovers)} 件）")
        if blockers:
            raise OkfError(
                "config.yml の log.baseline が未設定で、コミットハッシュを持たない既存エントリがあります: "
                + " / ".join(blockers)
                + "。同じ変更を二重に追記する恐れがあるため書き込みを中止しました。"
                " `okf log --dry-run` で内容を確認し、"
                " config.yml の log.baseline に移行済みのコミットを設定してください。"
            )

    results: list[str] = []
    changed = 0
    for layer in target_layers:
        log_path = bundle.log_path(layer)
        existing = read_text(log_path) if log_path.exists() else ""
        recorded = recorded_hashes(existing)

        entries_by_date: dict[str, list[str]] = {}
        added = 0
        for commit in commits:
            # 記録済み判定は full SHA を正として prefix 照合する
            # （短縮ハッシュ同士の prefix 比較だと別コミットを既出扱いしうる）
            if any(commit.sha.startswith(h) for h in recorded):
                continue
            layers = {layer_of(bundle, p) for p in commit.paths}
            layers.discard(None)
            if layer not in layers:
                continue
            entries_by_date.setdefault(commit.date, []).append(
                format_log_line(bundle, commit, web_url)
            )
            added += 1

        if not added:
            continue

        if not existing:
            heading = str(bundle.log_cfg.get("heading_prefix", "変更履歴 — "))
            existing = f"# {heading}{layer}\n"
        content = insert_log_entries(existing, entries_by_date)

        rel = rel_posix(log_path, REPO_ROOT)
        results.append(f"{rel}: {added} 件")
        if args.dry_run:
            print(f"--- {rel} (dry-run) ---")
            for date in sorted(entries_by_date, reverse=True):
                print(f"## {date}")
                for line in entries_by_date[date]:
                    print(line)
            print()
        elif args.write:
            if write_if_changed(log_path, content):
                changed += 1

    if not results:
        print("log.md に追記すべき変更はありません。")
        return 0
    if args.write:
        print(f"log.md を更新しました（{changed} ファイル）:")
    elif not args.dry_run:
        print("追記対象（--write で書き込み / --dry-run で内容確認）:")
    for line in results:
        print(f"  {line}")
    return 0


# =============================================================================
# lint コマンド
# =============================================================================

ACTOR_RE = re.compile(r"^(?:human:\S+|process:\S+|[^\s/]+/[^\s/]+)$")

# 文末記号。`.` `!` `?` は後ろが空白 or 行末のときだけ文末とみなす（`v1.0` 対策）
SENTENCE_END_RE = re.compile(r"[。！？]|[.!?](?=\s|$)")


class Finding:
    def __init__(self, path: str, line: int | None, level: str, rule: str, message: str):
        self.path = path
        self.line = line
        self.level = level
        self.rule = rule
        self.message = message

    def __str__(self) -> str:
        loc = f"{self.path}:{self.line}" if self.line else self.path
        return f"{loc} {self.level} {self.rule} {self.message}"


def _check_actor_entry(entry, label: str) -> str | None:
    """`{by, at}` 形式の Actor エントリを検証し、問題があればメッセージを返す。"""
    if not isinstance(entry, dict):
        return f"`{label}` はマップ（`by` / `at`）である必要があります"
    by = entry.get("by")
    if not isinstance(by, str) or not ACTOR_RE.match(by.strip()):
        return f"`{label}.by: {by!r}` は Actor 表記（producer/version, human:, process:）ではありません"
    at = entry.get("at")
    if at is not None:
        parsed, _ = parse_datetime(at)
        if parsed is None:
            return f"`{label}.at: {at!r}` は ISO 8601 ではありません"
    return None


def trust_level(doc: Doc) -> str:
    """`verified` の内容から信頼度を返す（CONVENTIONS.md §1-3）。"""
    verified = doc.fm.get("verified")
    if not isinstance(verified, list) or not verified:
        return "unverified"
    actors = []
    for item in verified:
        if isinstance(item, dict) and isinstance(item.get("by"), str):
            actors.append(item["by"].strip())
    if not actors:
        return "unverified"
    if any(a.startswith("human:") for a in actors):
        return "human-reviewed"
    return "machine-confirmed"


def run_lint(bundle: Bundle) -> list[Finding]:
    """CONVENTIONS.md §10 の L1〜L13 を検証する。"""
    findings: list[Finding] = []
    add = findings.append

    # --- L1〜L6, L9〜L12: 非予約ドキュメント ---
    for doc in bundle.docs():
        path = doc.repo_rel
        if not doc.has_fm or doc.fm_error:
            reason = doc.fm_error or "frontmatter がありません"
            add(Finding(path, 1, "error", "L1", f"frontmatter を読めません: {reason}"))
            continue

        if not doc.type:
            add(Finding(path, doc.key_line("type"), "error", "L2", "`type` が空です"))
        elif doc.type not in bundle.types:
            add(Finding(path, doc.key_line("type"), "error", "L3",
                        f"`type: {doc.type}` は語彙表にありません（CONVENTIONS.md §2）"))

        if "status" in doc.fm and doc.fm.get("status") is not None:
            raw_status = doc.fm.get("status")
            if not isinstance(raw_status, str) or raw_status.strip() not in bundle.statuses:
                add(Finding(path, doc.key_line("status"), "error", "L4",
                            f"`status: {raw_status!r}` は {'/'.join(bundle.statuses)} "
                            "のいずれか（文字列）にしてください"))

        layer = doc.fm.get("layer")
        if not isinstance(layer, str) or layer.strip() not in bundle.layers:
            add(Finding(path, doc.key_line("layer"), "error", "L5",
                        f"`layer` は {'/'.join(bundle.layers)} のいずれかが必要です（現在: {layer!r}）"))

        if "generated" in doc.fm and doc.fm.get("generated") is not None:
            problem = _check_actor_entry(doc.fm.get("generated"), "generated")
            if problem:
                add(Finding(path, doc.key_line("generated"), "warn", "L6", problem))

        if "verified" in doc.fm and doc.fm.get("verified") is not None:
            verified = doc.fm.get("verified")
            if not isinstance(verified, list):
                add(Finding(path, doc.key_line("verified"), "warn", "L6",
                            f"`verified` はリストである必要があります（現在: {type(verified).__name__}）"))
            elif not verified:
                add(Finding(path, doc.key_line("verified"), "warn", "L6", "`verified` が空配列です"))
            else:
                for pos, item in enumerate(verified, start=1):
                    problem = _check_actor_entry(item, f"verified[{pos}]")
                    if problem:
                        add(Finding(path, doc.key_line("verified"), "warn", "L6", problem))

        desc = doc.description
        if desc:
            if len(SENTENCE_END_RE.findall(desc)) > 1:
                add(Finding(path, doc.key_line("description"), "warn", "L9",
                            "`description` は一文にしてください（文末記号が 2 つ以上あります）"))
            if len(desc) > 120:
                add(Finding(path, doc.key_line("description"), "warn", "L9",
                            f"`description` が 120 字を超えています（{len(desc)} 字）"))

        for problem in doc.code_globs_problems():
            add(Finding(path, doc.key_line("code_globs"), "error", "L10", problem))

        globs = doc.code_globs()
        if not globs and doc.requires_code_globs():
            add(Finding(path, doc.key_line("type"), "warn", "L10",
                        f"`code_globs` がありません（type: {doc.type} はコード由来なので更新検知の起点が必要です）"))

        for pattern in globs:
            if not resolve_resource(pattern):
                add(Finding(path, doc.key_line("code_globs"), "warn", "L10",
                            f"`code_globs: {pattern}` にマッチするファイルがありません"))

        for problem in doc.source_problems():
            add(Finding(path, doc.key_line("sources"), "warn", "L14", problem))

        related = doc.fm.get("related")
        if related is not None and not isinstance(related, list):
            add(Finding(path, doc.key_line("related"), "warn", "L11",
                        f"`related` はリストである必要があります（現在: {type(related).__name__}）"))
        elif isinstance(related, list):
            for link in related:
                if not isinstance(link, str) or not link.strip():
                    add(Finding(path, doc.key_line("related"), "warn", "L11",
                                f"`related` の要素が文字列ではありません: {link!r}"))
                    continue
                target = link.split("#", 1)[0].strip()
                if not target or target.startswith(("http://", "https://")):
                    continue
                base = bundle.root if target.startswith("/") else doc.path.parent
                candidate = (base / target.lstrip("/")).resolve()
                try:
                    candidate.relative_to(bundle.root.resolve())
                except ValueError:
                    add(Finding(path, doc.key_line("related"), "warn", "L11",
                                f"`related` はバンドル（{rel_posix(bundle.root, REPO_ROOT)}/）内を"
                                f"指す必要があります: {link}"))
                    continue
                if not candidate.exists():
                    add(Finding(path, doc.key_line("related"), "warn", "L11",
                                f"`related` のリンク先が存在しません: {link}"))

        if doc.type == "Backlog Item":
            states = list(bundle.backlog_cfg.get("states") or [])
            state = doc.fm.get("state")
            if not isinstance(state, str) or state.strip() not in states:
                add(Finding(path, doc.key_line("state"), "error", "L12",
                            f"`state` は {'/'.join(states)} のいずれかが必要です（現在: {state!r}）"))
            elif state.strip() == "done":
                done_at = doc.fm.get("done_at")
                if not is_iso_date(done_at if isinstance(done_at, str) else str(done_at or "")):
                    add(Finding(path, doc.key_line("done_at"), "error", "L12",
                                f"`state: done` には `done_at: YYYY-MM-DD`（実在する日付）が必要です"
                                f"（現在: {done_at!r}）"))

    # --- L7: 予約ファイルの frontmatter（ルート index.md の okf_version のみ例外） ---
    for directory in bundle.dirs():
        index_path = directory / "index.md"
        if index_path.exists():
            doc = Doc(index_path, bundle.root)
            rel = doc.repo_rel
            is_root = directory.resolve() == bundle.root.resolve()
            if doc.fm_opened and not doc.has_fm:
                add(Finding(rel, 1, "error", "L7",
                            f"index.md の frontmatter が壊れています: {doc.fm_error}"))
            elif doc.has_fm and doc.fm_error:
                add(Finding(rel, 1, "error", "L7",
                            f"index.md の frontmatter を読めません: {doc.fm_error}"))
            elif doc.has_fm and not (is_root and set(doc.fm.keys()) <= {"okf_version"}):
                add(Finding(rel, 1, "error", "L7",
                            "index.md は frontmatter を持てません（ルートの `okf_version` のみ例外）"))

        log_path = directory / "log.md"
        if log_path.exists():
            log_doc = Doc(log_path, bundle.root)
            if log_doc.fm_opened:
                add(Finding(log_doc.repo_rel, 1, "error", "L7",
                            "log.md は frontmatter を持てません（OKF v0.2 §8 の予約ファイル）"))

    # --- L8: log.md の日付見出し ---
    for directory in bundle.dirs():
        log_path = directory / "log.md"
        if not log_path.exists():
            continue
        rel = rel_posix(log_path, REPO_ROOT)
        prev: str | None = None
        seen: dict[str, int] = {}
        for no, line in enumerate(read_text(log_path).split("\n"), start=1):
            if not line.startswith("## "):
                continue
            heading = line[3:].strip()
            if not is_iso_date(heading):
                add(Finding(rel, no, "warn", "L8",
                            f"見出しが ISO 8601 の実在する日付ではありません: {heading}"))
                continue
            if heading in seen:
                add(Finding(rel, no, "warn", "L8",
                            f"日付見出しが重複しています: {heading}（{seen[heading]} 行目にもあります）"))
            else:
                seen[heading] = no
            if prev and heading > prev:
                add(Finding(rel, no, "warn", "L8",
                            f"日付見出しが新しい順になっていません: {prev} の後に {heading}"))
            prev = heading

    # --- L13: index.md が最新か ---
    for directory in bundle.dirs():
        index_path = directory / "index.md"
        try:
            block = build_index_block(bundle, directory)
            content = render_index(bundle, directory, block)
        except MarkerError as exc:
            add(Finding(rel_posix(index_path, REPO_ROOT), None, "error", "L13", str(exc)))
            continue
        current = read_text(index_path) if index_path.exists() else None
        if current != content:
            add(Finding(rel_posix(index_path, REPO_ROOT), None, "error", "L13",
                        "index.md が最新ではありません（`okf index --write` を実行してください）"))

    findings.sort(key=lambda f: (f.path, f.line or 0, f.rule))
    return findings


def cmd_lint(bundle: Bundle, args) -> int:
    findings = run_lint(bundle)
    for finding in findings:
        print(finding)
    errors = sum(1 for f in findings if f.level == "error")
    warns = sum(1 for f in findings if f.level == "warn")
    print(f"\nlint: error {errors} 件 / warn {warns} 件")
    if errors:
        return 1
    if warns and getattr(args, "strict", False):
        return 1
    return 0


# =============================================================================
# stale コマンド
# =============================================================================


def run_stale(bundle: Bundle) -> list[dict]:
    """陳腐化レポートを組み立てる。"""
    results: list[dict] = []
    draft_days = int((bundle.cfg.get("stale") or {}).get("draft_days", 30))
    todays = today()

    for doc in bundle.docs():
        if not doc.has_fm:
            continue
        path = doc.repo_rel
        generated = doc.fm.get("generated")
        gen_raw = generated.get("at") if isinstance(generated, dict) else None
        gen_dt, gen_has_time = parse_datetime(gen_raw)
        gen_at = extract_date(gen_raw)

        stale_after = extract_date(doc.fm.get("stale_after"))
        if stale_after and stale_after <= todays.isoformat():
            results.append({"path": path, "kind": "expired", "level": "warn",
                            "message": f"stale_after: {stale_after} を過ぎています"})

        for resource in doc.code_globs():
            matched = resolve_resource(resource)
            if not matched:
                results.append({"path": path, "kind": "orphan", "level": "warn",
                                "message": f"code_globs: {resource} にマッチするファイルがありません"})
                continue
            if gen_dt is None:
                continue
            latest_raw = last_commit_time(matched)
            if not latest_raw:
                continue
            latest_dt, _ = parse_datetime(latest_raw)
            if latest_dt is None:
                continue
            if gen_has_time:
                outdated = latest_dt > gen_dt
                shown = latest_dt.astimezone(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            else:
                # generated.at が日付のみのときは日単位で比較する（誤検知を避ける）
                outdated = latest_dt.date() > gen_dt.date()
                shown = latest_dt.date().isoformat()
            if outdated:
                results.append({"path": path, "kind": "outdated", "level": "warn",
                                "message": f"{resource} の最終コミット {shown} > generated.at {gen_raw}"})

        if trust_level(doc) == "unverified":
            results.append({"path": path, "kind": "unverified", "level": "info",
                            "message": "verified がありません（人によるレビュー未実施）"})

        if doc.status == "draft" and gen_at:
            try:
                age = (todays - _dt.date.fromisoformat(gen_at)).days
            except ValueError:
                age = 0
            if age >= draft_days:
                results.append({"path": path, "kind": "draft-stale", "level": "info",
                                "message": f"status: draft のまま {age} 日経過しています"})

    results.sort(key=lambda r: (r["level"] != "warn", r["path"], r["kind"]))
    return results


def cmd_stale(bundle: Bundle, args) -> int:
    if git_available() and is_shallow():
        print(
            "[okf stale] 警告: shallow clone のため outdated 判定が不正確になる可能性があります。",
            file=sys.stderr,
        )
    results = run_stale(bundle)
    if args.format == "json":
        print(json.dumps(results, ensure_ascii=False, indent=2))
        return 0
    if not results:
        print("陳腐化の兆候はありません。")
        return 0
    for item in results:
        print(f"{item['path']} {item['level']} {item['kind']} {item['message']}")
    warns = sum(1 for r in results if r["level"] == "warn")
    infos = len(results) - warns
    print(f"\nstale: warn {warns} 件 / info {infos} 件")
    return 0


# =============================================================================
# affected コマンド
# =============================================================================


def changed_paths(base: str) -> list[str]:
    """base からの変更パス。未コミットの作業ツリー変更も含める。

    base は `<base>` → `origin/<base>` の順に解決し、HEAD との merge-base で
    比較する（detached HEAD やローカル ref が無い環境でも動くようにする）。
    """
    if not git_available():
        raise OkfError("git リポジトリが見つかりません。リポジトリ内で実行してください。")

    paths: set[str] = set()
    if has_commits():
        ref = resolve_ref(base)
        if ref is None:
            raise OkfError(
                f"base ref を解決できませんでした: {base}"
                f"（`{base}` も `origin/{base}` も存在しません。--base か --paths を指定してください）"
            )
        code, out = git("merge-base", ref, "HEAD")
        merge_base = out.strip() if code == 0 else ""
        if merge_base:
            code, out = git("diff", "--name-only", "-z", merge_base, "HEAD")
        else:
            # 履歴が交わらない（shallow / 別ルート）ときは直接比較にフォールバック
            code, out = git("diff", "--name-only", "-z", ref)
        if code != 0:
            raise OkfError(f"git diff に失敗しました（base: {base}）")
        paths.update(p.replace("\\", "/") for p in out.split("\0") if p.strip())
    else:
        print("[okf affected] コミットがまだないため、作業ツリーの変更のみを対象にします。",
              file=sys.stderr)

    code, out = git("status", "--porcelain", "-z", "--untracked-files=all")
    if code == 0:
        paths.update(parse_porcelain_z(out))
    return sorted(paths)


def compute_affected(bundle: Bundle, paths: list[str]) -> tuple[dict[str, list[str]], list[str]]:
    """変更パス → 更新すべきドキュメントの対応表と、未カバーのパスを返す。"""
    mapping: dict[str, list[str]] = {}
    covered: set[str] = set()
    for doc in bundle.docs():
        resources = doc.code_globs()
        if not resources:
            continue
        hits = []
        for path in paths:
            if any(path == r.lstrip("/") or path_matches(path, r.lstrip("/")) for r in resources):
                hits.append(path)
        if hits:
            mapping[doc.repo_rel] = sorted(set(hits))
            covered.update(hits)
    uncovered = sorted(p for p in paths if p not in covered)
    return mapping, uncovered


def cmd_affected(bundle: Bundle, args) -> int:
    paths = list(args.paths) if args.paths else changed_paths(args.base)
    # layer_map で skip 指定のパス（docs/** など）は対象外にする
    paths = [
        p.replace("\\", "/")
        for p in paths
        if not p.endswith("/") and layer_of(bundle, p.replace("\\", "/")) is not None
    ]
    if not paths:
        print("変更パスがありません。")
        return 0
    mapping, uncovered = compute_affected(bundle, paths)
    for doc_path in sorted(mapping):
        print(f"{doc_path}  <- {', '.join(mapping[doc_path])}")
    if not mapping:
        print("更新すべきドキュメントは見つかりませんでした。")
    if uncovered:
        print("\n未カバー:")
        for path in uncovered:
            print(f"  {path}")
    return 0


# =============================================================================
# new コマンド
# =============================================================================

SLUG_RE = re.compile(r"^[a-z0-9]+(?:[-.][a-z0-9]+)*$")


def slugify(title: str) -> str:
    """タイトルから ASCII の kebab-case slug を作る。作れなければ空文字。"""
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", title).strip("-").lower()
    return slug


def validate_slug(slug: str) -> str:
    if not SLUG_RE.match(slug):
        raise OkfError(
            f"slug は kebab-case（英小文字・数字・ハイフン）で指定してください: {slug!r}"
        )
    return slug


def validate_subdir(value: str) -> str:
    """`--dir` を検証する（相対・kebab-case・`..` 禁止）。"""
    normalized = value.replace("\\", "/").strip("/")
    if not normalized:
        raise OkfError("`--dir` が空です")
    if value.startswith(("/", "\\")) or re.match(r"^[A-Za-z]:", value):
        raise OkfError(f"`--dir` に絶対パスは指定できません: {value!r}")
    for part in normalized.split("/"):
        if part in ("", ".", ".."):
            raise OkfError(f"`--dir` に `.` / `..` は使えません: {value!r}")
        validate_slug(part)
    return normalized


def ensure_inside_bundle(bundle: Bundle, path: Path) -> Path:
    resolved = path.resolve()
    try:
        resolved.relative_to(bundle.root.resolve())
    except ValueError:
        raise OkfError(
            f"バンドル（{rel_posix(bundle.root, REPO_ROOT)}/）の外には作成できません: {resolved}"
        ) from None
    return resolved


def set_fm_field(text: str, key: str, value: str, parent: str | None = None) -> str:
    """frontmatter の 1 フィールドを置換する（parent 指定でネストしたキーに対応）。

    value は**すでに YAML としてシリアライズ済み**の文字列であること。
    """
    lines = text.split("\n")
    if not lines or lines[0].strip() != "---":
        return text
    end = next((i for i in range(1, len(lines)) if lines[i].strip() == "---"), None)
    if end is None:
        return text
    if parent is None:
        for i in range(1, end):
            if re.match(rf"^{re.escape(key)}\s*:", lines[i]):
                lines[i] = f"{key}: {value}"
                break
    else:
        in_parent = False
        for i in range(1, end):
            if re.match(rf"^{re.escape(parent)}\s*:", lines[i]):
                in_parent = True
                continue
            if in_parent:
                if not lines[i].startswith((" ", "\t")):
                    break
                if re.match(rf"^\s+{re.escape(key)}\s*:", lines[i]):
                    indent = lines[i][: len(lines[i]) - len(lines[i].lstrip())]
                    lines[i] = f"{indent}{key}: {value}"
                    break
    return "\n".join(lines)


def load_template(bundle: Bundle, type_name: str) -> str:
    templates = bundle.cfg.get("templates") or {}
    rel = templates.get(type_name)
    if not rel:
        raise OkfError(f"type '{type_name}' に対応するテンプレートが config.yml にありません")
    path = bundle.root / str(rel)
    if not path.exists():
        raise OkfError(f"テンプレートが見つかりません: {rel_posix(path, REPO_ROOT)}")
    return read_text(path)


def next_numbered_id(directory: Path, prefix: str = "") -> int:
    """`<prefix>NNNN-...` の最大値 + 1 を返す（prefix 無しは ADR 用）。"""
    pattern = rf"^{re.escape(prefix)}(\d{{4}})(?:-|\.md$)"
    max_id = 0
    if directory.exists():
        for p in directory.glob("*.md"):
            m = re.match(pattern, p.name)
            if m:
                max_id = max(max_id, int(m.group(1)))
    return max_id + 1


def next_backlog_id(bundle: Bundle) -> int:
    """既存の B-NNNN の最大値 + 1 を返す。"""
    prefix = str(bundle.backlog_cfg.get("prefix", "B"))
    return next_numbered_id(bundle.backlog_dir(), f"{prefix}-")


def _validate_vocab(value: str, allowed: list, label: str) -> str:
    if allowed and value not in allowed:
        raise OkfError(f"`{label} {value}` は語彙表にありません（{', '.join(str(a) for a in allowed)}）")
    return value


def cmd_new(bundle: Bundle, args) -> int:
    if "\n" in args.title or "\r" in args.title:
        raise OkfError("`--title` に改行は使えません")
    _validate_vocab(args.layer, bundle.layers, "--layer")

    if args.kind == "backlog":
        _validate_vocab(args.priority, list(bundle.backlog_cfg.get("priorities") or []), "--priority")
        _validate_vocab(args.effort, list(bundle.backlog_cfg.get("efforts") or []), "--effort")
        text = load_template(bundle, "Backlog Item")
        number = next_backlog_id(bundle)
        prefix = str(bundle.backlog_cfg.get("prefix", "B"))
        slug = validate_slug(args.slug) if args.slug else slugify(args.title)
        name = f"{prefix}-{number:04d}-{slug}.md" if slug else f"{prefix}-{number:04d}.md"
        out_path = bundle.backlog_dir() / name

        text = set_fm_field(text, "title", yaml_scalar(args.title))
        text = set_fm_field(text, "layer", yaml_scalar(args.layer))
        text = set_fm_field(text, "tags", yaml_flow_list([args.layer]))
        text = set_fm_field(text, "state", yaml_scalar("todo"))
        text = set_fm_field(text, "priority", yaml_scalar(args.priority))
        text = set_fm_field(text, "effort", yaml_scalar(args.effort))
        text = set_fm_field(text, "created", yaml_scalar(today().isoformat()))
        text = set_fm_field(text, "by", yaml_scalar("process:okf-cli"), parent="generated")
        text = set_fm_field(text, "at", yaml_scalar(now_iso()), parent="generated")
    else:
        _validate_vocab(args.type, bundle.types, "--type")
        text = load_template(bundle, args.type)
        slug = validate_slug(args.slug) if args.slug else slugify(args.title)
        if not slug:
            raise OkfError("タイトルから slug を生成できませんでした。`--slug <kebab-case>` を指定してください。")
        layer_dirs = bundle.cfg.get("layer_dirs") or {}
        base = bundle.root / str(layer_dirs.get(args.layer, args.layer))
        if args.dir:
            base = base / validate_subdir(args.dir)
        filename = f"{slug}.md"
        if args.type == "Decision Record":
            # ADR は CONVENTIONS.md §8 に従い 4 桁連番を前置する
            filename = f"{next_numbered_id(base):04d}-{slug}.md"
        out_path = base / filename

        text = set_fm_field(text, "type", yaml_scalar(args.type))
        text = set_fm_field(text, "title", yaml_scalar(args.title))
        text = set_fm_field(text, "layer", yaml_scalar(args.layer))
        text = set_fm_field(text, "by", yaml_scalar("process:okf-cli"), parent="generated")
        text = set_fm_field(text, "at", yaml_scalar(now_iso()), parent="generated")

    out_path = ensure_inside_bundle(bundle, out_path)
    text = re.sub(r"^#\s+<[^>\n]*>\s*$", f"# {args.title}", text, count=1, flags=re.MULTILINE)

    if out_path.exists():
        raise OkfError(f"既に存在します: {rel_posix(out_path, REPO_ROOT)}")
    write_if_changed(out_path, text)
    print(rel_posix(out_path, REPO_ROOT))
    return 0


# =============================================================================
# status コマンド
# =============================================================================


def backlog_docs(bundle: Bundle) -> list[Doc]:
    directory = bundle.backlog_dir()
    if not directory.exists():
        return []
    return [
        Doc(p, bundle.root)
        for p in sorted(directory.iterdir())
        if p.is_file() and p.suffix == ".md" and p.name not in bundle.reserved
    ]


def cmd_status(bundle: Bundle, args) -> int:
    docs = backlog_docs(bundle)
    states = list(bundle.backlog_cfg.get("state_order") or ["doing", "todo", "done", "dropped"])
    priorities = list(bundle.backlog_cfg.get("priorities") or ["high", "medium", "low"])

    by_state: dict[str, list[Doc]] = {s: [] for s in states}
    for doc in docs:
        by_state.setdefault(str(doc.fm.get("state") or "todo"), []).append(doc)

    priority_counts = {
        state: {p: sum(1 for d in items if str(d.fm.get("priority") or "") == p) for p in priorities}
        for state, items in by_state.items()
    }

    if args.format == "json":
        payload = {
            "total": len(docs),
            "states": {s: len(v) for s, v in by_state.items()},
            "priorities": priority_counts,
            "doing": [{"path": d.repo_rel, "title": d.title,
                       "priority": d.fm.get("priority"), "effort": d.fm.get("effort")}
                      for d in by_state.get("doing", [])],
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    print(f"backlog: 全 {len(docs)} 件")
    for state in states + sorted(s for s in by_state if s not in states):
        items = by_state.get(state) or []
        detail = " ".join(f"{p}:{priority_counts.get(state, {}).get(p, 0)}" for p in priorities)
        print(f"  {state:<8} {len(items):>3} 件  ({detail})")
    doing = by_state.get("doing") or []
    if doing:
        print("\ndoing:")
        for doc in doing:
            chips = " ".join(f"`{doc.fm[k]}`" for k in ("priority", "effort") if doc.fm.get(k))
            print(f"  - {doc.title} {chips} ({doc.repo_rel})")
    return 0


# =============================================================================
# HTML レンダリング
# =============================================================================


def cmd_render(bundle: Bundle, args) -> int:
    """Bundle 対象の Markdown を、AI を使わず閲覧用 HTML に変換する。"""
    try:
        from .renderer import RenderError, render_bundle
    except ImportError as exc:  # pragma: no cover - 壊れたインストール向け
        raise OkfError(f"HTML レンダラーを読み込めません: {exc}") from exc

    output_root = None
    if args.output:
        output_root = (REPO_ROOT / args.output).resolve()
        try:
            output_root.relative_to(REPO_ROOT.resolve())
        except ValueError as exc:
            raise OkfError("HTML の出力先はリポジトリ内に指定してください") from exc

    try:
        report = render_bundle(
            bundle,
            Doc,
            output_root,
            write=not args.check,
        )
    except RenderError as exc:
        raise OkfError(str(exc)) from exc

    if args.hook:
        # Codex / Claude の Stop hook は exit 0 時に JSON を要求する。
        # 追加コンテキストや block 指示は返さず、モデル継続を発生させない。
        print("{}")
        return 0

    for warning in report.warnings:
        print(f"warn: {warning}", file=sys.stderr)
    mode = "検証" if args.check else "生成"
    print(
        f"HTML {mode}: {report.pages} ページ / 書き込み {report.written} 件 / "
        f"削除 {report.removed} 件 / "
        f"warn {len(report.warnings)} 件 -> {report.output_root}"
    )
    return 0


# =============================================================================
# sync コマンド
# =============================================================================

STDIN_LIMIT = 1 << 20  # hook 入力の読み取り上限（1 MiB）
STDIN_TIMEOUT = 2.0    # 秒。EOF が来なくてもここで諦める（ハング防止）
GATE_TTL = 600         # session_id が無いときに同一セッションとみなす秒数


def gate_state_dir() -> Path:
    """gate 状態の保存先（git 管理外）。

    作業ツリーに置くと `.gitignore` 漏れで常に dirty になり、
    「変更が無ければ即終了」が機能しなくなるため git ディレクトリ配下に置く。
    """
    code, out = git("rev-parse", "--git-path", "okf-gate")
    if code == 0 and out.strip():
        path = Path(out.strip())
        if not path.is_absolute():
            path = REPO_ROOT / path
        return path
    return Path(tempfile.gettempdir()) / "okf-gate"


def _gate_state_file(session_id: str | None) -> Path:
    key = re.sub(r"[^A-Za-z0-9_.-]", "_", session_id or "")[:80] or "_nosession"
    return gate_state_dir() / f"{key}.json"


def _read_stdin_json(timeout: float = STDIN_TIMEOUT, limit: int = STDIN_LIMIT) -> dict | None:
    """hook が stdin で渡す JSON を、ハングしない形で読む。

    `sys.stdin.read()` は EOF が来るまで無期限に待つため、別スレッドで
    サイズ上限付きに読み、タイムアウトしたら諦める（デーモンスレッドなので
    プロセス終了を妨げない）。
    """
    stream = getattr(sys.stdin, "buffer", sys.stdin)
    if stream is None:
        return None
    try:
        if sys.stdin.isatty():
            return None
    except Exception:
        return None

    box: dict = {}

    def worker() -> None:
        try:
            box["raw"] = stream.read(limit)
        except Exception:
            pass

    thread = threading.Thread(target=worker, daemon=True)
    thread.start()
    thread.join(timeout)
    raw = box.get("raw")
    if raw is None:
        return None
    if isinstance(raw, bytes):
        try:
            raw = raw.decode("utf-8", errors="replace")
        except Exception:
            return None
    if not raw.strip():
        return None
    try:
        data = json.loads(raw)
    except Exception:
        return None
    return data if isinstance(data, dict) else None


def resolve_session_id(args) -> str | None:
    """`--session-id` → 環境変数 → stdin JSON の順にセッション ID を決める。"""
    explicit = getattr(args, "session_id", None)
    if explicit:
        return str(explicit)
    for name in ("CLAUDE_SESSION_ID", "OKF_SESSION_ID"):
        value = os.environ.get(name)
        if value:
            return value
    payload = _read_stdin_json()
    if payload:
        value = payload.get("session_id")
        if value:
            return str(value)
    return None


def findings_fingerprint(findings: list[Finding]) -> str:
    """lint error 集合の指紋。内容が変われば別物として扱う。"""
    joined = "\n".join(sorted(str(f) for f in findings))
    return hashlib.sha256(joined.encode("utf-8")).hexdigest()[:32]


def gate_bump(session_id: str | None, fingerprint: str | None) -> int:
    """同じ error 集合に対して exit 2 を返した回数を数える。

    fingerprint が None（= error 無し）のときは状態をリセットして 0 を返す。
    """
    state_file = _gate_state_file(session_id)
    if fingerprint is None:
        try:
            state_file.unlink()
        except OSError:
            pass
        return 0

    prev: dict = {}
    same = False
    if state_file.exists():
        try:
            prev = json.loads(state_file.read_text(encoding="utf-8"))
        except Exception:
            prev = {}
        if isinstance(prev, dict) and prev.get("fingerprint") == fingerprint:
            if session_id:
                same = True
            else:
                try:
                    age = time.time() - state_file.stat().st_mtime
                except OSError:
                    age = GATE_TTL + 1
                same = age <= GATE_TTL
    count = int(prev.get("count", 0)) + 1 if same else 1
    payload = json.dumps(
        {"session_id": session_id, "fingerprint": fingerprint, "count": count, "at": now_iso()},
        ensure_ascii=False,
    )
    atomic_write_bytes(state_file, payload.encode("utf-8"))
    return count


def _has_local_changes() -> bool:
    code, out = git("status", "--porcelain")
    if code != 0:
        return True  # git が使えないときは判断できないので処理を続ける
    return bool(out.strip())


def cmd_sync(bundle: Bundle, args) -> int:
    session_id = resolve_session_id(args) if args.gate else None

    if args.gate and not _has_local_changes():
        return 0  # docs もコードも変更が無ければ何もしない

    print("== index ==")
    index_args = argparse.Namespace(write=True, check=False, quiet=False)
    index_rc = cmd_index(bundle, index_args)

    print("\n== log ==")
    log_args = argparse.Namespace(write=True, range=None, layer=None, dry_run=False)
    try:
        cmd_log(bundle, log_args)
    except OkfError as exc:
        # log の失敗（baseline 未設定など）で sync 全体を落とさない。
        print(f"[okf log] スキップしました: {exc}", file=sys.stderr)
    if _has_local_changes():
        # log の入力はコミット履歴だけなので、未コミットの作業は反映されない。
        print(
            "[okf log] 未コミットの変更があります。今回の作業分の log.md エントリは"
            "コミット後に `okf log --write` を実行して生成してください。",
            file=sys.stderr,
        )

    print("\n== lint ==")
    bundle._docs = None  # index / log の書き込み結果を反映させる
    findings = run_lint(bundle)
    for finding in findings:
        print(finding)
    errors = [f for f in findings if f.level == "error"]
    warns = [f for f in findings if f.level == "warn"]
    print(f"lint: error {len(errors)} 件 / warn {len(warns)} 件")

    print("\n== stale ==")
    results = run_stale(bundle)
    if not results:
        print("陳腐化の兆候はありません。")
    for item in results:
        print(f"{item['path']} {item['level']} {item['kind']} {item['message']}")

    if not args.gate:
        return 1 if (errors or index_rc != 0) else 0

    count = gate_bump(session_id, findings_fingerprint(errors) if errors else None)
    if not errors:
        return 0
    if count >= 2:
        print(
            f"[okf gate] lint error が {len(errors)} 件残っていますが、"
            "同じ内容で 2 回目の差し戻しになるため警告のみとします。",
            file=sys.stderr,
        )
        return 0
    lines = [
        "[okf gate] ドキュメントの規約違反があります。次を修正してから終了してください。",
        "",
    ]
    lines += [f"  {f}" for f in errors]
    lines += [
        "",
        "修正の手順:",
        "  1. 上記ファイルの frontmatter / 本文を修正する",
        "  2. okf lint で解消を確認する",
    ]
    print("\n".join(lines), file=sys.stderr)
    return 2


# =============================================================================
# init
# =============================================================================


def _scaffold_text(rel: str) -> str:
    path = SCAFFOLD_DIR / rel
    if not path.is_file():  # pragma: no cover - 壊れたインストール向け
        raise OkfError(f"scaffold が見つかりません: {path}")
    return path.read_text(encoding="utf-8").replace("\r\n", "\n")


def _parse_layer_specs(specs: list[str] | None) -> list[tuple[str, str, str]]:
    """``--layer name=glob[:dir]`` を (name, glob, dir) に分解する。

    ``glob`` は「その層に属するコードのパス」で、log の振り分けと affected の
    起点になる。``dir`` 省略時は層名をそのままバンドル内のディレクトリ名に使う。
    """
    parsed: list[tuple[str, str, str]] = []
    seen: set[str] = set()
    for spec in specs or []:
        name, sep, rest = spec.partition("=")
        name = name.strip()
        if not sep or not name or not rest.strip():
            raise OkfError(f"--layer の書式が不正です（name=glob[:dir]）: {spec}")
        glob_part, _, dir_part = rest.partition(":")
        glob_part = glob_part.strip()
        dir_part = dir_part.strip() or name
        if not re.fullmatch(r"[a-z0-9][a-z0-9_-]*", name):
            raise OkfError(f"層名は英小文字・数字・- _ のみ使えます: {name}")
        if name in seen:
            raise OkfError(f"層名が重複しています: {name}")
        if name == "shared":
            raise OkfError("`shared` は層をまたぐ知識用に予約されています")
        if dir_part.startswith((".", "/")) or ".." in dir_part.split("/"):
            raise OkfError(f"層のディレクトリが不正です: {dir_part}")
        seen.add(name)
        parsed.append((name, glob_part, dir_part))
    return parsed


def _render_okf_yml(
    bundle_root: str, site_name: str, layers: list[tuple[str, str, str]]
) -> str:
    """``okf.yml`` を組み立てる。値はすべて ``yaml_scalar`` で安全に引用する。"""
    names = [name for name, _glob, _dir in layers]

    layer_lines = [f"  - {yaml_scalar(n)}" for n in names] + ["  - shared"]
    dir_lines = [f"  {n}: {yaml_scalar(d)}" for n, _g, d in layers]
    dir_lines.append("  shared: project")
    map_lines = [
        f"  - {{ glob: {yaml_scalar(g)}, layer: {yaml_scalar(n)} }}"
        for n, g, _d in layers
    ]
    map_lines.append(f"  - {{ glob: {yaml_scalar(bundle_root + chr(47) + chr(42) * 2)}, layer: skip }}")
    map_lines.append('  - { glob: "**", layer: shared }')
    # log.paths は log: > paths: の下なのでインデントは4スペース
    log_path_lines = [f"    {n}: {yaml_scalar(d + '/log.md')}" for n, _g, d in layers]
    log_path_lines.append("    shared: log.md")

    return _scaffold_text("okf.yml.tmpl").format(
        bundle_root=yaml_scalar(bundle_root),
        site_name=yaml_scalar(site_name),
        root_heading=yaml_scalar(f"{site_name} ドキュメント"),
        layers="\n".join(layer_lines),
        layer_dirs="\n".join(dir_lines),
        layer_map="\n".join(map_lines),
        log_layers=("[" + ", ".join(names) + "]") if names else "[]",
        log_paths="\n".join(log_path_lines),
    )


def cmd_init(args) -> int:
    """リポジトリに OKF バンドルと設定一式を生成する。"""
    layers = _parse_layer_specs(args.layer)
    raw = args.bundle_root if args.bundle_root is not None else "docs"
    bundle_root = raw.strip().replace("\\", "/")
    # 末尾スラッシュを落とす前に判定する（"/abs" が "abs" に化けるのを防ぐ）。
    if bundle_root.startswith(("/", ".")) or ":" in bundle_root:
        raise OkfError(f"bundle_root はプロジェクト内の相対パスで指定してください: {raw!r}")
    bundle_root = bundle_root.rstrip("/")
    if not bundle_root or ".." in bundle_root.split("/"):
        raise OkfError(f"bundle_root が不正です: {raw!r}")
    site_name = (args.site_name or REPO_ROOT.name).strip() or "Project"

    created: list[str] = []
    skipped: list[str] = []

    def emit(rel: str, text: str) -> None:
        path = REPO_ROOT / rel
        if path.exists() and not args.force:
            skipped.append(rel)
            return
        path.parent.mkdir(parents=True, exist_ok=True)
        write_if_changed(path, text)
        created.append(rel)

    layer_table = "\n".join(
        f"| `{bundle_root}/{d}/log.md` | `{g}` の変更 |" for _n, g, d in layers
    ) or "| （層を定義していません） | — |"
    tokens = {
        "GENERATED_AT": now_iso(),
        "BUNDLE_ROOT": bundle_root,
        "SITE_NAME": site_name,
        "LAYER_LIST": "、".join(n for n, _g, _d in layers) or "（層なし）",
        "LAYER_DIRS": " ".join(f"`{d}/`" for _n, _g, d in layers) or "—",
        "LAYER_TABLE": layer_table,
    }

    def expand(text: str) -> str:
        for key, value in tokens.items():
            text = text.replace("{{" + key + "}}", value)
        return text

    emit(CONFIG_FILENAME, _render_okf_yml(bundle_root, site_name, layers))
    emit(f"{bundle_root}/AGENTS.md", expand(_scaffold_text("AGENTS.md.tmpl")))
    emit(f"{bundle_root}/CONVENTIONS.md", expand(_scaffold_text("CONVENTIONS.md.tmpl")))

    for tmpl in sorted((SCAFFOLD_DIR / "templates").glob("*.md")):
        emit(f"{bundle_root}/_templates/{tmpl.name}", _scaffold_text(f"templates/{tmpl.name}"))
    for hook in sorted((SCAFFOLD_DIR / "hooks").iterdir()):
        emit(f".okf/hooks/{hook.name}", _scaffold_text(f"hooks/{hook.name}"))

    def empty_log(layer_name: str) -> str:
        return (
            f"# 変更履歴 — {layer_name}\n"
            "\n"
            "<!-- `okf log --write` が git 履歴からここに追記する。"
            "書式は /CONVENTIONS.md §7 を参照。 -->\n"
        )

    for name, _glob, directory in layers:
        emit(f"{bundle_root}/{directory}/log.md", empty_log(name))
    emit(f"{bundle_root}/project/log.md", empty_log("shared"))

    for rel in created:
        print(f"作成: {rel}")
    if skipped:
        print(f"既存のためスキップ（--force で上書き）: {len(skipped)} 件")
        for rel in skipped:
            print(f"  {rel}")
    print()
    print("次の手順:")
    print(f"  1. {bundle_root}/CONVENTIONS.md の語彙を確認・調整する")
    print(f"  2. {CONFIG_FILENAME} の layer_map が実際のコード配置と合っているか確認する")
    print("  3. okf index --write で目次を生成する")
    print("  4. okf lint で規約違反が無いか確認する")
    return 0


# =============================================================================
# エントリーポイント
# =============================================================================


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
    p_stale.add_argument("--format", choices=["text", "json"], default="text")

    p_affected = sub.add_parser("affected", help="更新すべきドキュメントを列挙する")
    p_affected.add_argument("--base", default="main", help="比較対象のブランチ（既定: main）")
    p_affected.add_argument("--paths", nargs="+", help="変更パスを直接指定する")

    p_new = sub.add_parser("new", help="雛形を生成する")
    new_sub = p_new.add_subparsers(dest="kind", required=True)

    p_new_backlog = new_sub.add_parser("backlog", help="backlog アイテムを作る")
    p_new_backlog.add_argument("--title", required=True)
    p_new_backlog.add_argument("--layer", default="shared")
    p_new_backlog.add_argument("--priority", default="medium")
    p_new_backlog.add_argument("--effort", default="M")
    p_new_backlog.add_argument("--slug", help="ファイル名の slug（日本語タイトル時に指定する）")

    p_new_doc = new_sub.add_parser("doc", help="通常ドキュメントを作る")
    p_new_doc.add_argument("--layer", required=True)
    p_new_doc.add_argument("--type", required=True)
    p_new_doc.add_argument("--title", required=True)
    p_new_doc.add_argument("--dir", help="層ディレクトリ配下のサブディレクトリ")
    p_new_doc.add_argument("--slug", help="ファイル名の slug")

    p_status = sub.add_parser("status", help="backlog の集計")
    p_status.add_argument("--format", choices=["text", "json"], default="text")

    p_render = sub.add_parser("render", help="Bundle の Markdown を閲覧用 HTML に変換する")
    p_render.add_argument("--output", help="出力先（既定: Markdown の隣。例: _site）")
    p_render.add_argument("--check", action="store_true", help="書き込まず、全ページを生成できるか検証する")
    p_render.add_argument("--hook", action="store_true", help="Stop hook 用。成功時は空の JSON だけを返す")

    p_sync = sub.add_parser("sync", help="index → log → lint → stale を一括実行する")
    p_sync.add_argument("--gate", action="store_true", help="hook 用。error があれば exit 2")
    p_sync.add_argument("--session-id", help="gate のセッション識別子（既定: 環境変数 / stdin JSON）")

    return parser


def resolve_root(args) -> Path:
    """プロジェクトルートを決める。``--root`` > ``--config`` の親 > 自動探索。"""
    if getattr(args, "root", None):
        root = Path(args.root).expanduser().resolve()
        if not root.is_dir():
            raise OkfError(f"--root がディレクトリではありません: {root}")
        return root
    if getattr(args, "config", None):
        return Path(args.config).expanduser().resolve().parent
    return find_project_root()


def main(argv: list[str] | None = None) -> int:
    global REPO_ROOT
    args = build_parser().parse_args(argv)
    gate = args.command == "sync" and getattr(args, "gate", False)
    try:
        REPO_ROOT = resolve_root(args)
        if args.command == "init":
            return cmd_init(args)
        bundle = Bundle(Path(args.config) if args.config else None)
        if not bundle.root.exists():
            raise OkfError(f"バンドルルートがありません: {bundle.root}")
        handlers = {
            "index": cmd_index,
            "log": cmd_log,
            "lint": cmd_lint,
            "stale": cmd_stale,
            "affected": cmd_affected,
            "new": cmd_new,
            "status": cmd_status,
            "render": cmd_render,
            "sync": cmd_sync,
        }
        return handlers[args.command](bundle, args)
    except OkfError as exc:
        print(f"エラー: {exc}", file=sys.stderr)
        if gate:
            # gate 中の運用エラーは fail-open にせず、安全側（差し戻し）に倒す
            print("[okf gate] 上記エラーのため検証を完了できませんでした。", file=sys.stderr)
            return 2
        return 1


def run() -> int:
    """コンソールスクリプト（`okf`）のエントリーポイント。"""
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # Windows のコンソール対策
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:  # pragma: no cover
        pass
    return main()


if __name__ == "__main__":
    sys.exit(run())
