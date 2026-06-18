"""加载测试用 case.yml 样本清单。"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

from thesis_review.rules.catalog.models import RuleCaseFile, RuleCaseSpec, RuleCatalog
from thesis_review.rules.catalog.rule_loader import RuleCatalogError


def _read_yaml(path: Path) -> dict[str, Any]:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise RuleCatalogError(f"Invalid YAML: {path}") from exc
    if not isinstance(data, dict):
        raise RuleCatalogError(f"YAML root must be a mapping: {path}")
    return data


def load_rule_cases(
    root: str | Path,
    catalog: RuleCatalog,
    *,
    require_samples: bool = False,
) -> list[RuleCaseSpec]:
    root_path = Path(root)
    case_files = sorted(root_path.glob("*/case.yml"))
    cases: list[RuleCaseSpec] = []
    for path in case_files:
        try:
            case_file = RuleCaseFile.model_validate(_read_yaml(path))
        except ValidationError as exc:
            raise RuleCatalogError(f"Invalid case.yml: {path}") from exc
        for case in case_file.cases:
            sample_path = path.parent / case.file
            if require_samples and not sample_path.exists():
                raise RuleCatalogError(f"Case sample does not exist: {sample_path}")
            for rule_id in case.expected_rule_ids:
                if rule_id not in catalog.rules_by_id:
                    raise RuleCatalogError(
                        f"Unknown expected rule id {rule_id!r} in {path}"
                    )
            cases.append(case)
    return cases
