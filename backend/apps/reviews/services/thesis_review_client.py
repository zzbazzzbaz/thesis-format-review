from __future__ import annotations

from dataclasses import dataclass
from email import policy
from email.parser import BytesParser

import httpx
from django.conf import settings


class ThesisReviewClientError(RuntimeError):
    def __init__(self, public_message: str) -> None:
        super().__init__(public_message)
        self.public_message = public_message


@dataclass(frozen=True)
class ThesisReviewArtifacts:
    marked_docx: bytes
    issues_json: bytes


class ThesisReviewClient:
    def __init__(self, base_url: str | None = None, timeout_seconds: float | None = None) -> None:
        self.base_url = (base_url or settings.THESIS_REVIEW_BASE_URL).rstrip("/")
        self.timeout_seconds = timeout_seconds or settings.THESIS_REVIEW_TIMEOUT_SECONDS

    def health_check(self) -> bool:
        try:
            response = httpx.get(f"{self.base_url}/healthz", timeout=10)
        except httpx.HTTPError:
            return False
        return response.status_code == 200

    def review_docx(self, path: str, filename: str = "source.docx") -> ThesisReviewArtifacts:
        try:
            with open(path, "rb") as source:
                response = httpx.post(
                    f"{self.base_url}/api/review",
                    files={
                        "file": (
                            filename,
                            source,
                            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        )
                    },
                    timeout=self.timeout_seconds,
                )
        except (OSError, httpx.TimeoutException, httpx.ConnectError) as exc:
            raise ThesisReviewClientError("审核服务暂不可用") from exc
        except httpx.HTTPError as exc:
            raise ThesisReviewClientError("审核服务处理失败") from exc

        if response.status_code == 400:
            raise ThesisReviewClientError("审核服务拒绝该文件")
        if response.status_code >= 500:
            raise ThesisReviewClientError("审核服务暂不可用")
        if response.status_code != 200:
            raise ThesisReviewClientError("审核服务处理失败")
        return parse_multipart_artifacts(
            response.content,
            response.headers.get("content-type", ""),
        )


def parse_multipart_artifacts(content: bytes, content_type: str) -> ThesisReviewArtifacts:
    if not content_type.startswith("multipart/mixed"):
        raise ThesisReviewClientError("审核服务返回格式不正确")
    raw_message = (
        f"Content-Type: {content_type}\r\n"
        "MIME-Version: 1.0\r\n"
        "\r\n"
    ).encode("utf-8") + content
    message = BytesParser(policy=policy.default).parsebytes(raw_message)
    if not message.is_multipart():
        raise ThesisReviewClientError("审核服务返回格式不正确")
    parts: dict[str, bytes] = {}
    for part in message.iter_parts():
        name = part.get_param("name", header="content-disposition")
        if name:
            parts[name] = part.get_payload(decode=True) or b""
    try:
        marked_docx = parts["marked_docx"]
        issues_json = parts["issues_json"]
    except KeyError as exc:
        raise ThesisReviewClientError("审核服务返回结果缺失") from exc
    if not marked_docx or not issues_json:
        raise ThesisReviewClientError("审核服务返回结果为空")
    return ThesisReviewArtifacts(marked_docx=marked_docx, issues_json=issues_json)
