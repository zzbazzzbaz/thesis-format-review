"""pytest 共享 fixture 与配置。"""
from __future__ import annotations

from pathlib import Path

import pytest

HERE = Path(__file__).parent
FIXTURES = HERE / "fixtures"
WPS_DIR = HERE / "word手工编辑版"


@pytest.fixture
def sample_docx() -> str:
    """python-docx 程序化生成的基线 fixture。"""
    return str(FIXTURES / "sample.docx")


@pytest.fixture
def wps_docx() -> str:
    """WPS macOS 手工编辑后另存的真实 docx。"""
    return str(WPS_DIR / "MACOS_WPS编辑版.docx")


@pytest.fixture
def clean_thesis_docx() -> str:
    """格式无误的论文（WPS 编辑，生产级格式）。"""
    return str(WPS_DIR / "格式无误_人工智能发展史.docx")
