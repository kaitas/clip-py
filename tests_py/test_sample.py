from __future__ import annotations

# 初心者向けの補足:
# - このテストは「サンプルの .clip ファイルの中でSQLiteヘッダがどこにあるか」を確認します。
# - 既存のGo実装（export_test.go）で既知のオフセット値(3494297)が定義されており、
#   Python版でも同じ位置を検出できることを検証します。

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
