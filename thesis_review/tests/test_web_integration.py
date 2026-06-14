"""Web + pipeline 端到端测试。"""
from __future__ import annotations

import zipfile

import pytest
from fastapi.testclient import TestClient

from thesis_review.web.app import app

DOCX_MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


@pytest.mark.uno
def test_web_review_endpoint_runs_pipeline_and_returns_docx(sample_docx, tmp_path):
    client = TestClient(app)

    with open(sample_docx, "rb") as f:
        response = client.post(
            "/api/review",
            files={"file": ("sample.docx", f, DOCX_MIME)},
        )

    assert response.status_code == 200
    assert response.headers["content-type"] == DOCX_MIME
    assert 'filename="sample.marked.docx"' in response.headers["content-disposition"]
    out = tmp_path / "sample.marked.docx"
    out.write_bytes(response.content)
    assert zipfile.is_zipfile(out)

    from thesis_review.uno_session import UnoSession

    with UnoSession() as session:
        with session.open(str(out)) as doc:
            assert doc.getText().getString()
