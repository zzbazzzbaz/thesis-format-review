"""UNO 会话测试：需要 LibreOffice/UNO 环境（Docker 容器内运行）。

在没有 UNO 的环境下，整个模块级 import 会失败（import uno）。
此时 pytest 在模块加载阶段就会报 ImportError，而非优雅跳过。
因此先尝试 import uno；失败时用 pytest.skip 跳过整个模块。
"""
from __future__ import annotations

import pytest

pytest.importorskip("uno")  # 无 UNO 环境时跳过整个模块

from thesis_review.uno_session import UnoSession


@pytest.mark.uno
def test_session_opens_and_closes_document(sample_docx):
    """验证能打开 docx 并拿到可识别的文本文档组件。"""
    with UnoSession() as session:
        assert session.is_ready(), "UNO 连接应就绪"
        with session.open(sample_docx) as doc:
            assert doc.supportsService("com.sun.star.text.TextDocument"), (
                "应返回文本文档服务"
            )


@pytest.mark.uno
def test_session_health_check_reports_soffice(sample_docx):
    """验证 is_ready() 健康检查。"""
    with UnoSession() as session:
        assert session.is_ready()


@pytest.mark.uno
def test_session_opens_wps_docx(wps_docx):
    """验证能打开 WPS macOS 手工编辑版 docx。"""
    with UnoSession() as session:
        with session.open(wps_docx) as doc:
            assert doc.supportsService("com.sun.star.text.TextDocument"), (
                "WPS 编辑版也应被识别为文本文档服务"
            )


@pytest.mark.uno
def test_session_can_reattach(wps_docx):
    """验证同一个 session 可以先后打开两个文档。"""
    with UnoSession() as session:
        with session.open(wps_docx) as doc1:
            assert doc1.supportsService("com.sun.star.text.TextDocument")
        with session.open(wps_docx) as doc2:
            assert doc2.supportsService("com.sun.star.text.TextDocument")
