"""上传文件保存、审核调用和临时文件生命周期管理。"""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
import shutil
import tempfile

from fastapi import UploadFile

from thesis_review import pipeline

CHUNK_SIZE = 1024 * 1024


class InvalidUpload(ValueError):
    """用户上传内容不符合首版 Web 接口要求。"""


@dataclass(frozen=True)
class ReviewResult:
    output_path: Path
    download_name: str
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


async def _save_upload(upload: UploadFile, target: Path) -> None:
    with target.open("wb") as f:
        while True:
            chunk = await upload.read(CHUNK_SIZE)
            if not chunk:
                break
            f.write(chunk)


async def review_upload(upload: UploadFile) -> ReviewResult:
    filename = _client_filename(upload.filename)
    workdir = Path(tempfile.mkdtemp(prefix="thesis-review-"))
    input_path = workdir / "input.docx"
    output_path = workdir / "output.marked.docx"

    def cleanup() -> None:
        shutil.rmtree(workdir, ignore_errors=True)

    try:
        await _save_upload(upload, input_path)
        pipeline.review(str(input_path), str(output_path))
    except Exception:
        cleanup()
        raise

    return ReviewResult(
        output_path=output_path,
        download_name=_download_name(filename),
        cleanup=cleanup,
    )
