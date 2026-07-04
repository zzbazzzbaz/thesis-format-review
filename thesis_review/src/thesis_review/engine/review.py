"""审核编排入口。"""
from __future__ import annotations

import logging
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from thesis_review.core.models import DocumentModel, Issue
from thesis_review.engine.report import write_issues_json
from thesis_review.engine.result import ReviewResult

log = logging.getLogger(__name__)


class SessionFactory(Protocol):
    def __call__(self) -> Any:
        ...


@dataclass(frozen=True)
class ReviewDependencies:
    session_factory: SessionFactory
    extract: Callable[[Any, str], DocumentModel]
    annotate: Callable[[Any, str, str, list[Issue]], None]
    build_rule_context: Callable[[DocumentModel], Any]
    get_checkers: Callable[[], list[Any]]


def default_dependencies() -> ReviewDependencies:
    from thesis_review.adapters.uno.annotator import annotate
    from thesis_review.adapters.uno.extractor import extract
    from thesis_review.rules.context import build_rule_context
    from thesis_review.rules.registry import get_checkers
    from thesis_review.adapters.uno.session import UnoSession

    return ReviewDependencies(
        session_factory=UnoSession,
        extract=extract,
        annotate=annotate,
        build_rule_context=build_rule_context,
        get_checkers=get_checkers,
    )


def review(
    input_docx: str | Path,
    out_dir: str | Path,
    *,
    dependencies: ReviewDependencies | None = None,
) -> ReviewResult:
    input_path = Path(input_docx)
    output_dir = Path(out_dir)
    marked_docx = output_dir / "marked.docx"
    issues_json = output_dir / "issues.json"
    output_dir.mkdir(parents=True, exist_ok=True)

    deps = dependencies or default_dependencies()
    log.info("review begin: input=%s", input_path)
    t0 = time.monotonic()
    with deps.session_factory() as session:
        with session.open(str(input_path)) as doc:
            t = time.monotonic()
            document = deps.extract(doc, source_path=str(input_path))
            log.info("review: extract done %.1fs blocks=%s", time.monotonic() - t, len(document.blocks))
        context = deps.build_rule_context(document)
        issues: list[Issue] = []
        for checker in deps.get_checkers():
            issues.extend(checker.check(context))
        log.info("review: rules done issues=%s", len(issues))
        t = time.monotonic()
        deps.annotate(session, str(input_path), str(marked_docx), issues)
        log.info("review: annotate done %.1fs issues=%s", time.monotonic() - t, len(issues))

    result = ReviewResult(
        input_docx=input_path,
        out_dir=output_dir,
        marked_docx=marked_docx,
        issues_json=issues_json,
        issues=issues,
        sections=getattr(context, "sections", {}),
    )
    write_issues_json(result)
    log.info("review end: input=%s total=%.1fs", input_path, time.monotonic() - t0)
    return result
