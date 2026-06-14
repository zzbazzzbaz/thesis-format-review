"""FastAPI Web 路由测试。"""
from __future__ import annotations

from fastapi.testclient import TestClient

from thesis_review.web import services
from thesis_review.web.app import app

DOCX_MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


def test_get_index_returns_upload_page():
    client = TestClient(app)

    response = client.get("/")

    assert response.status_code == 200
    assert '<input id="file"' in response.text
    assert 'accept=".docx"' in response.text


def test_head_index_returns_ok_for_curl_smoke_check():
    client = TestClient(app)

    response = client.head("/")

    assert response.status_code == 200


def test_post_review_returns_file_response(monkeypatch, tmp_path):
    output = tmp_path / "marked.docx"
    output.write_bytes(b"marked")
    cleaned: list[bool] = []

    async def fake_review_upload(upload):
        assert upload.filename == "paper.docx"
        return services.ReviewResult(
            output_path=output,
            download_name="paper.marked.docx",
            cleanup=lambda: cleaned.append(True),
        )

    monkeypatch.setattr(services, "review_upload", fake_review_upload)
    client = TestClient(app)

    response = client.post(
        "/api/review",
        files={"file": ("paper.docx", b"input", DOCX_MIME)},
    )

    assert response.status_code == 200
    assert response.content == b"marked"
    assert response.headers["content-type"] == DOCX_MIME
    assert 'filename="paper.marked.docx"' in response.headers["content-disposition"]
    assert cleaned == [True]


def test_post_review_maps_invalid_upload_to_400(monkeypatch):
    async def fake_review_upload(upload):
        raise services.InvalidUpload("仅支持 .docx 文件")

    monkeypatch.setattr(services, "review_upload", fake_review_upload)
    client = TestClient(app)

    response = client.post(
        "/api/review",
        files={"file": ("paper.pdf", b"input", "application/pdf")},
    )

    assert response.status_code == 400
    assert response.json() == {"detail": "仅支持 .docx 文件"}


def test_post_review_500_does_not_expose_server_path(monkeypatch):
    async def fake_review_upload(upload):
        raise RuntimeError("/tmp/secret/path failed")

    monkeypatch.setattr(services, "review_upload", fake_review_upload)
    client = TestClient(app)

    response = client.post(
        "/api/review",
        files={"file": ("paper.docx", b"input", DOCX_MIME)},
    )

    assert response.status_code == 500
    assert response.json() == {"detail": "审核失败，请稍后重试"}
    assert "secret" not in response.text


def test_static_css_is_served():
    client = TestClient(app)

    response = client.get("/static/style.css")

    assert response.status_code == 200
    assert "body" in response.text
