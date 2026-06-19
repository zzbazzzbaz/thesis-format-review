"""规则 case.yml 测试辅助。"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

from thesis_review.rules.catalog import RuleCaseFile, RuleCaseSpec, RuleCatalog


@dataclass(frozen=True)
class ResolvedRuleCase:
    module: str
    case: RuleCaseSpec
    module_dir: Path
    sample_path: Path
    module_rule_ids: set[str]


def resolve_rule_cases(rules_root: Path, catalog: RuleCatalog) -> list[ResolvedRuleCase]:
    resolved: list[ResolvedRuleCase] = []
    for module_dir in sorted(path for path in rules_root.iterdir() if path.is_dir()):
        case_path = module_dir / "case.yml"
        if not case_path.exists():
            continue
        case_file = RuleCaseFile.model_validate(
            yaml.safe_load(case_path.read_text(encoding="utf-8"))
        )
        module_spec = catalog.modules_by_name[module_dir.name]
        module_rule_ids = {rule.id for rule in module_spec.rules}
        for case in case_file.cases:
            for rule_id in case.expected_rule_ids:
                if rule_id not in catalog.rules_by_id:
                    raise AssertionError(f"Unknown rule id in {case_path}: {rule_id}")
            resolved.append(
                ResolvedRuleCase(
                    module=module_dir.name,
                    case=case,
                    module_dir=module_dir,
                    sample_path=module_dir / case.file,
                    module_rule_ids=module_rule_ids,
                )
            )
    return resolved


def filter_module_rule_ids(rule_ids: set[str], module_rule_ids: set[str]) -> set[str]:
    return rule_ids & module_rule_ids
