from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, List, Tuple

from .text_extract import extract_texts_from_path

PAGE_RE = re.compile(r"page(\d+)\.clip$", re.IGNORECASE)


def _page_number_from_name(name: str) -> int:
    m = PAGE_RE.search(name)
    return int(m.group(1)) if m else 0


def _clean_text(s: str) -> str:
    # 改行を正規化、制御文字は削除
    s = s.replace("\r\n", "\n").replace("\r", "\n")
    return "".join(ch for ch in s if ch >= "\u0020" or ch in "\n\t")


def _group_lines_by_page(records: List[Dict[str, str]]) -> Dict[str, List[str]]:
    pages: Dict[str, List[str]] = {}
    for r in records:
        table = r.get("table", "")
        col = r.get("column", "")
        if table == "Layer" and col in ("TextLayerString", "TextLayerStringArray"):
            file = r.get("file", "")
            pages.setdefault(file, []).append(_clean_text(r.get("text", "")))
    return pages


def _collect_panels(records: List[Dict[str, str]]) -> Dict[str, List[str]]:
    panels: Dict[str, List[str]] = {}
    for r in records:
        if r.get("table") == "Layer" and r.get("column") == "LayerName":
            t = r.get("text", "")
            if t.startswith("コマ"):
                file = r.get("file", "")
                panels.setdefault(file, []).append(t)
    return panels


def write_gensaku(target_dir: Path, out_yaml: Path, title: str = "", per_page: bool = False) -> None:
    """
    原作者向けの軽量YAML（gensaku）を出力する。
    - ページ単位に台詞群と簡易パネル名（"コマ n"）のみを収録
    - 大規模でも開きやすいよう、必要最低限の情報に絞る
    - per_page=True の場合、ページごとに分割YAMLも出力
    """
    records = extract_texts_from_path(target_dir, limit=0)
    by_page = _group_lines_by_page(records)
    panels = _collect_panels(records)

    # ページ順に並べ替え
    page_keys = sorted(by_page.keys(), key=lambda f: (_page_number_from_name(Path(f).name), Path(f).name))

    # YAML出力を手書きで生成
    out_yaml.parent.mkdir(parents=True, exist_ok=True)
    with out_yaml.open("w", encoding="utf-8") as f:
        if title:
            f.write(f"title: \"{title}\"\n\n")
        f.write("pages:\n")
        for file in page_keys:
            name = Path(file).name
            page_num = _page_number_from_name(name)
            f.write(f"  - file: {name}\n")
            if page_num:
                f.write(f"    page_number: {page_num}\n")
            ps = panels.get(file) or []
            if ps:
                f.write("    panels:\n")
                # 多すぎると読みにくいので上位のみ
                for p in ps[:20]:
                    f.write(f"      - {p}\n")
            lines = by_page[file]
            f.write("    speech:\n")
            # 各ページの台詞を上位のみ（サイズ抑制）
            for line in lines[:80]:
                if "\n" in line:
                    f.write("      - |\n")
                    for ln in line.split("\n"):
                        f.write(f"          {ln}\n")
                else:
                    f.write(f"      - {line}\n")

            # 省略がある場合の注記
            if len(lines) > 80:
                f.write(f"    note: "+f"このページの台詞は {len(lines)} 件。先頭80件のみ記載。\n")

    if per_page:
        per_dir = out_yaml.parent / (out_yaml.stem + "_pages")
        per_dir.mkdir(parents=True, exist_ok=True)
        for file in page_keys:
            name = Path(file).name
            page_num = _page_number_from_name(name)
            p_out = per_dir / (f"page{page_num:04d}.yaml" if page_num else (name + ".yaml"))
            with p_out.open("w", encoding="utf-8") as pf:
                pf.write(f"file: {name}\n")
                if page_num:
                    pf.write(f"page_number: {page_num}\n")
                ps = panels.get(file) or []
                if ps:
                    pf.write("panels:\n")
                    for p in ps:
                        pf.write(f"  - {p}\n")
                lines = by_page[file]
                pf.write("speech:\n")
                for line in lines:
                    if "\n" in line:
                        pf.write("  - |\n")
                        for ln in line.split("\n"):
                            pf.write(f"      {ln}\n")
                    else:
                        pf.write(f"  - {line}\n")

