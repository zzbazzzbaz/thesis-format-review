"""Web HTTP 路由。"""
from __future__ import annotations

import logging
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile
from starlette.background import BackgroundTask
from starlette.responses import FileResponse, Response

from thesis_review.interfaces.web import services

log = logging.getLogger(__name__)

STATIC_DIR = Path(__file__).parent / "static"

router = APIRouter()


@router.get("/", include_in_schema=False)
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@router.head("/", include_in_schema=False)
def index_head() -> Response:
    return Response(status_code=200)


@router.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}


@router.post(
    "/api/review",
    responses={
        200: {
            "description": "审核产物，包含 marked_docx 和 issues_json 两个 multipart part",
            "content": {"multipart/mixed": {}},
        }
    },
)
def review_endpoint(file: UploadFile = File(...)) -> Response:
    log.info("review start: filename=%s size=%s", file.filename, getattr(file, "size", "?"))
    try:
        artifacts = services.review_upload_artifacts(file)
    except services.InvalidUpload as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        log.exception("review failed: filename=%s", file.filename)
        raise HTTPException(status_code=500, detail="审核失败，请稍后重试") from exc

    log.info("review done: filename=%s", file.filename)

    return Response(
        content=artifacts.body,
        media_type=artifacts.media_type,
        background=BackgroundTask(artifacts.cleanup),
    )
