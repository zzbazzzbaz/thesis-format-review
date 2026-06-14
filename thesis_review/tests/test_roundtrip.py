"""定位契约 roundtrip 测试：extractor 索引 → annotator 反查同一节点。"""
from __future__ import annotations

import pytest

from src.extractor import extract
from src.annotator import _paragraphs, _portions, annotate
from src.models import Issue, Location
from src.uno_session import UnoSession


@pytest.mark.uno
def test_paragraph_index_roundtrip(sample_docx):
    """extractor 的 paragraph_index 能在 annotator 中定位同一段落文本。"""
    with UnoSession() as session:
        with session.open(sample_docx) as doc:
            model = extract(doc, source_path=sample_docx)
        # 取一个有 run 的段落
        target_para = next(p for p in model.paragraphs if p.runs)
        expected_text = target_para.text

        with session.open(sample_docx) as doc2:
            paras = _paragraphs(doc2)
            located = paras[target_para.paragraph_index]
            assert located.getString() == expected_text


@pytest.mark.uno
def test_run_index_roundtrip(sample_docx):
    """extractor 的 run_index 能在 annotator 的 _portions 中定位同一文本。"""
    with UnoSession() as session:
        with session.open(sample_docx) as doc:
            model = extract(doc, source_path=sample_docx)
        target_para = next(p for p in model.paragraphs if p.runs)
        target_run = target_para.runs[0]

        with session.open(sample_docx) as doc2:
            paras = _paragraphs(doc2)
            para = paras[target_para.paragraph_index]
            portions = _portions(para)
            located = portions[target_run.run_index]
            assert located.getString() == target_run.text


@pytest.mark.uno
def test_full_annotate_roundtrip(tmp_path, sample_docx):
    """端到端：extract → 构造 Issue → annotate → 重开验证底纹。"""
    out = str(tmp_path / "marked.docx")
    with UnoSession() as session:
        with session.open(sample_docx) as doc:
            model = extract(doc, source_path=sample_docx)

        # 对第一个正文段落的第一个 run 构造 issue
        body_paras = [p for p in model.paragraphs if p.outline_level is None and p.runs]
        target = body_paras[0]
        run = target.runs[0]
        issue = Issue(
            rule_id="roundtrip.test",
            category="format",
            severity="error",
            message="roundtrip 测试批注",
            location=Location(
                kind="run",
                block_id=target.id,
                paragraph_index=target.paragraph_index,
                run_id=run.id,
                run_index=run.run_index,
            ),
        )

        annotate(session, sample_docx, out, [issue])

        # 重开 marked.docx，验证该 portion 有底纹、有批注
        with session.open(out) as doc2:
            paras = _paragraphs(doc2)
            portions = _portions(paras[target.paragraph_index])
            located = portions[run.run_index]
            assert located.CharBackColor == 0xFF0000
            assert located.getString() == run.text

            # 验证批注
            fields = doc2.getTextFields().createEnumeration()
            texts = []
            while fields.hasMoreElements():
                f = fields.nextElement()
                if f.supportsService("com.sun.star.text.textfield.Annotation"):
                    texts.append(f.Content)
            assert any("roundtrip" in t for t in texts)
