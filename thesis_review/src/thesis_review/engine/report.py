"""审核结果 JSON 报告。"""
from __future__ import annotations

import json
from typing import Any

from thesis_review.engine.result import ReviewResult

_REQUIRED_MODULE_SECTIONS = {
    "cover": ("cover",),
    "abstract": ("abstract-chinese", "abstract-english"),
    "table-of-contents": ("table-of-contents",),
    "main-text": ("main-text",),
    "references": ("references",),
}

_OPTIONAL_MODULE_SECTIONS = {
    "acknowledgements": ("acknowledgements",),
    "appendix": ("appendix",),
}


def _section_range_payload(section: Any) -> dict[str, Any]:
    block_ids = getattr(section, "block_ids", set())
    return {
        "start": getattr(section, "start", None),
        "end": getattr(section, "end", None),
        "block_count": len(block_ids),
    }


def _module_detection_payload(
    sections: dict[str, Any],
    *,
    required: bool,
    section_names: tuple[str, ...],
) -> dict[str, Any]:
    detected_sections = [
        name for name in section_names
        if name in sections
    ]
    missing_sections = [
        name for name in section_names
        if name not in sections
    ]
    return {
        "required": required,
        "detected": not missing_sections,
        "partial": bool(detected_sections) and bool(missing_sections),
        "section_names": list(section_names),
        "detected_sections": detected_sections,
        "missing_sections": missing_sections,
    }


def sections_payload(sections: dict[str, Any]) -> dict[str, Any]:
    modules = {
        module: _module_detection_payload(
            sections,
            required=True,
            section_names=section_names,
        )
        for module, section_names in _REQUIRED_MODULE_SECTIONS.items()
    }
    modules.update({
        module: _module_detection_payload(
            sections,
            required=False,
            section_names=section_names,
        )
        for module, section_names in _OPTIONAL_MODULE_SECTIONS.items()
    })
    return {
        "detected": {
            name: _section_range_payload(section)
            for name, section in sorted(sections.items())
        },
        "modules": modules,
        "missing_required": [
            module
            for module, info in modules.items()
            if info["required"] and not info["detected"]
        ],
        "missing_optional": [
            module
            for module, info in modules.items()
            if not info["required"] and not info["detected"]
        ],
    }


def result_payload(result: ReviewResult) -> dict[str, Any]:
    return {
        "input": str(result.input_docx),
        "marked_docx": str(result.marked_docx),
        "summary": result.summary,
        "sections": sections_payload(result.sections),
        "issues": [issue.model_dump(mode="json") for issue in result.issues],
    }


def write_issues_json(result: ReviewResult) -> None:
    result.issues_json.parent.mkdir(parents=True, exist_ok=True)
    result.issues_json.write_text(
        json.dumps(result_payload(result), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
