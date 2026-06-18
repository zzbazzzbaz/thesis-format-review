"""Web service 层测试。"""
from __future__ import annotations

import asyncio
from io import BytesIO
from pathlib import Path

import pytest
from starlette.datastructures import UploadFile

from thesis_review.interfaces.web import services


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


def test_review_upload_saves_file_calls_engine_and_returns_download(monkeypatch):
    calls: list[tuple[str, Path]] = []

    class FakeEngineResult:
        def __init__(self, out_dir: Path):
            self.marked_docx = out_dir / "marked.docx"
            self.issues_json = out_dir / "issues.json"

    def fake_review(input_docx: str, out_dir: Path):
        calls.append((input_docx, out_dir))
        out_dir.mkdir(parents=True)
        result = FakeEngineResult(out_dir)
        result.marked_docx.write_bytes(b"marked docx bytes")
        result.issues_json.write_text('{"issues": []}', encoding="utf-8")
        return result

    monkeypatch.setattr(services, "review", fake_review)
    upload = make_upload("论文初稿.docx", b"input docx bytes")

    result = asyncio.run(services.review_upload(upload))

    assert result.output_path.exists()
    assert result.output_path.read_bytes() == b"marked docx bytes"
    assert result.issues_json.exists()
    assert result.download_name == "论文初稿.marked.docx"
    assert len(calls) == 1
    input_docx, out_dir = calls[0]
    assert Path(input_docx).read_bytes() == b"input docx bytes"
    assert out_dir == result.output_path.parent

    workdir = result.output_path.parent.parent
    result.cleanup()
    assert not workdir.exists()


def test_review_upload_cleans_workdir_when_pipeline_fails(monkeypatch):
    seen_input_dirs: list[Path] = []

    def fake_review(input_docx: str, out_dir: Path):
        seen_input_dirs.append(Path(input_docx).parent)
        raise RuntimeError("pipeline failed")

    monkeypatch.setattr(services, "review", fake_review)
    upload = make_upload("paper.docx", b"input")

    with pytest.raises(RuntimeError, match="pipeline failed"):
        asyncio.run(services.review_upload(upload))

    assert seen_input_dirs
    assert not seen_input_dirs[0].exists()
