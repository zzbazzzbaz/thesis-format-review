"""engine 测试：extract → rules → annotate 端到端。"""
from __future__ import annotations

import pytest

from thesis_review.engine import review


@pytest.mark.uno
def test_review_returns_issues_and_writes_output(tmp_path, sample_docx):
    """对 sample.docx 运行完整审核，产出 marked.docx 且含当前启用规则问题。"""
    result = review(sample_docx, tmp_path / "out")
    issues = result.issues
    assert result.marked_docx.exists()
    assert result.issues_json.exists()
    ids = {i.rule_id for i in issues}
    table_of_contents_rule_ids = {
        "table-of-contents-title-001",
        "table-of-contents-title-002",
        "table-of-contents-title-003",
        "table-of-contents-title-004",
        "table-of-contents-title-005",
        "table-of-contents-title-006",
        "table-of-contents-entry-001",
        "table-of-contents-entry-002",
        "table-of-contents-entry-003",
        "table-of-contents-entry-004",
        "table-of-contents-entry-005",
        "table-of-contents-entry-006",
        "table-of-contents-entry-007",
        "table-of-contents-entry-008",
    }
    assert ids & table_of_contents_rule_ids


@pytest.mark.uno
def test_review_marked_docx_has_annotations(tmp_path, sample_docx):
    """审核后的 marked.docx 应包含批注。"""
    result = review(sample_docx, tmp_path / "out")
    issues = result.issues
    assert len(issues) >= 1
    from thesis_review.uno_session import UnoSession

    with UnoSession() as session:
        with session.open(str(result.marked_docx)) as doc:
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

    当前启用规则只检查目录范围；正文、参考文献等区域规则后续按业务编号重建。
    """
    result = review(clean_thesis_docx, tmp_path / "out")
    issues = result.issues
    assert result.marked_docx.exists()
    assert result.issues_json.exists()
    assert isinstance(issues, list)
    # 至少不崩溃，产出合法的 issue list
