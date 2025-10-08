from __future__ import annotations

# 初心者向けの補足:
# - ここはPython版CLIのエントリポイント（実行開始地点）です。
# - 「clip-py」というコマンド名で実行できるよう、pyproject.tomlでエントリポイントを設定しています。
# - 引数の処理には標準ライブラリのargparseを使います。

import argparse
import sys
from pathlib import Path
from . import __version__
from .text_extract import extract_texts_from_path, write_output


def main(argv: list[str] | None = None) -> int:
    # ArgumentParserはコマンドライン引数の説明やヘルプを自動生成してくれます。
    parser = argparse.ArgumentParser(prog="clip-py", description="clip binary helpers（テキスト抽出に注力）")
    sub = parser.add_subparsers(dest="cmd")

    parser.add_argument("--version", action="store_true", help="バージョン表示")

    # extract-text サブコマンド
    p_ext = sub.add_parser("extract-text", help=".clip/.cmc から日本語テキストを抽出")
    p_ext.add_argument("path", help="対象ファイルまたはディレクトリ")
    p_ext.add_argument("-o", "--output", default="-", help="出力先（- は標準出力）")
    p_ext.add_argument("--format", choices=["jsonl", "md", "yaml"], default="jsonl", help="出力フォーマット")
    p_ext.add_argument("--limit", type=int, default=0, help="各テーブルのサンプル件数上限（0は無制限）")

    # outline（gensakuフォーマット）
    from .gensaku import write_gensaku  # import here to keep startup fast
    p_gen = sub.add_parser("outline", help="原作者向けの簡易アウトラインYAML（gensaku）を生成")
    p_gen.add_argument("path", help="対象ディレクトリ（.clip/.cmc を含む）")
    p_gen.add_argument("-o", "--output", default="gensaku.yaml", help="出力YAMLパス（デフォルト: gensaku.yaml）")
    p_gen.add_argument("--title", default="", help="作品タイトル（省略可）")
    p_gen.add_argument("--per-page", action="store_true", help="ページごとに分割ファイルを出力（outputと同ディレクトリに出力）")

    # export-desu（manga-editor-desu用のプロジェクトZIP）
    from .export_desu import export_desu_project, export_desu_lz4  # lazy import
    p_desu = sub.add_parser("export-desu", help="manga-editor-desu に読み込めるZIP（入れ子）を生成")
    p_desu.add_argument("path", help="対象ディレクトリ（.clip を含む）")
    p_desu.add_argument("-o", "--output", default="DESU-Project.zip", help="出力ZIPパス")
    p_desu.add_argument("--with-gensaku", action="store_true", help="各ページZIPに簡易gensaku YAMLを同梱")

    p_desu_lz4 = sub.add_parser("export-desu-lz4", help="manga-editor-desu の LZ4 プロジェクトを生成")
    p_desu_lz4.add_argument("path", help="対象ディレクトリ（.clip を含む）")
    p_desu_lz4.add_argument("-o", "--output", default="DESU-Project.lz4", help="出力LZ4パス")
    p_desu_lz4.add_argument("--with-gensaku", action="store_true", help="各ページパートに簡易gensaku YAMLを同梱")

    args = parser.parse_args(argv)

    if args.version and not args.cmd:
        print(__version__)
        return 0

    if args.cmd == "extract-text":
        texts = extract_texts_from_path(Path(args.path), limit=args.limit)
        write_output(texts, Path(args.output) if args.output != "-" else None, fmt=args.format)
        return 0

    if args.cmd == "outline":
        target = Path(args.path)
        out = Path(args.output)
        write_gensaku(target, out, title=args.title, per_page=args.per_page)
        return 0

    if args.cmd == "export-desu":
        export_desu_project(Path(args.path), Path(args.output), with_gensaku=args.with_gensaku)
        return 0

    if args.cmd == "export-desu-lz4":
        export_desu_lz4(Path(args.path), Path(args.output), with_gensaku=args.with_gensaku)
        return 0

    parser.print_help()
    return 0


if __name__ == "__main__":  # pragma: no cover
    # スクリプトとして直接実行された場合のエントリポイントです。
    raise SystemExit(main())
