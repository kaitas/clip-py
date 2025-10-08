from __future__ import annotations

# 初心者向けの補足:
# - CLIP STUDIO の .clip ファイルは内部的にSQLiteデータベースを含みます。
# - 下の定数はSQLiteファイルの先頭に現れる「おまじない」のようなバイト列です。
# - このヘッダを探し、その位置(オフセット)からSQLite DBが始まると判断します。

SQLITE_HEADER = b"SQLite format 3\x00"


def seek_sqlite_header(data: bytes) -> int:
    """
    SQLiteヘッダが始まる位置（バイトオフセット）を返します。

    見つからない場合は ValueError を投げます。
    """
    idx = data.find(SQLITE_HEADER)
    if idx == -1:
        raise ValueError("SQLite header not found")
    return idx


def seek_sqlite_header_in_file(path: str) -> int:
    """
    ファイル全体を読み込み、SQLiteヘッダの位置を返します。
    大きなファイルではメモリ使用量に注意（後でストリーム対応に拡張予定）。
    """
    with open(path, "rb") as f:
        blob = f.read()
    return seek_sqlite_header(blob)
