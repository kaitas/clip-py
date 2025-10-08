from __future__ import annotations

from pathlib import Path

from clip_py.header import seek_sqlite_header_in_file


ASSETS = Path("tests/assets")


def test_sample_clip_header_offset():
    sample = ASSETS / "sample.clip"
    assert sample.exists(), "tests/assets/sample.clip が存在しません"
    # 既存Goテスト(export_test.go)準拠の既知オフセット
    expected = 3494297
    offset = seek_sqlite_header_in_file(str(sample))
    assert offset == expected

