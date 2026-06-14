"""UNO 文档遍历工具。

extractor 和 annotator 都依赖这里的过滤规则，确保
paragraph_index/run_index 的读写定位契约保持一致。
"""
from __future__ import annotations


def paragraphs(doc) -> list:
    """按模型定位契约枚举非空正文段落。"""
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


def text_portions(para) -> list:
    """按模型定位契约枚举非空 Text portion。"""
    out = []
    enum = para.createEnumeration()
    while enum.hasMoreElements():
        portion = enum.nextElement()
        if getattr(portion, "TextPortionType", "Text") != "Text":
            continue
        if not portion.getString():
            continue
        out.append(portion)
    return out
