"""Web service 层测试。"""
from __future__ import annotations

from email.parser import BytesParser
from email.policy import default
from io import BytesIO
from pathlib import Path

import pytest
from starlette.datastructures import UploadFile

from thesis_review.interfaces.web import services


def make_upload(filename: str | None, content: bytes) -> UploadFile:
    return UploadFile(filename=filename, file=BytesIO(content))


def parse_artifacts(artifacts: services.WebReviewArtifacts):
    raw = (
        b"Content-Type: "
        + artifacts.media_type.encode("utf-8")
        + b"\r\nMIME-Version: 1.0\r\n\r\n"
        + artifacts.body
    )
    return BytesParser(policy=default).parsebytes(raw)


def test_review_upload_rejects_empty_filename():
    upload = make_upload(None, b"abc")

    with pytest.raises(services.InvalidUpload, match="请选择 .docx 文件"):
        services.review_upload(upload)


def test_review_upload_rejects_non_docx():
    upload = make_upload("paper.pdf", b"abc")

    with pytest.raises(services.InvalidUpload, match="仅支持 .docx 文件"):
        services.review_upload(upload)


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

    result = services.review_upload(upload)

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


def test_review_upload_artifacts_returns_multipart_payload(monkeypatch):
    seen_out_dirs: list[Path] = []

    def fake_review(input_docx: str, out_dir: Path):
        seen_out_dirs.append(out_dir)
        out_dir.mkdir(parents=True)
        result = type("FakeEngineResult", (), {})()
        result.marked_docx = out_dir / "marked.docx"
        result.issues_json = out_dir / "issues.json"
        result.marked_docx.write_bytes(b"marked docx bytes")
        result.issues_json.write_text('{"issues": []}', encoding="utf-8")
        return result

    monkeypatch.setattr(services, "review", fake_review)
    upload = make_upload("paper.docx", b"input docx bytes")

    artifacts = services.review_upload_artifacts(upload)
    message = parse_artifacts(artifacts)
    parts = list(message.iter_parts())

    assert artifacts.media_type.startswith("multipart/mixed")
    assert len(parts) == 2
    assert parts[0]["content-disposition"] == (
        'attachment; name="marked_docx"; filename="marked.docx"'
    )
    assert parts[0].get_content_type() == services.DOCX_MIME
    assert parts[0].get_payload(decode=True) == b"marked docx bytes"
    assert parts[1]["content-disposition"] == (
        'attachment; name="issues_json"; filename="issues.json"'
    )
    assert parts[1].get_content_type() == services.JSON_MIME
    assert parts[1].get_payload(decode=True) == b'{"issues": []}'

    artifacts.cleanup()
    assert seen_out_dirs
    assert not seen_out_dirs[0].parent.exists()


def test_review_upload_cleans_workdir_when_engine_fails(monkeypatch):
    seen_input_dirs: list[Path] = []

    def fake_review(input_docx: str, out_dir: Path):
        seen_input_dirs.append(Path(input_docx).parent)
        raise RuntimeError("engine failed")

    monkeypatch.setattr(services, "review", fake_review)
    upload = make_upload("paper.docx", b"input")

    with pytest.raises(RuntimeError, match="engine failed"):
        services.review_upload(upload)

    assert seen_input_dirs
    assert not seen_input_dirs[0].exists()
