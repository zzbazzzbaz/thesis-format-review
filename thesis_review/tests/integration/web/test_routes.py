"""FastAPI Web 路由测试。"""
from __future__ import annotations

from email.parser import BytesParser
from email.policy import default

from fastapi.testclient import TestClient

from thesis_review.interfaces.web import services
from thesis_review.interfaces.web.app import app

DOCX_MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


def parse_multipart_response(response):
    raw = (
        b"Content-Type: "
        + response.headers["content-type"].encode("utf-8")
        + b"\r\nMIME-Version: 1.0\r\n\r\n"
        + response.content
    )
    return BytesParser(policy=default).parsebytes(raw)


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


def test_healthz_returns_ok():
    client = TestClient(app)

    response = client.get("/healthz")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_post_review_returns_marked_docx_and_issues_json(
    monkeypatch,
    tmp_path,
):
    marked_docx = tmp_path / "marked.docx"
    issues_json = tmp_path / "issues.json"
    marked_docx.write_bytes(b"marked")
    issues_json.write_text('{"issues": []}', encoding="utf-8")
    cleaned: list[bool] = []

    def fake_review_upload(upload):
        assert upload.filename == "paper.docx"
        return services.WebReviewResult(
            output_path=marked_docx,
            issues_json=issues_json,
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
    assert response.headers["content-type"].startswith("multipart/mixed")
    message = parse_multipart_response(response)
    parts = list(message.iter_parts())

    assert len(parts) == 2
    assert parts[0]["content-disposition"] == (
        'attachment; name="marked_docx"; filename="marked.docx"'
    )
    assert parts[0].get_content_type() == DOCX_MIME
    assert parts[0].get_payload(decode=True) == b"marked"
    assert parts[1]["content-disposition"] == (
        'attachment; name="issues_json"; filename="issues.json"'
    )
    assert parts[1].get_content_type() == "application/json"
    assert parts[1].get_payload(decode=True) == b'{"issues": []}'
    assert cleaned == [True]


def test_post_review_artifacts_route_is_removed():
    client = TestClient(app)

    response = client.post(
        "/api/review/artifacts",
        files={"file": ("paper.docx", b"input", DOCX_MIME)},
    )

    assert response.status_code == 404


def test_post_review_maps_invalid_upload_to_400(monkeypatch):
    def fake_review_upload(upload):
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
    def fake_review_upload(upload):
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
