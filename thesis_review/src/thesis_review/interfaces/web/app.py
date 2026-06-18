"""FastAPI 应用工厂入口。"""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from thesis_review.interfaces.web.routes import STATIC_DIR, router

app = FastAPI(title="毕业设计格式审核系统")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
app.include_router(router)
