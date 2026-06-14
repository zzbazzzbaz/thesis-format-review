"""CLI 测试：参数解析与输入校验。"""
from __future__ import annotations

import pytest

from src.cli import build_parser, validate_input


def test_parser_requires_input_and_output():
    """解析位置 input + -o output。"""
    parser = build_parser()
    args = parser.parse_args(["in.docx", "-o", "out.docx"])
    assert args.input == "in.docx"
    assert args.output == "out.docx"


def test_validate_rejects_non_docx(tmp_path):
    """非 .docx 后缀应拒绝。"""
    bad = tmp_path / "x.doc"
    bad.write_text("x")
    with pytest.raises(SystemExit):
        validate_input(str(bad))


def test_validate_rejects_missing_file(tmp_path):
    """不存在的文件应拒绝。"""
    with pytest.raises(SystemExit):
        validate_input(str(tmp_path / "nope.docx"))


def test_validate_accepts_docx(tmp_path):
    """已存在的 .docx 应通过校验。"""
    f = tmp_path / "test.docx"
    f.write_text("x")
    validate_input(str(f))  # 不应抛异常
