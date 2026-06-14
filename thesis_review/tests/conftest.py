"""pytest 共享 fixture 与配置。"""
from __future__ import annotations

from pathlib import Path

import pytest

HERE = Path(__file__).parent
FIXTURES = HERE / "fixtures"
WORD_FIXTURES = HERE / "word"


@pytest.fixture
def sample_docx() -> str:
    """python-docx 程序化生成的基线 fixture。"""
    return str(FIXTURES / "sample.docx")


@pytest.fixture
def wps_docx() -> str:
    """WPS macOS 手工编辑后另存的真实 docx。"""
    return str(WORD_FIXTURES / "111.docx")


@pytest.fixture
def clean_thesis_docx() -> str:
    """格式无误的论文（WPS 编辑，生产级格式）。"""
    return str(WORD_FIXTURES / "论文规范.docx")
