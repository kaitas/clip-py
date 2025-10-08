from __future__ import annotations

import io
import sqlite3
import tempfile
import zipfile
from pathlib import Path
from typing import List, Tuple

from .text_extract import extract_sqlite_to_temp
from .lz4pack import pack_lz4_filelist, merge_lz4_parts

try:
    from PIL import Image
except Exception:
    Image = None  # Pillow 未導入でもPNGをそのまま入れる


def _read_canvas_preview_png(db_path: Path) -> bytes | None:
    con = sqlite3.connect(str(db_path))
    cur = con.cursor()
    try:
        row = cur.execute("SELECT ImageData FROM CanvasPreview LIMIT 1").fetchone()
        if not row:
            return None
        data = row[0]
        if isinstance(data, memoryview):
            data = data.tobytes()
        return bytes(data)
    except Exception:
        return None
    finally:
        con.close()


def _png_to_jpeg_bytes(png_bytes: bytes) -> bytes:
    if Image is None:
        # フォールバック: そのままPNGを返す（拡張子はjpegのままでも読み込まれる）
        return png_bytes
    img = Image.open(io.BytesIO(png_bytes)).convert("RGB")
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85)
    return buf.getvalue()


def export_desu_project(target_dir: Path, out_zip: Path, with_gensaku: bool = False) -> None:
    """
    manga-editor-desu の "Project Load" が受け付ける入れ子ZIP群を生成する。
    - 各ページごとに ZIP を作成し、preview-image.jpeg を含める
    - それらをまとめた ZIP を out_zip に出力
    - with_gensaku=True のとき、ページごとの簡易YAML（gensaku_pages/pageXXXX.yaml）が存在すれば同梱
    """
    page_files: List[Path] = sorted([p for p in target_dir.iterdir() if p.suffix.lower() == ".clip"])
    out_zip.parent.mkdir(parents=True, exist_ok=True)
    gensaku_dir = target_dir / "gensaku_pages"

    with zipfile.ZipFile(out_zip, "w", compression=zipfile.ZIP_DEFLATED) as outer_zip:
        for clip_path in page_files:
            # SQLite 抽出 → CanvasPreview を JPEG に変換
            try:
                db = extract_sqlite_to_temp(clip_path)
                png = _read_canvas_preview_png(db)
            finally:
                try:
                    db.unlink(missing_ok=True)
                except Exception:
                    pass
            if not png:
                continue
            jpeg = _png_to_jpeg_bytes(png)

            # 内側ZIPをメモリ上で構築
            inner_buf = io.BytesIO()
            with zipfile.ZipFile(inner_buf, "w", compression=zipfile.ZIP_DEFLATED) as inner_zip:
                inner_zip.writestr("preview-image.jpeg", jpeg)
                if with_gensaku and gensaku_dir.exists():
                    # ページ番号から gensaku を探す
                    stem = clip_path.stem  # page0001
                    # 推測: pageXXXX.yaml
                    g_path = gensaku_dir / (stem + ".yaml")
                    if g_path.exists():
                        inner_zip.writestr("page_gensaku.yaml", g_path.read_text())

            inner_name = clip_path.stem + ".zip"
            outer_zip.writestr(inner_name, inner_buf.getvalue())


def export_desu_lz4(target_dir: Path, out_lz4: Path, with_gensaku: bool = False) -> None:
    """
    DESU-Project.lz4 を生成（上位LZ4に、各ページの下位LZ4を含める）。
    下位LZ4は最低限 preview-image.jpeg（と任意で page_gensaku.yaml）を含める。
    """
    page_files: List[Path] = sorted([p for p in target_dir.iterdir() if p.suffix.lower() == ".clip"])
    gensaku_dir = target_dir / "gensaku_pages"
    parts: List[bytes] = []
    for clip_path in page_files:
        try:
            db = extract_sqlite_to_temp(clip_path)
            png = _read_canvas_preview_png(db)
        finally:
            try:
                db.unlink(missing_ok=True)
            except Exception:
                pass
        if not png:
            continue
        jpeg = _png_to_jpeg_bytes(png)
        files = [("preview-image.jpeg", jpeg)]
        if with_gensaku and gensaku_dir.exists():
            g_path = gensaku_dir / (clip_path.stem + ".yaml")
            if g_path.exists():
                files.append(("page_gensaku.yaml", g_path.read_bytes()))
        part = pack_lz4_filelist(files)
        parts.append(part)
    out_lz4.parent.mkdir(parents=True, exist_ok=True)
    out_lz4.write_bytes(merge_lz4_parts(parts))

