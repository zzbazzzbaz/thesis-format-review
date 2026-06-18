"""串联三步：extract → rules → annotate。"""
from __future__ import annotations

from thesis_review.core.models import Issue
from thesis_review.rules.context import build_rule_context
from thesis_review.rules.registry import get_checkers


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
        context = build_rule_context(document)
        issues: list[Issue] = []
        for checker in get_checkers():
            issues.extend(checker.check(context))
        annotate(session, input_docx, output_docx, issues)
    return issues
