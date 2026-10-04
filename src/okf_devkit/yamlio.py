"""Strict YAML parsing and frontmatter serialization with an optional backend."""
from __future__ import annotations

import datetime as _dt
import re

from .errors import OkfError
from .fsutil import ISO_DATE_RE

try:  # Use PyYAML when available.
    import yaml as _pyyaml
except Exception:  # pragma: no cover - environment dependent
    _pyyaml = None

_DEFAULT_BACKEND = object()

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


def parse_yaml(text: str, source: str = "<yaml>", *, backend=_DEFAULT_BACKEND):
    """YAML を dict / list に変換する。PyYAML 優先、無ければ内蔵パーサ。"""
    selected = _pyyaml if backend is _DEFAULT_BACKEND else backend
    if selected is not None:
        try:
            return _normalize(selected.safe_load(text))
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
