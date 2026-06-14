"""Web service 层测试。"""
from __future__ import annotations

import asyncio
from io import BytesIO
from pathlib import Path

import pytest
from starlette.datastructures import UploadFile

from thesis_review.web import services


def make_upload(filename: str | None, content: bytes) -> UploadFile:
    return UploadFile(filename=filename, file=BytesIO(content))


def test_review_upload_rejects_empty_filename():
    upload = make_upload(None, b"abc")

    with pytest.raises(services.InvalidUpload, match="请选择 .docx 文件"):
        asyncio.run(services.review_upload(upload))


def test_review_upload_rejects_non_docx():
    upload = make_upload("paper.pdf", b"abc")

    with pytest.raises(services.InvalidUpload, match="仅支持 .docx 文件"):
        asyncio.run(services.review_upload(upload))


def test_review_upload_saves_file_calls_pipeline_and_returns_download(monkeypatch):
    calls: list[tuple[str, str]] = []

    def fake_review(input_docx: str, output_docx: str):
        calls.append((input_docx, output_docx))
        Path(output_docx).write_bytes(b"marked docx bytes")
        return []

    monkeypatch.setattr(services.pipeline, "review", fake_review)
    upload = make_upload("论文初稿.docx", b"input docx bytes")

    result = asyncio.run(services.review_upload(upload))

    assert result.output_path.exists()
    assert result.output_path.read_bytes() == b"marked docx bytes"
    assert result.download_name == "论文初稿.marked.docx"
    assert len(calls) == 1
    input_docx, output_docx = calls[0]
    assert Path(input_docx).read_bytes() == b"input docx bytes"
    assert Path(output_docx) == result.output_path

    workdir = result.output_path.parent
    result.cleanup()
    assert not workdir.exists()


def test_review_upload_cleans_workdir_when_pipeline_fails(monkeypatch):
    seen_input_dirs: list[Path] = []

    def fake_review(input_docx: str, output_docx: str):
        seen_input_dirs.append(Path(input_docx).parent)
        raise RuntimeError("pipeline failed")

    monkeypatch.setattr(services.pipeline, "review", fake_review)
    upload = make_upload("paper.docx", b"input")

    with pytest.raises(RuntimeError, match="pipeline failed"):
        asyncio.run(services.review_upload(upload))

    assert seen_input_dirs
    assert not seen_input_dirs[0].exists()
