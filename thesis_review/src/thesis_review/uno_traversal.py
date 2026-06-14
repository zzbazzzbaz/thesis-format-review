"""UNO 文档遍历工具。

extractor 和 annotator 都依赖这里的过滤规则，确保
flow_index/run_index 的读写定位契约保持一致。
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

TraversedBlockKind = Literal["paragraph", "table", "image"]


@dataclass(frozen=True)
class TraversedBlock:
    kind: TraversedBlockKind
    element: object
    flow_index: int
    type_index: int


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


def blocks(doc) -> list[TraversedBlock]:
    """按模型定位契约枚举文档流中的块级元素。"""
    out: list[TraversedBlock] = []
    type_counts: dict[TraversedBlockKind, int] = {
        "paragraph": 0,
        "table": 0,
        "image": 0,
    }
    enum = doc.Text.createEnumeration()
    while enum.hasMoreElements():
        elem = enum.nextElement()
        kind: TraversedBlockKind | None = None
        if elem.supportsService("com.sun.star.text.Paragraph"):
            if not elem.getString():
                continue
            kind = "paragraph"
        elif elem.supportsService("com.sun.star.text.TextTable"):
            kind = "table"
        if kind is None:
            continue
        out.append(
            TraversedBlock(
                kind=kind,
                element=elem,
                flow_index=len(out),
                type_index=type_counts[kind],
            )
        )
        type_counts[kind] += 1
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
