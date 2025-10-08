from __future__ import annotations

import json
from typing import List, Tuple

def _le32(n: int) -> bytes:
    return (n & 0xFFFFFFFF).to_bytes(4, "little", signed=False)


def pack_lz4_filelist(filelist: List[Tuple[str, bytes]]) -> bytes:
    """
    manga-editor-desu の lz4Compressor と互換の LZ4 ブロブを生成する。
    構造: [4byte:header_size_le] [header(JSON UTF-8)] [lz4block(combinedData)]
    header は [{"name": str, "size": int}, ...]
    """
    try:
        import lz4.block as lz4b
    except Exception as e:
        raise RuntimeError("Python package 'lz4' is required: pip install lz4") from e

    header_arr = [{"name": name, "size": len(data)} for name, data in filelist]
    header = json.dumps(header_arr, ensure_ascii=False).encode("utf-8")
    combined = b"".join(data for _, data in filelist)
    # lz4js はLZ4ブロック圧縮を使用しているため、block.compressを利用
    compressed = lz4b.compress(combined)
    return _le32(len(header)) + header + compressed


def merge_lz4_parts(parts: List[bytes]) -> bytes:
    """
    lz4Compressor.mergeLz4Blobs と互換の上位 LZ4 を生成する。
    parts は下位 LZ4ブロブのバイト列。
    各パートは name: lz4_part_N.lz4 としてヘッダに登録される。
    """
    flist: List[Tuple[str, bytes]] = [(f"lz4_part_{i}.lz4", data) for i, data in enumerate(parts)]
    return pack_lz4_filelist(flist)


def unpack_lz4_files(blob: bytes) -> List[Tuple[str, bytes]]:
    """pack_lz4_filelist の逆変換。"""
    import struct
    try:
        import lz4.block as lz4b
    except Exception as e:
        raise RuntimeError("Python package 'lz4' is required: pip install lz4") from e
    if len(blob) < 4:
        raise ValueError("invalid lz4 blob: too short")
    header_len = struct.unpack('<I', blob[:4])[0]
    header_bytes = blob[4:4+header_len]
    import json
    header = json.loads(header_bytes.decode('utf-8'))
    comp = blob[4+header_len:]
    decomp = lz4b.decompress(comp)
    out = []
    ofs = 0
    for ent in header:
        size = int(ent['size'])
        name = ent['name']
        out.append((name, decomp[ofs:ofs+size]))
        ofs += size
    return out
