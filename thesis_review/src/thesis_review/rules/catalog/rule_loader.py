"""加载运行时 rule.yml 规则元数据。"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

from thesis_review.rules.catalog.models import RuleCatalog, RuleModuleSpec, RuleSpec


class RuleCatalogError(ValueError):
    """规则目录配置错误。"""


def _read_yaml(path: Path) -> dict[str, Any]:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise RuleCatalogError(f"Invalid YAML: {path}") from exc
    if not isinstance(data, dict):
        raise RuleCatalogError(f"YAML root must be a mapping: {path}")
    return data


def _load_module(path: Path) -> RuleModuleSpec:
    try:
        module = RuleModuleSpec.model_validate(_read_yaml(path))
    except ValidationError as exc:
        raise RuleCatalogError(f"Invalid rule.yml: {path}") from exc
    expected_module = path.parent.name
    if module.module != expected_module:
        raise RuleCatalogError(
            f"{path}: module must match directory name "
            f"({module.module!r} != {expected_module!r})"
        )
    return module


def load_rule_catalog(root: str | Path) -> RuleCatalog:
    root_path = Path(root)
    rule_files = sorted(root_path.glob("*/rule.yml"))
    if not rule_files:
        raise RuleCatalogError(f"No rule.yml files found under {root_path}")

    rules_by_id: dict[str, RuleSpec] = {}
    modules_by_name: dict[str, RuleModuleSpec] = {}
    for path in rule_files:
        module = _load_module(path)
        modules_by_name[module.module] = module
        for rule in module.rules:
            if rule.id in rules_by_id:
                raise RuleCatalogError(f"Duplicate rule id: {rule.id}")
            rules_by_id[rule.id] = rule

    return RuleCatalog(
        rules_by_id=rules_by_id,
        modules_by_name=modules_by_name,
    )
