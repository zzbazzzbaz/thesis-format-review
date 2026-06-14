"""UNO 写：红色底纹 + 批注 → marked.docx。

唯一写文档的模块。按 Issue.location 用与 extractor 同一套 UNO 枚举顺序
定位块/portion，给目标 text range 加红色字符底纹并插入批注，另存为
marked.docx。定位失败跳过该 issue，不崩溃。

段落级 issue 会对该段所有 portion 设底纹，因 OOXML 不保留段落级
CharBackColor，save+reload 后会丢失。
"""
from __future__ import annotations

import logging

import uno
from com.sun.star.beans import PropertyValue

from thesis_review.models import Issue
from thesis_review.uno_session import path_to_url
from thesis_review.uno_traversal import TraversedBlock
from thesis_review.uno_traversal import blocks as iter_blocks
from thesis_review.uno_traversal import text_portions

log = logging.getLogger(__name__)

_RED = 0xFF0000


def _add_comment(doc, target, message: str) -> None:
    """在目标 text range 起点插入批注。"""
    ann = doc.createInstance("com.sun.star.text.textfield.Annotation")
    ann.Content = message
    ann.Author = "审核系统"
    cursor = doc.Text.createTextCursorByRange(target.getStart())
    doc.Text.insertTextContent(cursor, ann, False)


def _apply_paragraph_issue(doc, para, issue: Issue) -> None:
    if issue.location.target == "run" and issue.location.run_index is not None:
        portions = text_portions(para)
        r_idx = issue.location.run_index
        if r_idx < 0 or r_idx >= len(portions):
            log.warning("未能标注(run 越界)：%s @ flow=%s r=%s",
                        issue.rule_id, issue.location.flow_index, r_idx)
            return
        expected_run_id = f"{issue.location.block_id}-r-{r_idx:04d}"
        if issue.location.run_id != expected_run_id:
            log.warning(
                "未能标注(run id 不匹配)：%s @ expected=%s actual=%s",
                issue.rule_id,
                expected_run_id,
                issue.location.run_id,
            )
            return
        target = portions[r_idx]
        target.CharBackColor = _RED
        _add_comment(doc, target, issue.message)
        return

    # 段落块级：对所有 portion 设底纹，批注锚在第一个 portion
    portions = text_portions(para)
    if not portions:
        return
    for p in portions:
        p.CharBackColor = _RED
    _add_comment(doc, portions[0], issue.message)


def _apply_issue(doc, doc_blocks: list[TraversedBlock], issue: Issue) -> None:
    """对单个 Issue 写入红色底纹和批注。

    段落级 issue：对该段所有 portion 设底纹（因 OOXML 不保留段落级
    CharBackColor，写后重开会丢失）。
    run 级 issue：仅对该 portion 设底纹。
    定位失败：记录 warning 并跳过。
    """
    flow_index = issue.location.flow_index
    if flow_index < 0 or flow_index >= len(doc_blocks):
        log.warning("未能标注(块越界)：%s @ flow_index=%s",
                    issue.rule_id, flow_index)
        return
    expected_block_id = f"b-{flow_index:04d}"
    if issue.location.block_id != expected_block_id:
        log.warning(
            "未能标注(块 id 不匹配)：%s @ expected=%s actual=%s",
            issue.rule_id,
            expected_block_id,
            issue.location.block_id,
        )
        return
    block = doc_blocks[flow_index]
    if block.kind != issue.location.block_kind:
        log.warning(
            "未能标注(块类型不匹配)：%s @ expected=%s actual=%s",
            issue.rule_id,
            issue.location.block_kind,
            block.kind,
        )
        return

    if block.kind == "paragraph":
        _apply_paragraph_issue(doc, block.element, issue)
        return

    log.warning("未能标注(暂不支持的块类型)：%s @ kind=%s",
                issue.rule_id, block.kind)


def annotate(session, input_docx: str, output_docx: str,
             issues: list[Issue]) -> None:
    """对一篇 docx 写入红色底纹和批注，另存为 marked.docx。

    Args:
        session: UnoSession 实例
        input_docx: 源文件路径（只读，不修改）
        output_docx: 输出路径（marked.docx）
        issues: 需要标注的问题列表
    """
    with session.open(input_docx) as doc:
        doc_blocks = iter_blocks(doc)
        for issue in issues:
            try:
                _apply_issue(doc, doc_blocks, issue)
            except Exception:  # noqa: BLE001 — 单个 issue 失败不影响其余
                log.exception(
                    "未能标注(写入失败)：%s @ flow_index=%s",
                    issue.rule_id,
                    issue.location.flow_index,
                )

        url = path_to_url(output_docx)
        doc.storeToURL(url, (
            PropertyValue(Name="FilterName", Value="MS Word 2007 XML"),))
