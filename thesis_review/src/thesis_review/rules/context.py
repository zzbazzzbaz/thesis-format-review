"""规则运行时共享上下文。"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from thesis_review.models import DocumentModel
from thesis_review.rules.catalog import RuleCatalog, load_rule_catalog
from thesis_review.rules.issue_factory import IssueFactory
from thesis_review.sections import SectionRange, detect_sections


def _default_rules_root() -> Path:
    for parent in Path(__file__).resolve().parents:
        candidate = parent / "docs" / "rules"
        if candidate.exists():
            return candidate
    raise FileNotFoundError("Cannot find thesis_review/docs/rules from package location")


@dataclass(frozen=True)
class RuleContext:
    document: DocumentModel
    sections: dict[str, SectionRange]
    catalog: RuleCatalog
    issue_factory: IssueFactory


def build_rule_context(
    document: DocumentModel,
    rules_root: str | Path | None = None,
) -> RuleContext:
    root = Path(rules_root) if rules_root is not None else _default_rules_root()
    catalog = load_rule_catalog(root)
    return RuleContext(
        document=document,
        sections=detect_sections(document),
        catalog=catalog,
        issue_factory=IssueFactory(catalog),
    )
