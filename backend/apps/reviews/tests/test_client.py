from __future__ import annotations

import pytest

from apps.reviews.services.thesis_review_client import (
    ThesisReviewClientError,
    parse_multipart_artifacts,
)


def multipart_body(boundary: str, include_issues: bool = True) -> bytes:
    parts = [
        (
            f"--{boundary}\r\n"
            'Content-Disposition: attachment; name="marked_docx"; filename="marked.docx"\r\n'
            "Content-Type: application/vnd.openxmlformats-officedocument.wordprocessingml.document\r\n"
            "\r\n"
        ).encode()
        + b"marked"
        + b"\r\n"
    ]
    if include_issues:
        parts.append(
            (
                f"--{boundary}\r\n"
                'Content-Disposition: attachment; name="issues_json"; filename="issues.json"\r\n'
                "Content-Type: application/json\r\n"
                "\r\n"
            ).encode()
            + b'{"issues":[]}'
            + b"\r\n"
        )
    parts.append(f"--{boundary}--\r\n".encode())
    return b"".join(parts)


def test_parse_multipart_artifacts_success():
    artifacts = parse_multipart_artifacts(
        multipart_body("x"),
        'multipart/mixed; boundary="x"',
    )

    assert artifacts.marked_docx == b"marked"
    assert artifacts.issues_json == b'{"issues":[]}'


def test_parse_multipart_artifacts_rejects_missing_part():
    with pytest.raises(ThesisReviewClientError):
        parse_multipart_artifacts(
            multipart_body("x", include_issues=False),
            'multipart/mixed; boundary="x"',
        )
