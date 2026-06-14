"""UNO 写：红色底纹 + 批注 → marked.docx。

唯一写文档的模块。按 Issue.location 用与 extractor 同一套 UNO 枚举顺序
定位段落/portion，给目标 text range 加红色字符底纹并插入批注，另存为
marked.docx。定位失败跳过该 issue，不崩溃。

段落级 issue 会对该段所有 portion 设底纹，因 OOXML 不保留段落级
CharBackColor，save+reload 后会丢失。
"""
from __future__ import annotations

import logging

import uno
from com.sun.star.beans import PropertyValue

from src.models import Issue

log = logging.getLogger(__name__)

_RED = 0xFF0000


def _paragraphs(doc) -> list:
    """枚举文档中的非空段落，与 extractor 过滤规则一致。

    必须跳过非 Paragraph service 的元素和空段落，
    以保证 paragraph_index 与 extractor 产出匹配。
    """
    out = []
    enum = doc.Text.createEnumeration()
    while enum.hasMoreElements():
        elem = enum.nextElement()
        if not elem.supportsService("com.sun.star.text.Paragraph"):
            continue
        if not elem.getString():
            continue
        out.append(elem)
    return out


def _portions(para) -> list:
    """枚举段落中的非空 Text portion，与 extractor 过滤规则一致。"""
    out = []
    enum = para.createEnumeration()
    while enum.hasMoreElements():
        p = enum.nextElement()
        if getattr(p, "TextPortionType", "Text") == "Text" and p.getString():
            out.append(p)
    return out


def _add_comment(doc, target, message: str) -> None:
    """在目标 text range 起点插入批注。"""
    ann = doc.createInstance("com.sun.star.text.textfield.Annotation")
    ann.Content = message
    ann.Author = "审核系统"
    cursor = doc.Text.createTextCursorByRange(target.getStart())
    doc.Text.insertTextContent(cursor, ann, False)


def _apply_issue(doc, paras, issue: Issue) -> None:
    """对单个 Issue 写入红色底纹和批注。

    段落级 issue：对该段所有 portion 设底纹（因 OOXML 不保留段落级
    CharBackColor，写后重开会丢失）。
    run 级 issue：仅对该 portion 设底纹。
    定位失败：记录 warning 并跳过。
    """
    p_idx = issue.location.paragraph_index
    if p_idx < 0 or p_idx >= len(paras):
        log.warning("未能标注(段落越界)：%s @ paragraph_index=%s",
                    issue.rule_id, p_idx)
        return
    para = paras[p_idx]

    if issue.location.kind == "run" and issue.location.run_index is not None:
        portions = _portions(para)
        r_idx = issue.location.run_index
        if r_idx < 0 or r_idx >= len(portions):
            log.warning("未能标注(run 越界)：%s @ p=%s r=%s",
                        issue.rule_id, p_idx, r_idx)
            return
        target = portions[r_idx]
        target.CharBackColor = _RED
        _add_comment(doc, target, issue.message)
        return

    # 段落级：对所有 portion 设底纹，批注锚在第一个 portion
    portions = _portions(para)
    if not portions:
        return
    for p in portions:
        p.CharBackColor = _RED
    _add_comment(doc, portions[0], issue.message)


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
        paras = _paragraphs(doc)
        for issue in issues:
            try:
                _apply_issue(doc, paras, issue)
            except Exception:  # noqa: BLE001 — 单个 issue 失败不影响其余
                log.warning("未能标注(写入失败)：%s @ paragraph_index=%s",
                            issue.rule_id, issue.location.paragraph_index)

        url = uno.systemPathToFileUrl(output_docx)
        doc.storeToURL(url, (
            PropertyValue(Name="FilterName", Value="MS Word 2007 XML"),))
