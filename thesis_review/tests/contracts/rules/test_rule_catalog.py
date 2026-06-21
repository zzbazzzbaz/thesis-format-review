from pathlib import Path

import pytest
import yaml

from thesis_review.rules.catalog import RuleCatalogError, load_rule_catalog
from thesis_review.rules.catalog import load_rule_cases
from thesis_review.rules.registry import get_checkers


def rules_root() -> Path:
    return Path(__file__).resolve().parents[3] / "docs" / "rules"


EXPECTED_MODULES = {
    "global": "整体",
    "cover": "封面",
    "abstract": "摘要",
    "table-of-contents": "目录",
    "main-text": "正文",
    "references": "参考文献",
    "acknowledgements": "致谢",
    "appendix": "附录",
}


def test_rule_asset_files_exist_for_all_modules():
    for module in EXPECTED_MODULES:
        base = rules_root() / module

        assert (base / "README.md").exists()
        assert (base / "rule.yml").exists()
        assert (base / "case.yml").exists()
        assert (base / "samples").is_dir()


def test_rule_modules_match_expected_names():
    catalog = load_rule_catalog(rules_root())

    assert set(catalog.modules_by_name) == set(EXPECTED_MODULES)
    for module, module_name in EXPECTED_MODULES.items():
        spec = catalog.modules_by_name[module]
        assert spec.module == module
        assert spec.module_name == module_name


def test_deprecated_global_rules_remain_deprecated_and_stage_two_rules_are_active():
    catalog = load_rule_catalog(rules_root())
    global_rules = catalog.modules_by_name["global"].rules
    by_id = {rule.id: rule for rule in global_rules}

    for rule_id in {
        "global-margin-001",
        "global-margin-002",
        "global-margin-003",
        "global-margin-004",
        "global-footer-page-number-002",
        "global-footer-page-number-excluded-001",
        "global-footer-page-number-excluded-002",
        "global-footer-page-number-excluded-003",
        "global-footer-page-number-excluded-004",
    }:
        assert by_id[rule_id].status == "deprecated"

    for rule_id in {
        "global-header-001",
        "global-header-002",
        "global-header-003",
        "global-header-004",
        "global-footer-page-number-001",
        "global-footer-page-number-003",
        "global-footer-page-number-004",
        "global-footer-page-number-005",
    }:
        assert by_id[rule_id].status == "active"

    assert {rule.severity for rule in global_rules} == {"error"}


def test_stage_two_main_text_object_rules_are_active():
    catalog = load_rule_catalog(rules_root())

    main_text = catalog.modules_by_name["main-text"]
    active_prefixes = (
        "main-text-formula-",
        "main-text-figure-caption-",
        "main-text-table-caption-",
    )
    for rule in main_text.rules:
        if rule.id.startswith(active_prefixes):
            assert rule.status == "active"


def test_active_rules_are_declared_by_registered_checkers():
    catalog = load_rule_catalog(rules_root())
    checker_rule_ids = {
        rule_id for checker in get_checkers() for rule_id in checker.rule_ids
    }

    active_rule_ids = {
        rule.id
        for spec in catalog.modules_by_name.values()
        for rule in spec.rules
        if rule.status == "active"
    }

    assert active_rule_ids <= checker_rule_ids


def test_table_of_contents_rule_yml_has_expected_ids():
    path = rules_root() / "table-of-contents" / "rule.yml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    rule_ids = {rule["id"] for rule in data["rules"]}

    assert data["module"] == "table-of-contents"
    assert data["module_name"] == "目录"
    assert {
        "table-of-contents-title-001",
        "table-of-contents-title-002",
        "table-of-contents-title-003",
        "table-of-contents-title-004",
        "table-of-contents-title-005",
        "table-of-contents-title-006",
        "table-of-contents-entry-001",
        "table-of-contents-entry-002",
        "table-of-contents-entry-003",
        "table-of-contents-entry-004",
        "table-of-contents-entry-005",
        "table-of-contents-entry-006",
        "table-of-contents-entry-007",
        "table-of-contents-entry-008",
    } <= rule_ids


def test_table_of_contents_cases_have_required_descriptions():
    base = rules_root() / "table-of-contents"
    cases = yaml.safe_load((base / "case.yml").read_text(encoding="utf-8"))["cases"]

    assert cases
    for case in cases:
        assert case["description"]
        assert case["error_description"]
        assert case["file"].startswith("samples/")


def test_new_modules_have_compact_manual_cases():
    for module in EXPECTED_MODULES:
        if module == "table-of-contents":
            continue
        base = rules_root() / module
        cases = yaml.safe_load((base / "case.yml").read_text(encoding="utf-8"))["cases"]

        max_cases = 5 if module == "abstract" else 4
        assert 1 <= len(cases) <= max_cases
        for case in cases:
            assert case["description"]
            assert case["error_description"]
            assert case["file"].startswith("samples/")
            assert case["expected_rule_ids"]


def test_load_rule_catalog_returns_rule_metadata():
    catalog = load_rule_catalog(rules_root())
    rule = catalog.get("table-of-contents-title-006")

    assert rule.id == "table-of-contents-title-006"
    assert rule.title == "目录标题后空行"
    assert rule.severity == "error"
    assert rule.status == "active"
    assert rule.message == "目录标题后必须且只能空一行"
    assert rule.expected == "1 个空段落"


def test_rule_catalog_unknown_rule_id_raises_key_error():
    catalog = load_rule_catalog(rules_root())

    with pytest.raises(KeyError, match="unknown-rule-id"):
        catalog.get("unknown-rule-id")


def test_load_rule_catalog_rejects_duplicate_rule_ids(tmp_path):
    module_dir = tmp_path / "first"
    module_dir.mkdir()
    (module_dir / "rule.yml").write_text(
        """
module: first
module_name: 第一
rules:
  - id: first-title-001
    title: 重复规则
    severity: error
    status: active
    description: 重复规则说明
    message: 重复规则消息
    expected: 重复规则期望
  - id: first-title-001
    title: 重复规则二
    severity: error
    status: active
    description: 重复规则说明二
    message: 重复规则消息二
    expected: 重复规则期望二
""",
        encoding="utf-8",
    )

    with pytest.raises(RuleCatalogError, match="Duplicate rule id"):
        load_rule_catalog(tmp_path)


def test_load_rule_catalog_rejects_module_directory_mismatch(tmp_path):
    module_dir = tmp_path / "table-of-contents"
    module_dir.mkdir()
    (module_dir / "rule.yml").write_text(
        """
module: wrong-module
module_name: 错误模块
rules:
  - id: wrong-module-title-001
    title: 错误规则
    severity: error
    status: active
    description: 错误规则说明
    message: 错误规则消息
    expected: 错误规则期望
""",
        encoding="utf-8",
    )

    with pytest.raises(RuleCatalogError, match="module must match directory name"):
        load_rule_catalog(tmp_path)


def test_load_rule_catalog_rejects_invalid_rule_id(tmp_path):
    module_dir = tmp_path / "table-of-contents"
    module_dir.mkdir()
    (module_dir / "rule.yml").write_text(
        """
module: table-of-contents
module_name: 目录
rules:
  - id: TOC001
    title: 错误编号
    severity: error
    status: active
    description: 错误编号说明
    message: 错误编号消息
    expected: 错误编号期望
""",
        encoding="utf-8",
    )

    with pytest.raises(RuleCatalogError, match="Invalid rule.yml"):
        load_rule_catalog(tmp_path)


def test_load_rule_cases_returns_cases_and_validates_rule_ids():
    catalog = load_rule_catalog(rules_root())
    cases = load_rule_cases(rules_root(), catalog)

    case_by_id = {case.id: case for case in cases}
    clean = case_by_id["table-of-contents-clean"]
    assert clean.expected_rule_ids == []

    title_case = case_by_id["table-of-contents-title-text-and-blank"]
    assert "table-of-contents-title-001" in title_case.expected_rule_ids
    assert "空" in title_case.error_description


def test_load_rule_cases_rejects_unknown_expected_rule_id(tmp_path):
    module_dir = tmp_path / "table-of-contents"
    samples_dir = module_dir / "samples"
    samples_dir.mkdir(parents=True)
    (module_dir / "rule.yml").write_text(
        """
module: table-of-contents
module_name: 目录
rules:
  - id: table-of-contents-title-001
    title: 目录标题文本
    severity: error
    status: active
    description: 规则说明
    message: 规则消息
    expected: 规则期望
""",
        encoding="utf-8",
    )
    (module_dir / "case.yml").write_text(
        """
cases:
  - id: bad-case
    file: samples/sample.docx
    description: 错误样本
    error_description: 错误说明
    expected_rule_ids:
      - unknown-rule-001
""",
        encoding="utf-8",
    )
    catalog = load_rule_catalog(tmp_path)

    with pytest.raises(RuleCatalogError, match="Unknown expected rule id"):
        load_rule_cases(tmp_path, catalog)


def test_load_rule_cases_can_require_sample_files(tmp_path):
    module_dir = tmp_path / "table-of-contents"
    module_dir.mkdir(parents=True)
    (module_dir / "rule.yml").write_text(
        """
module: table-of-contents
module_name: 目录
rules:
  - id: table-of-contents-title-001
    title: 目录标题文本
    severity: error
    status: active
    description: 规则说明
    message: 规则消息
    expected: 规则期望
""",
        encoding="utf-8",
    )
    (module_dir / "case.yml").write_text(
        """
cases:
  - id: missing-sample
    file: samples/missing.docx
    description: 错误样本
    error_description: 错误说明
    expected_rule_ids:
      - table-of-contents-title-001
""",
        encoding="utf-8",
    )
    catalog = load_rule_catalog(tmp_path)

    assert len(load_rule_cases(tmp_path, catalog)) == 1
    with pytest.raises(RuleCatalogError, match="Case sample does not exist"):
        load_rule_cases(tmp_path, catalog, require_samples=True)
