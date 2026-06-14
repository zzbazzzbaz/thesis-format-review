"""命令行入口。"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path


def build_parser() -> argparse.ArgumentParser:
    """构建参数解析器。"""
    p = argparse.ArgumentParser(
        prog="thesis-review",
        description="毕业设计论文格式审核",
    )
    p.add_argument("input", help="输入 .docx 路径")
    p.add_argument("-o", "--output", required=True, help="输出 marked.docx 路径")
    return p


def validate_input(path: str) -> None:
    """校验输入文件存在且为 .docx 格式。"""
    f = Path(path)
    if not f.exists():
        print(f"错误：文件不存在：{path}", file=sys.stderr)
        raise SystemExit(2)
    if f.suffix.lower() != ".docx":
        print("错误：仅支持 .docx 输入(不支持 .doc，不做转换)", file=sys.stderr)
        raise SystemExit(2)


def main(argv: list[str] | None = None) -> int:
    """CLI 入口。返回退出码（0=成功）。"""
    args = build_parser().parse_args(argv)
    validate_input(args.input)
    # 延迟导入：避免无 UNO 环境时 import 失败影响 --help
    from src.pipeline import review
    issues = review(args.input, args.output)
    errors = sum(1 for i in issues if i.severity == "error")
    warnings = sum(1 for i in issues if i.severity == "warning")
    print(f"检查完成：{errors} 处错误，{warnings} 处警告 → {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
