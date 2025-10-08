from __future__ import annotations

SQLITE_HEADER = b"SQLite format 3\x00"


def seek_sqlite_header(data: bytes) -> int:
    """Return the byte offset where the SQLite header begins.

    Raises ValueError if not found.
    """
    idx = data.find(SQLITE_HEADER)
    if idx == -1:
        raise ValueError("SQLite header not found")
    return idx


def seek_sqlite_header_in_file(path: str) -> int:
    with open(path, "rb") as f:
        blob = f.read()
    return seek_sqlite_header(blob)

