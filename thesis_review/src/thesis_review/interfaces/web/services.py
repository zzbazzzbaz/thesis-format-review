"""上传文件保存、审核调用和临时文件生命周期管理。"""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
import shutil
import tempfile
import uuid

from fastapi import UploadFile

from thesis_review.engine import review

CHUNK_SIZE = 1024 * 1024
DOCX_MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
JSON_MIME = "application/json"


class InvalidUpload(ValueError):
    """用户上传内容不符合首版 Web 接口要求。"""


@dataclass(frozen=True)
class WebReviewResult:
    output_path: Path
    issues_json: Path
    download_name: str
    cleanup: Callable[[], None]


@dataclass(frozen=True)
class WebReviewArtifacts:
    body: bytes
    media_type: str
    cleanup: Callable[[], None]


def _client_filename(filename: str | None) -> str:
    if not filename:
        raise InvalidUpload("请选择 .docx 文件")
    name = filename.replace("\\", "/").split("/")[-1].strip()
    if not name:
        raise InvalidUpload("请选择 .docx 文件")
    if Path(name).suffix.lower() != ".docx":
        raise InvalidUpload("仅支持 .docx 文件")
    return name


def _download_name(filename: str) -> str:
    stem = Path(filename).stem
    return f"{stem}.marked.docx"


def _save_upload(upload: UploadFile, target: Path) -> None:
    with target.open("wb") as f:
        while True:
            chunk = upload.file.read(CHUNK_SIZE)
            if not chunk:
                break
            f.write(chunk)


def _multipart_part(
    boundary: str,
    *,
    name: str,
    filename: str,
    media_type: str,
    content: bytes,
) -> bytes:
    headers = (
        f"--{boundary}\r\n"
        f'Content-Disposition: attachment; name="{name}"; filename="{filename}"\r\n'
        f"Content-Type: {media_type}\r\n"
        "\r\n"
    ).encode("utf-8")
    return headers + content + b"\r\n"


def _review_artifacts(result: WebReviewResult) -> WebReviewArtifacts:
    boundary = f"thesis-review-{uuid.uuid4().hex}"
    body = b"".join(
        [
            _multipart_part(
                boundary,
                name="marked_docx",
                filename="marked.docx",
                media_type=DOCX_MIME,
                content=result.output_path.read_bytes(),
            ),
            _multipart_part(
                boundary,
                name="issues_json",
                filename="issues.json",
                media_type=JSON_MIME,
                content=result.issues_json.read_bytes(),
            ),
            f"--{boundary}--\r\n".encode("utf-8"),
        ]
    )
    return WebReviewArtifacts(
        body=body,
        media_type=f'multipart/mixed; boundary="{boundary}"',
        cleanup=result.cleanup,
    )


def review_upload(upload: UploadFile) -> WebReviewResult:
    filename = _client_filename(upload.filename)
    workdir = Path(tempfile.mkdtemp(prefix="thesis-review-"))
    input_path = workdir / "input.docx"
    out_dir = workdir / "review"

    def cleanup() -> None:
        shutil.rmtree(workdir, ignore_errors=True)

    try:
        _save_upload(upload, input_path)
        result = review(str(input_path), out_dir)
    except Exception:
        cleanup()
        raise

    return WebReviewResult(
        output_path=result.marked_docx,
        issues_json=result.issues_json,
        download_name=_download_name(filename),
        cleanup=cleanup,
    )


def review_upload_artifacts(upload: UploadFile) -> WebReviewArtifacts:
    result = review_upload(upload)
    try:
        return _review_artifacts(result)
    except Exception:
        result.cleanup()
        raise
