"""Root-independent paths, atomic file writes, dates and glob matching."""
from __future__ import annotations

import datetime as _dt
import os
import re
import tempfile
import time
from pathlib import Path, PurePosixPath

from .errors import OkfError

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
