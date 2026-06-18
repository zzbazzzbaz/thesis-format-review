"""CLI 参数和输出目录测试。"""
from __future__ import annotations

import json

import pytest

from thesis_review.interfaces import cli


def test_parser_accepts_review_input_and_out_dir():
    parser = cli.build_parser()

    args = parser.parse_args(["review", "in.docx", "--out-dir", "out"])

    assert args.command == "review"
    assert args.input == "in.docx"
    assert args.out_dir == "out"


def test_validate_input_rejects_non_docx(tmp_path):
    bad = tmp_path / "x.doc"
    bad.write_text("x", encoding="utf-8")

    with pytest.raises(SystemExit):
        cli.validate_input(bad)


def test_validate_input_rejects_missing_file(tmp_path):
    with pytest.raises(SystemExit):
        cli.validate_input(tmp_path / "missing.docx")


def test_main_calls_engine_and_prints_summary(monkeypatch, tmp_path, capsys):
    input_docx = tmp_path / "paper.docx"
    input_docx.write_bytes(b"docx")
    out_dir = tmp_path / "out"

    class FakeResult:
        marked_docx = out_dir / "marked.docx"
        issues_json = out_dir / "issues.json"
        summary = {"total": 1, "error": 1, "warning": 0, "info": 0}

    calls = []

    def fake_review(input_arg, out_dir_arg):
        calls.append((input_arg, out_dir_arg))
        out_dir.mkdir()
        FakeResult.marked_docx.write_bytes(b"marked")
        FakeResult.issues_json.write_text(json.dumps({"issues": []}), encoding="utf-8")
        return FakeResult()

    monkeypatch.setattr(cli, "review", fake_review)

    exit_code = cli.main(["review", str(input_docx), "--out-dir", str(out_dir)])

    assert exit_code == 0
    assert calls == [(input_docx, out_dir)]
    assert "检查完成：1 处错误，0 处警告" in capsys.readouterr().out
