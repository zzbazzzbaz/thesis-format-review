"""规则元数据模型。"""
from __future__ import annotations

import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

RuleSeverity = Literal["error", "warning", "info"]
RuleStatus = Literal["draft", "active", "deprecated"]
_RULE_ID_RE = re.compile(r"^[a-z]+(?:-[a-z]+)*-\d{3}$")


class RuleSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    title: str
    severity: RuleSeverity
    status: RuleStatus
    description: str
    message: str
    expected: str

    @field_validator("id")
    @classmethod
    def validate_rule_id(cls, value: str) -> str:
        if not _RULE_ID_RE.fullmatch(value):
            raise ValueError(
                "rule id must be lowercase words joined by '-' and end with three digits"
            )
        return value


class RuleModuleSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    module: str
    module_name: str
    rules: list[RuleSpec] = Field(min_length=1)


class RuleCaseSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    file: str
    description: str
    error_description: str
    expected_rule_ids: list[str]


class RuleCaseFile(BaseModel):
    model_config = ConfigDict(extra="forbid")

    cases: list[RuleCaseSpec]


class RuleCatalog(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    rules_by_id: dict[str, RuleSpec]
    modules_by_name: dict[str, RuleModuleSpec]

    def get(self, rule_id: str) -> RuleSpec:
        try:
            return self.rules_by_id[rule_id]
        except KeyError as exc:
            raise KeyError(rule_id) from exc

    def active_rule_ids(self) -> set[str]:
        return {
            rule.id
            for rule in self.rules_by_id.values()
            if rule.status == "active"
        }
