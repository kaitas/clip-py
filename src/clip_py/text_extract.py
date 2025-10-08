from __future__ import annotations

# 初心者向けの補足:
# - .clip/.cmc はバイナリ先頭ではなく途中から SQLite のヘッダが始まります。
# - ここではSQLiteを抽出→各テーブルを走査し、日本語を含むテキストを収集します。

import io
import re
import sqlite3
import tempfile
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Iterable, Iterator, List, Dict, Any

SQLITE_HEADER = b"SQLite format 3\x00"
JP_RE = re.compile(r"[\u3040-\u30FF\u4E00-\u9FFF]")


def has_japanese(s: str) -> bool:
    return bool(JP_RE.search(s))


def extract_sqlite_to_temp(path: Path) -> Path:
    data = path.read_bytes()
    ofs = data.find(SQLITE_HEADER)
    if ofs < 0:
        raise RuntimeError(f"SQLite header not found: {path}")
    tmp = tempfile.NamedTemporaryFile(prefix="clip_py_", suffix=".sqlite", delete=False)
    tmp.write(data[ofs:])
    tmp.flush()
    tmp.close()
    return Path(tmp.name)


@dataclass
class TextRecord:
    file: str
    table: str
    column: str
    text: str


def iter_texts_from_sqlite(db_path: Path, limit: int = 0) -> Iterator[TextRecord]:
    con = sqlite3.connect(str(db_path))
    cur = con.cursor()
    tables = [r[0] for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table'")]
    for t in tables:
        # カラム名
        cols = [r[1] for r in cur.execute(f"PRAGMA table_info({t})")]
        q = f"SELECT * FROM {t}"
        if limit and limit > 0:
            q += f" LIMIT {int(limit)}"
        try:
            for row in cur.execute(q):
                for name, val in zip(cols, row):
                    if val is None:
                        continue
                    if isinstance(val, (bytes, bytearray)):
                        # BLOB からUTF-8として読める部分を拾う
                        s = bytes(val).decode("utf-8", errors="ignore")
                    else:
                        s = str(val)
                    # 改行や制御はそのまま、長すぎる場合は適度に切る
                    if s and has_japanese(s):
                        yield TextRecord(file=str(db_path), table=t, column=name, text=s[:4000])
        except Exception:
            # 一部のテーブルは権限/構造の都合で失敗する可能性があるためスキップ
            continue
    con.close()


def extract_texts_from_path(target: Path, limit: int = 0) -> List[Dict[str, Any]]:
    files: List[Path]
    if target.is_dir():
        files = sorted([p for p in target.iterdir() if p.suffix.lower() in (".clip", ".cmc")])
    else:
        files = [target]

    results: List[Dict[str, Any]] = []
    for f in files:
        try:
            db = extract_sqlite_to_temp(f)
        except Exception as e:
            results.append({"file": str(f), "error": str(e)})
            continue
        for rec in iter_texts_from_sqlite(db, limit=limit):
            results.append({
                "file": str(f),
                "table": rec.table,
                "column": rec.column,
                "text": rec.text,
            })
        try:
            db.unlink(missing_ok=True)
        except Exception:
            pass
    return results


def write_output(records: List[Dict[str, Any]], out: Path | None, fmt: str = "jsonl") -> None:
    if fmt == "jsonl":
        import json
        lines = [json.dumps(r, ensure_ascii=False) for r in records]
        data = "\n".join(lines) + ("\n" if lines else "")
    elif fmt == "md":
        from collections import defaultdict
        grouped: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        for r in records:
            grouped[r["file"]].append(r)
        buf = io.StringIO()
        for fname in sorted(grouped.keys()):
            buf.write(f"## {Path(fname).name}\n")
            g2 = grouped[fname]
            # テーブル.カラム単位でまとめる
            idx = {}
            for r in g2:
                key = (r["table"], r["column"])
                idx.setdefault(key, []).append(r["text"])
            for (t, c), arr in list(idx.items())[:50]:
                buf.write(f"- {t}.{c}:\n")
                for s in arr[:5]:
                    s2 = s.replace("\r", " ").replace("\n", "\n    ")
                    buf.write(f"    - {s2}\n")
            buf.write("\n")
        data = buf.getvalue()
    elif fmt == "yaml":
        # 人間可読（原作者向け）を想定した簡易YAML。主にセリフ等に限定。
        # - Layer.TextLayerString / TextLayerStringArray のみを抽出
        # - フォントは Project.ComicStoryNombreFont / Canvas.ComicStoryNombreFont を参考として添付
        from collections import defaultdict
        pages: Dict[str, Dict[str, Any]] = {}
        fonts_by_file: Dict[str, str] = {}
        panels_by_file: Dict[str, list] = defaultdict(list)
        for r in records:
            file = r.get("file", "")
            table = r.get("table", "")
            col = r.get("column", "")
            text = r.get("text", "")
            # フォント情報
            if col == "ComicStoryNombreFont" and table in ("Project", "Canvas"):
                fonts_by_file[file] = text
                continue
            # パネル名（"コマ n" を拾う）
            if table == "Layer" and col == "LayerName" and (text.startswith("コマ ") or text.startswith("コマ")):
                panels_by_file[file].append(text)
                continue
            # セリフ候補のみ
            if table == "Layer" and col in ("TextLayerString", "TextLayerStringArray"):
                entry = pages.setdefault(file, {"lines": []})
                entry["lines"].append(text)

        # YAML文字列を手作業で生成（PyYAML未使用）
        import io as _io
        buf = _io.StringIO()
        buf.write("pages:\n")
        for file in sorted(pages.keys()):
            page = pages[file]
            font = fonts_by_file.get(file)
            panels = panels_by_file.get(file) or []
            buf.write(f"  - file: {Path(file).name}\n")
            if font:
                buf.write(f"    font: {font}\n")
            if panels:
                buf.write("    panels:\n")
                for p in panels[:50]:
                    buf.write(f"      - {p}\n")
            buf.write("    lines:\n")
            for line in page["lines"][:500]:
                # YAMLの複数行は | で表現
                s = line.replace("\r\n", "\n").replace("\r", "\n")
                if "\n" in s:
                    buf.write("      - |\n")
                    for ln in s.split("\n"):
                        buf.write(f"          {ln}\n")
                else:
                    buf.write(f"      - {s}\n")
        data = buf.getvalue()
    else:
        raise ValueError(fmt)

    if out is None:
        # 標準出力
        print(data, end="")
    else:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(data)
