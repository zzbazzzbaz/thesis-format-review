"""串联三步：extract → rules → annotate。"""
from __future__ import annotations

import logging

from src.models import Issue
from src.extractor import extract
from src.annotator import annotate
from src.rules.registry import get_rules
from src.uno_session import UnoSession

log = logging.getLogger(__name__)


def review(input_docx: str, output_docx: str) -> list[Issue]:
    """对一篇 .docx 执行完整审核。

    Args:
        input_docx: 输入 .docx 路径
        output_docx: 输出 marked.docx 路径

    Returns:
        list[Issue]: 所有规则检测到的问题
    """
    with UnoSession() as session:
        with session.open(input_docx) as doc:
            document = extract(doc, source_path=input_docx)
        issues: list[Issue] = []
        for rule in get_rules():
            try:
                issues.extend(rule.check(document))
            except Exception:  # noqa: BLE001 — 单条规则异常不影响其余
                log.exception("规则执行失败：%s", rule.rule_id)
        annotate(session, input_docx, output_docx, issues)
    return issues
