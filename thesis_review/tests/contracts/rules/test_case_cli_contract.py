"""case.yml 通过 CLI 驱动的规则契约测试。"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from tests.support.rule_cases import filter_module_rule_ids, resolve_rule_cases
from thesis_review.rules.catalog import load_rule_catalog


def rules_root() -> Path:
    return Path(__file__).resolve().parents[3] / "docs" / "rules"


def resolved_cases():
    catalog = load_rule_catalog(rules_root())
    return resolve_rule_cases(rules_root(), catalog)


@pytest.mark.uno
@pytest.mark.parametrize("resolved", resolved_cases(), ids=lambda item: item.case.id)
def test_rule_case_expected_ids_match_cli_output(resolved, tmp_path):
    if not resolved.sample_path.exists():
        pytest.skip(f"规则样本未准备：{resolved.sample_path}")

    out_dir = tmp_path / resolved.case.id
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "thesis_review.interfaces.cli",
            "review",
            str(resolved.sample_path),
            "--out-dir",
            str(out_dir),
        ],
        check=False,
        text=True,
        capture_output=True,
    )
    assert completed.returncode == 0, completed.stderr

    data = json.loads((out_dir / "issues.json").read_text(encoding="utf-8"))
    actual_rule_ids = {issue["rule_id"] for issue in data["issues"]}
    actual_module_rule_ids = filter_module_rule_ids(
        actual_rule_ids,
        resolved.active_rule_ids,
    )

    assert actual_module_rule_ids == set(resolved.case.expected_rule_ids)
