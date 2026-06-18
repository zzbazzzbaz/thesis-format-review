"""pytest 共享 fixture 与配置。"""
from __future__ import annotations

from pathlib import Path

import pytest

TESTS_ROOT = Path(__file__).parent
PROJECT_ROOT = TESTS_ROOT.parent
RULES_ROOT = PROJECT_ROOT / "docs" / "rules"


@pytest.fixture
def rules_root() -> Path:
    return RULES_ROOT


def _rule_sample(module: str, filename: str) -> str:
    path = RULES_ROOT / module / "samples" / filename
    if not path.exists():
        pytest.skip(f"规则样本未准备：{path}")
    return str(path)


@pytest.fixture
def sample_docx() -> str:
    return _rule_sample("table-of-contents", "table-of-contents-title-format.docx")


@pytest.fixture
def clean_thesis_docx() -> str:
    return _rule_sample("table-of-contents", "table-of-contents-clean.docx")
