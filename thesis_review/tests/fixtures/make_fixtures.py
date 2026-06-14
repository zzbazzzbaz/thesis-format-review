"""用 python-docx 程序化生成测试 .docx fixture。

用途：在不依赖 WPS/Microsoft Word 本机安装的前提下，生成已知格式缺陷的基线 docx，
用于驱动 extractor/annotator 的 UNO 测试。由 UNO 读取 python-docx 生成的 docx，
同时也验证了跨工具兼容性。

运行：uv run python tests/fixtures/make_fixtures.py
"""
from __future__ import annotations

from pathlib import Path

from docx import Document
from docx.enum.text import WD_LINE_SPACING
from docx.oxml.ns import qn
from docx.shared import Pt

HERE = Path(__file__).parent.resolve()


def _set_run_font_east_asian(run, font_name: str) -> None:
    """通过 XML 设 run 的中文字体。

    python-docx 高层 API(run.font.name)只设西文字体；设置
    w:eastAsia 属性来指定中文字体，使 WPS/Word/LibreOffice 均能从解析链读到。
    """
    rpr = run._element.get_or_add_rPr()
    rfonts = rpr.find(qn("w:rFonts"))
    if rfonts is None:
        rfonts = rpr.makeelement(qn("w:rFonts"), {})
        rpr.insert(0, rfonts)
    rfonts.set(qn("w:eastAsia"), font_name)


def build_sample() -> None:
    doc = Document()

    # ── 一级标题（合规，作为标题） ──
    doc.add_heading("第一章 绪论", level=1)

    # ── 正文段落：故意用错字体(楷体)、错字号(14pt)，触发 font/size 规则 ──
    p1 = doc.add_paragraph()
    run1 = p1.add_run("这是正文第一段，字体和字号都设置错误。")
    run1.font.size = Pt(14)
    _set_run_font_east_asian(run1, "楷体")
    p1.paragraph_format.line_spacing_rule = WD_LINE_SPACING.ONE_POINT_FIVE

    # ── 正文段落：合规（宋体 + 小四） ──
    p2 = doc.add_paragraph()
    run2 = p2.add_run("这是正文第二段，字体字号均合规。")
    run2.font.size = Pt(12)
    _set_run_font_east_asian(run2, "宋体")
    p2.paragraph_format.line_spacing_rule = WD_LINE_SPACING.ONE_POINT_FIVE

    # ── 正文段落：行距不对（单倍行距） ──
    p3 = doc.add_paragraph()
    run3 = p3.add_run("这是正文第三段，行距为单倍行距而非1.5倍。")
    run3.font.size = Pt(12)
    _set_run_font_east_asian(run3, "宋体")
    p3.paragraph_format.line_spacing_rule = WD_LINE_SPACING.SINGLE

    # ── 正文段落：首行缩进不对 ──
    p4 = doc.add_paragraph()
    run4 = p4.add_run("这是正文第四段，没有设置首行缩进。")
    run4.font.size = Pt(12)
    _set_run_font_east_asian(run4, "宋体")
    p4.paragraph_format.line_spacing_rule = WD_LINE_SPACING.ONE_POINT_FIVE

    # ── 摘要 / 关键词标题（参考文献故意缺失，触发 required 规则） ──
    doc.add_heading("摘要", level=1)
    doc.add_paragraph("这里是摘要内容。").paragraph_format.line_spacing_rule = (
        WD_LINE_SPACING.ONE_POINT_FIVE
    )

    doc.add_heading("关键词", level=1)
    doc.add_paragraph("关键词1；关键词2。").paragraph_format.line_spacing_rule = (
        WD_LINE_SPACING.ONE_POINT_FIVE
    )

    out = HERE / "sample.docx"
    doc.save(str(out))
    print(f"generated {out}")


if __name__ == "__main__":
    build_sample()
