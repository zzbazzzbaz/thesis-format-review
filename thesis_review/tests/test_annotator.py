"""annotator 测试：UNO 写红色底纹 + 批注 → marked.docx。"""
from __future__ import annotations

import os

import pytest

from src.annotator import annotate, _paragraphs, _portions
from src.uno_session import UnoSession
from src.models import Issue, Location


@pytest.mark.uno
def test_annotate_produces_marked_docx(tmp_path, sample_docx):
    """标注后产出 marked.docx 文件。"""
    out = str(tmp_path / "marked.docx")
    issues = [
        Issue(
            rule_id="format.body.font",
            category="format",
            severity="error",
            message="正文中文字体应为宋体",
            expected="宋体",
            actual="楷体",
            location=Location(
                kind="paragraph", block_id="p-0001", paragraph_index=1
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
    issues = [
        Issue(
            rule_id="format.body.font",
            category="format",
            severity="error",
            message="正文中文字体应为宋体",
            expected="宋体",
            actual="楷体",
            location=Location(
                kind="paragraph", block_id="p-0001", paragraph_index=1
            ),
        )
    ]
    with UnoSession() as session:
        annotate(session, sample_docx, out, issues)
        with session.open(out) as doc:
            fields = doc.getTextFields().createEnumeration()
            texts = []
            while fields.hasMoreElements():
                f = fields.nextElement()
                if f.supportsService("com.sun.star.text.textfield.Annotation"):
                    texts.append(f.Content)
    assert any("宋体" in t for t in texts)


@pytest.mark.uno
def test_annotate_writes_red_backcolor(tmp_path, sample_docx):
    """标注后重新打开，目标段落的 portion CharBackColor 应为红色。

    OOXML 不保留段落级 CharBackColor，因此段落级 issue 也会对
    所有 portion 设底纹，重开后查 portion。
    """
    out = str(tmp_path / "marked.docx")
    issues = [
        Issue(
            rule_id="format.body.font",
            category="format",
            severity="error",
            message="正文中文字体应为宋体",
            location=Location(
                kind="paragraph", block_id="p-0001", paragraph_index=1
            ),
        )
    ]
    with UnoSession() as session:
        annotate(session, sample_docx, out, issues)
        with session.open(out) as doc:
            paras = _paragraphs(doc)
            target = paras[1]  # paragraph_index=1
            portions = _portions(target)
            assert len(portions) >= 1
            assert portions[0].CharBackColor == 0xFF0000


@pytest.mark.uno
def test_annotate_skips_out_of_range_location(tmp_path, sample_docx):
    """越界定位不应抛异常。"""
    out = str(tmp_path / "marked.docx")
    issues = [
        Issue(
            rule_id="x",
            category="format",
            severity="error",
            message="越界",
            location=Location(
                kind="paragraph", block_id="p-9999", paragraph_index=9999
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
    issues = [
        Issue(
            rule_id="format.body.font",
            category="format",
            severity="error",
            message="正文字体不对",
            location=Location(
                kind="run",
                block_id="p-0001",
                paragraph_index=1,
                run_id="p-0001-r-0000",
                run_index=0,
            ),
        )
    ]
    with UnoSession() as session:
        annotate(session, sample_docx, out, issues)
        with session.open(out) as doc:
            paras = _paragraphs(doc)
            portions = _portions(paras[1])
            assert portions[0].CharBackColor == 0xFF0000
