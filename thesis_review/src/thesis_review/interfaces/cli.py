"""命令行入口。"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from thesis_review.engine import review


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="thesis-review",
        description="毕业设计论文格式审核",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    review_parser = subparsers.add_parser("review", help="审核 .docx 文档")
    review_parser.add_argument("input", help="输入 .docx 路径")
    review_parser.add_argument("--out-dir", required=True, help="输出目录")
    return parser


def validate_input(path: str | Path) -> Path:
    file_path = Path(path)
    if not file_path.exists():
        print(f"错误：文件不存在：{file_path}", file=sys.stderr)
        raise SystemExit(2)
    if file_path.suffix.lower() != ".docx":
        print("错误：仅支持 .docx 输入(不支持 .doc，不做转换)", file=sys.stderr)
        raise SystemExit(2)
    return file_path


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "review":
        input_path = validate_input(args.input)
        out_dir = Path(args.out_dir)
        result = review(input_path, out_dir)
        summary = result.summary
        print(
            "检查完成："
            f"{summary['error']} 处错误，{summary['warning']} 处警告 "
            f"→ {result.marked_docx}，{result.issues_json}"
        )
        return 0
    raise SystemExit(2)


if __name__ == "__main__":
    raise SystemExit(main())
