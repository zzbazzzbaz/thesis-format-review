"""串联三步：extract → rules → annotate。"""
from __future__ import annotations

from thesis_review.models import Issue
from thesis_review.rules.registry import get_rules


def review(input_docx: str, output_docx: str) -> list[Issue]:
    """对一篇 .docx 执行完整审核。

    Args:
        input_docx: 输入 .docx 路径
        output_docx: 输出 marked.docx 路径

    Returns:
        list[Issue]: 所有规则检测到的问题
    """
    from thesis_review.annotator import annotate
    from thesis_review.extractor import extract
    from thesis_review.uno_session import UnoSession

    with UnoSession() as session:
        with session.open(input_docx) as doc:
            document = extract(doc, source_path=input_docx)
        issues: list[Issue] = []
        for rule in get_rules():
            issues.extend(rule.check(document))
        annotate(session, input_docx, output_docx, issues)
    return issues
