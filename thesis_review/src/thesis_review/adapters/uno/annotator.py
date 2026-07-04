"""UNO 写：红色底纹 + 批注 → marked.docx。

唯一写文档的模块。按 Issue.location 用与 extractor 同一套 UNO 枚举顺序
定位块/portion，给目标 text range 加红色字符底纹并插入批注，另存为
marked.docx。定位失败跳过该 issue，不崩溃。

性能优化：按段落分组处理——同一段落的多个 issue 只枚举一次 portions、
每 portion 只设一次底纹、合并为一条批注。对 issue 数量极大的文档，
按严重度排序后截断到上限，超出部分只进 issues.json 不进 marked.docx。
"""
from __future__ import annotations

import logging
from collections import defaultdict

import uno
from com.sun.star.beans import PropertyValue

from thesis_review.core.models import Issue
from thesis_review.adapters.ooxml.font_assets import restore_font_assets
from thesis_review.adapters.ooxml.math_content import restore_math_content
from thesis_review.adapters.uno.session import path_to_url
from thesis_review.adapters.uno.traversal import TraversedBlock
from thesis_review.adapters.uno.traversal import blocks as iter_blocks
from thesis_review.adapters.uno.traversal import text_portions

log = logging.getLogger(__name__)

_RED = 0xFF0000
_DEFAULT_MAX_ANNOTATIONS = 500
_SEVERITY_ORDER = {"error": 0, "warning": 1, "info": 2}


def _add_comment(doc, target, author: str, message: str) -> None:
    """在目标 text range 起点插入批注。"""
    ann = doc.createInstance("com.sun.star.text.textfield.Annotation")
    ann.Content = message
    ann.Author = author
    cursor = doc.Text.createTextCursorByRange(target.getStart())
    doc.Text.insertTextContent(cursor, ann, False)


def _validate_issue_block(issue: Issue, doc_blocks: list[TraversedBlock]) -> TraversedBlock | None:
    """校验 issue 的块定位，返回对应块或 None（并记 warning）。"""
    flow_index = issue.location.flow_index
    if flow_index < 0 or flow_index >= len(doc_blocks):
        log.warning("未能标注(块越界)：%s @ flow_index=%s", issue.rule_id, flow_index)
        return None
    expected_block_id = f"b-{flow_index:04d}"
    if issue.location.block_id != expected_block_id:
        log.warning("未能标注(块 id 不匹配)：%s @ expected=%s actual=%s",
                    issue.rule_id, expected_block_id, issue.location.block_id)
        return None
    block = doc_blocks[flow_index]
    if block.kind != issue.location.block_kind:
        log.warning("未能标注(块类型不匹配)：%s @ expected=%s actual=%s",
                    issue.rule_id, issue.location.block_kind, block.kind)
        return None
    return block


def _collect_color_targets(block_issues: list[Issue], portion_count: int) -> set[int]:
    """收集需要着色的 portion 索引集合。

    block 级 issue → 全部 portion；run 级 issue → 指定 run_index。
    """
    indices: set[int] = set()
    for issue in block_issues:
        if issue.location.target == "run" and issue.location.run_index is not None:
            r_idx = issue.location.run_index
            if 0 <= r_idx < portion_count:
                indices.add(r_idx)
            else:
                log.warning("未能标注(run 越界)：%s @ flow=%s r=%s",
                            issue.rule_id, issue.location.flow_index, r_idx)
        else:
            indices.update(range(portion_count))
    return indices


def _annotate_paragraph_block(doc, block: TraversedBlock, block_issues: list[Issue]) -> None:
    """对单个段落块写入底纹 + 合并批注。

    portions 只枚举一次；每 portion 只着色一次；所有 issue 合并为一条批注。
    """
    para = block.element
    portions = text_portions(para)
    if not portions:
        return

    # 着色：收集目标索引，每 portion 只设一次
    color_targets = _collect_color_targets(block_issues, len(portions))
    for idx in color_targets:
        portions[idx].CharBackColor = _RED

    # 合并批注：author 取第一个 issue 的 rule_id，内容列出全部
    author = block_issues[0].rule_id
    lines = [f"[{issue.rule_id}] {issue.message}" for issue in block_issues]
    _add_comment(doc, portions[0], author, "\n".join(lines))


def _group_issues_by_block(issues: list[Issue]) -> dict[int, list[Issue]]:
    """按 flow_index 分组，保留每组内的 issue 顺序。"""
    grouped: dict[int, list[Issue]] = defaultdict(list)
    for issue in issues:
        grouped[issue.location.flow_index].append(issue)
    return grouped


def _add_summary_comment(doc, doc_blocks: list[TraversedBlock], total: int, shown: int) -> None:
    """在文档首个段落插入汇总批注，提示标注截断信息。"""
    for block in doc_blocks:
        if block.kind != "paragraph":
            continue
        portions = text_portions(block.element)
        if not portions:
            continue
        msg = f"共 {total} 处问题，已标注前 {shown} 处，其余详见 issues.json"
        _add_comment(doc, portions[0], "审核汇总", msg)
        return


def annotate(
    session,
    input_docx: str,
    output_docx: str,
    issues: list[Issue],
    max_annotations: int = _DEFAULT_MAX_ANNOTATIONS,
) -> None:
    """对一篇 docx 写入红色底纹和批注，另存为 marked.docx。

    Args:
        session: UnoSession 实例
        input_docx: 源文件路径（只读，不修改）
        output_docx: 输出路径（marked.docx）
        issues: 需要标注的问题列表
        max_annotations: marked.docx 最多标注的 issue 数（按严重度排序截断），
            超出部分只进 issues.json。默认 500。
    """
    # 按严重度排序后截断：error 优先，其次 warning，最后 info
    sorted_issues = sorted(
        issues,
        key=lambda i: _SEVERITY_ORDER.get(i.severity, 9),
    )
    to_annotate = sorted_issues[:max_annotations]
    skipped_count = len(sorted_issues) - len(to_annotate)

    with session.open(input_docx) as doc:
        doc_blocks = iter_blocks(doc)
        grouped = _group_issues_by_block(to_annotate)

        for flow_index in sorted(grouped):
            block_issues = grouped[flow_index]
            block = _validate_issue_block(block_issues[0], doc_blocks)
            if block is None:
                continue
            if block.kind != "paragraph":
                log.warning("未能标注(暂不支持的块类型)：%s @ kind=%s",
                            block_issues[0].rule_id, block.kind)
                continue
            try:
                _annotate_paragraph_block(doc, block, block_issues)
            except Exception:  # noqa: BLE001 — 单段失败不影响其余
                log.exception("未能标注(写入失败)：%s @ flow_index=%s",
                              block_issues[0].rule_id, flow_index)

        if skipped_count > 0:
            _add_summary_comment(doc, doc_blocks, total=len(issues), shown=len(to_annotate))

        url = path_to_url(output_docx)
        doc.storeToURL(url, (
            PropertyValue(Name="FilterName", Value="MS Word 2007 XML"),))
    restore_font_assets(input_docx, output_docx)
    restore_math_content(input_docx, output_docx)
