"""annotator 测试：UNO 写红色底纹 + 批注 → marked.docx。"""
from __future__ import annotations

import os

import pytest

pytest.importorskip("uno")

from thesis_review.adapters.uno.annotator import annotate
from thesis_review.adapters.uno.extractor import extract
from thesis_review.core.models import Issue, Location
from thesis_review.adapters.uno.session import UnoSession
from thesis_review.adapters.uno.traversal import blocks as iter_blocks
from thesis_review.adapters.uno.traversal import text_portions


def _first_text_paragraph(session: UnoSession, sample_docx: str):
    with session.open(sample_docx) as doc:
        model = extract(doc, source_path=sample_docx)
    return next(
        block for block in model.blocks
        if block.kind == "paragraph" and block.runs and block.text.strip()
    )


@pytest.mark.uno
def test_annotate_produces_marked_docx(tmp_path, sample_docx):
    """标注后产出 marked.docx 文件。"""
    out = str(tmp_path / "marked.docx")
    issues = [
        Issue(
            rule_id="table-of-contents-title-001",
            category="structure",
            severity="error",
            message="目录标题格式错误",
            expected="目    录",
            actual="目录",
            location=Location(
                target="block",
                block_id="b-0001",
                block_kind="paragraph",
                flow_index=1,
            ),
        )
    ]
    with UnoSession() as session:
        annotate(session, sample_docx, out, issues)
    assert os.path.exists(out)


@pytest.mark.uno
def test_annotate_writes_comment_text(tmp_path, sample_docx):
    """打开 marked.docx，确认批注内容已写入。"""
    out = str(tmp_path / "marked.docx")
    with UnoSession() as session:
        target = _first_text_paragraph(session, sample_docx)
        issues = [
            Issue(
                rule_id="table-of-contents-title-001",
                category="structure",
                severity="error",
                message="目录标题格式错误",
                expected="目    录",
                actual="目录",
                location=Location(
                    target="block",
                    block_id=target.id,
                    block_kind="paragraph",
                    flow_index=target.flow_index,
                ),
            )
        ]
        annotate(session, sample_docx, out, issues)
        with session.open(out) as doc:
            fields = doc.getTextFields().createEnumeration()
            comments = []
            while fields.hasMoreElements():
                f = fields.nextElement()
                if f.supportsService("com.sun.star.text.textfield.Annotation"):
                    comments.append((f.Author, f.Content))
    assert any(
        author == "table-of-contents-title-001"
        and "目录标题格式错误" in text
        for author, text in comments
    )


@pytest.mark.uno
def test_annotate_writes_red_backcolor(tmp_path, sample_docx):
    """标注后重新打开，目标段落的 portion CharBackColor 应为红色。

    OOXML 不保留段落级 CharBackColor，因此段落级 issue 也会对
    所有 portion 设底纹，重开后查 portion。
    """
    out = str(tmp_path / "marked.docx")
    with UnoSession() as session:
        target = _first_text_paragraph(session, sample_docx)
        issues = [
            Issue(
                rule_id="table-of-contents-title-001",
                category="structure",
                severity="error",
                message="目录标题格式错误",
                location=Location(
                    target="block",
                    block_id=target.id,
                    block_kind="paragraph",
                    flow_index=target.flow_index,
                ),
            )
        ]
        annotate(session, sample_docx, out, issues)
        with session.open(out) as doc:
            located = iter_blocks(doc)[target.flow_index].element
            portions = text_portions(located)
            assert len(portions) >= 1
            assert portions[0].CharBackColor == 0xFF0000


@pytest.mark.uno
def test_annotate_skips_out_of_range_location(tmp_path, sample_docx):
    """越界定位不应抛异常。"""
    out = str(tmp_path / "marked.docx")
    issues = [
        Issue(
            rule_id="table-of-contents-title-001",
            category="structure",
            severity="error",
            message="越界",
            location=Location(
                target="block",
                block_id="b-9999",
                block_kind="paragraph",
                flow_index=9999,
            ),
        )
    ]
    with UnoSession() as session:
        annotate(session, sample_docx, out, issues)
    assert os.path.exists(out)


@pytest.mark.uno
def test_annotate_run_level_backcolor(tmp_path, sample_docx):
    """run 级 issue 仅给该 portion 加底纹。"""
    out = str(tmp_path / "marked.docx")
    with UnoSession() as session:
        target = _first_text_paragraph(session, sample_docx)
        run = target.runs[0]
        issues = [
            Issue(
                rule_id="table-of-contents-entry-004",
                category="structure",
                severity="error",
                message="目录条目字体错误",
                location=Location(
                    target="run",
                    block_id=target.id,
                    block_kind="paragraph",
                    flow_index=target.flow_index,
                    run_id=run.id,
                    run_index=run.run_index,
                ),
            )
        ]
        annotate(session, sample_docx, out, issues)
        with session.open(out) as doc:
            located = iter_blocks(doc)[target.flow_index].element
            portions = text_portions(located)
            assert portions[run.run_index].CharBackColor == 0xFF0000


@pytest.mark.uno
def test_annotate_one_comment_per_issue(tmp_path, sample_docx):
    """同一段落多个 issue 各自独立一条批注，author=rule_id、内容=该 issue message。"""
    out = str(tmp_path / "marked.docx")
    with UnoSession() as session:
        target = _first_text_paragraph(session, sample_docx)
        issues = [
            Issue(
                rule_id="rule-a-001",
                category="format",
                severity="error",
                message="问题一",
                location=Location(
                    target="block",
                    block_id=target.id,
                    block_kind="paragraph",
                    flow_index=target.flow_index,
                ),
            ),
            Issue(
                rule_id="rule-b-002",
                category="format",
                severity="warning",
                message="问题二",
                location=Location(
                    target="block",
                    block_id=target.id,
                    block_kind="paragraph",
                    flow_index=target.flow_index,
                ),
            ),
        ]
        annotate(session, sample_docx, out, issues)
        with session.open(out) as doc:
            fields = doc.getTextFields().createEnumeration()
            comments = []
            while fields.hasMoreElements():
                f = fields.nextElement()
                if f.supportsService("com.sun.star.text.textfield.Annotation"):
                    comments.append((f.Author, f.Content))

    # 每个 issue 独立一条批注
    assert len(comments) == 2
    by_author = {author: content for author, content in comments}
    assert by_author["rule-a-001"] == "问题一"
    assert by_author["rule-b-002"] == "问题二"


@pytest.mark.uno
def test_annotate_caps_at_limit(tmp_path, sample_docx):
    """超过上限的 issue 不进 marked.docx，并插汇总批注。"""
    out = str(tmp_path / "marked.docx")
    with UnoSession() as session:
        target = _first_text_paragraph(session, sample_docx)
        # 构造 10 个 issue，上限设为 5
        issues = [
            Issue(
                rule_id=f"rule-cap-{i:03d}",
                category="format",
                severity="error" if i < 3 else "warning",
                message=f"问题{i}",
                location=Location(
                    target="block",
                    block_id=target.id,
                    block_kind="paragraph",
                    flow_index=target.flow_index,
                ),
            )
            for i in range(10)
        ]
        annotate(session, sample_docx, out, issues, max_annotations=5)
        with session.open(out) as doc:
            fields = doc.getTextFields().createEnumeration()
            count = 0
            has_summary = False
            while fields.hasMoreElements():
                f = fields.nextElement()
                if f.supportsService("com.sun.star.text.textfield.Annotation"):
                    count += 1
                    if f.Author == "审核汇总":
                        has_summary = True
                        assert "共 10 处" in f.Content
                        assert "已标注前 5 处" in f.Content

    # 5 个 issue 各一条 + 1 条汇总 = 6
    assert count == 6
    assert has_summary
