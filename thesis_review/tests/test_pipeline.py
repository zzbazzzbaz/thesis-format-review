"""pipeline 测试：extract → rules → annotate 端到端。"""
from __future__ import annotations

import os

import pytest

from thesis_review.pipeline import review


@pytest.mark.uno
def test_review_returns_issues_and_writes_output(tmp_path, sample_docx):
    """对 sample.docx 运行完整审核，产出 marked.docx 且含当前启用规则问题。"""
    out = str(tmp_path / "marked.docx")
    issues = review(sample_docx, out)
    assert os.path.exists(out)
    ids = {i.rule_id for i in issues}
    assert "C001" in ids


@pytest.mark.uno
def test_review_marked_docx_has_annotations(tmp_path, sample_docx):
    """审核后的 marked.docx 应包含批注。"""
    out = str(tmp_path / "marked.docx")
    issues = review(sample_docx, out)
    assert len(issues) >= 1
    from thesis_review.uno_session import UnoSession
    with UnoSession() as session:
        with session.open(out) as doc:
            fields = doc.getTextFields().createEnumeration()
            texts = []
            while fields.hasMoreElements():
                f = fields.nextElement()
                if f.supportsService("com.sun.star.text.textfield.Annotation"):
                    texts.append(f.Content)
    assert len(texts) > 0, "marked.docx 应包含批注"


@pytest.mark.uno
def test_review_clean_thesis_produces_output(clean_thesis_docx, tmp_path):
    """格式无误的真实论文能正常跑通审核，产出 marked.docx 不崩溃。

    注意：该论文封面/摘要/关键词/参考文献未使用 Heading 样式，
    导致 RequiredSectionRule 检查标题时找不到这些章节。
    这是真实 WPS 论文的常见现象，后续需放宽规则（如查正文前几段的文本）。
    """
    out = str(tmp_path / "marked.docx")
    issues = review(clean_thesis_docx, out)
    assert os.path.exists(out)
    assert isinstance(issues, list)
    # 至少不崩溃，产出合法的 issue list
