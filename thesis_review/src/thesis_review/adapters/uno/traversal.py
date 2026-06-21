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
    """按模型定位契约枚举正文段落，包含空段落。"""
    out = []
    enum = doc.Text.createEnumeration()
    while enum.hasMoreElements():
        elem = enum.nextElement()
        if not elem.supportsService("com.sun.star.text.Paragraph"):
            continue
        out.append(elem)
    return out


def _supports(obj, service: str) -> bool:
    try:
        return bool(obj.supportsService(service))
    except AttributeError:
        return False


def _portion_types(para) -> list[str]:
    out: list[str] = []
    try:
        enum = para.createEnumeration()
    except AttributeError:
        return out
    while enum.hasMoreElements():
        portion = enum.nextElement()
        out.append(getattr(portion, "TextPortionType", ""))
    return out


def _image_shapes(doc) -> list:
    try:
        draw_page = doc.DrawPage
        count = draw_page.getCount()
    except AttributeError:
        return []
    out = []
    for index in range(count):
        shape = draw_page.getByIndex(index)
        if _supports(shape, "com.sun.star.text.TextGraphicObject") or _supports(
            shape,
            "com.sun.star.drawing.GraphicObjectShape",
        ):
            out.append(shape)
    return out


def blocks(doc) -> list[TraversedBlock]:
    """按模型定位契约枚举文档流中的块级元素。"""
    out: list[TraversedBlock] = []
    type_counts: dict[TraversedBlockKind, int] = {
        "paragraph": 0,
        "table": 0,
        "image": 0,
    }
    images = _image_shapes(doc)
    image_index = 0
    enum = doc.Text.createEnumeration()
    while enum.hasMoreElements():
        elem = enum.nextElement()
        kind: TraversedBlockKind | None = None
        if elem.supportsService("com.sun.star.text.Paragraph"):
            portion_types = _portion_types(elem)
            frame_count = sum(1 for item in portion_types if item == "Frame")
            if elem.getString().strip() or frame_count == 0:
                kind = "paragraph"
            for _ in range(frame_count):
                image = images[image_index] if image_index < len(images) else elem
                out.append(
                    TraversedBlock(
                        kind="image",
                        element=image,
                        flow_index=len(out),
                        type_index=type_counts["image"],
                    )
                )
                type_counts["image"] += 1
                image_index += 1
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
