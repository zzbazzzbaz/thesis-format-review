"""Web HTTP 路由。"""
from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile
from starlette.background import BackgroundTask
from starlette.responses import FileResponse, Response

from thesis_review.interfaces.web import services

DOCX_MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
STATIC_DIR = Path(__file__).parent / "static"

router = APIRouter()


@router.get("/", include_in_schema=False)
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@router.head("/", include_in_schema=False)
def index_head() -> Response:
    return Response(status_code=200)


@router.post("/api/review")
async def review_endpoint(file: UploadFile = File(...)) -> FileResponse:
    try:
        result = await services.review_upload(file)
    except services.InvalidUpload as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="审核失败，请稍后重试") from exc

    return FileResponse(
        result.output_path,
        media_type=DOCX_MIME,
        filename=result.download_name,
        background=BackgroundTask(result.cleanup),
    )
