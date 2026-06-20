# 项目级 AGENTS.md

- 默认使用简体中文沟通。
- 除非用户另有说明，开发和测试以 `thesis_review/` Python 子项目为工作目录。
- Python 版本固定为 3.12，依赖管理优先使用 `uv`；安装依赖用 `uv sync --extra dev`。

## 必要结构

- 代码入口：`thesis_review/src/thesis_review/`
- 规则资产：`thesis_review/docs/rules/**`
- 测试目录：`thesis_review/tests/`
- UNO 镜像：`thesis_review/Dockerfile.uno-dev`

当前已实现规则模块是 `abstract` 和 `table-of-contents`；其他规则模块未实现前应保持 `draft`。

## 测试

所有命令默认从 `thesis_review/` 运行。

宿主机纯 Python 测试：

```bash
uv run pytest -m "not uno" -q
```

规则资产契约测试：

```bash
uv run pytest tests/contracts/rules/test_rule_catalog.py -q
```

容器内全量测试：

```bash
docker run --rm -v "$PWD":/workspace -w /workspace \
  thesis-review-uno-dev \
  /opt/venv/bin/python -m pytest -q
```

容器内 UNO 测试：

```bash
docker run --rm -v "$PWD":/workspace -w /workspace \
  thesis-review-uno-dev \
  /opt/venv/bin/python -m pytest -m uno -v
```

规则样本契约测试：

```bash
docker run --rm -v "$PWD":/workspace -w /workspace \
  thesis-review-uno-dev \
  /opt/venv/bin/python -m pytest tests/contracts/rules/test_case_cli_contract.py -m uno -v
```

## UNO 约束

- 涉及 LibreOffice/UNO 的测试必须在 Docker 容器中运行，不依赖 macOS 宿主机 LibreOffice。
- UNO 测试使用 `@pytest.mark.uno`。
- `SOFFICE_BIN` 默认是 `/usr/bin/soffice`，可通过环境变量覆盖。
- 日常修改 Python 代码、测试、规则资产或静态前端时，不需要重建 `thesis-review-uno-dev` 镜像；修改 `Dockerfile.uno-dev`、`pyproject.toml`、`uv.lock` 或 apt 依赖时才重建。

## 规则开发

- `rule.yml` 是运行时规则元数据；`case.yml` 是样本期望命中规则，只用于测试。
- Word 样本只放在 `thesis_review/docs/rules/<module>/samples/`。
- 规则编号使用小写英文全词和三位数字，例如 `table-of-contents-title-006`。
- 一个 `rule_id` 只代表一个原子检查点；已发布编号不能改名或复用，废弃时改为 `deprecated`。
- 规则代码通过 `IssueFactory.create(rule_id=..., actual=..., location=...)` 创建问题，不硬编码 `message`、`expected`、`severity`。
- 新增规则时先维护 `rule.yml` 和 `case.yml`，再实现检查器并加入 `rules/registry.py`。

## 实现偏好

- 保留 TDD：先写失败测试，再实现，再验证。
- 小改动优先跑最小相关测试；影响共享模型、规则注册、CLI/Web 或 UNO 定位契约时扩大测试范围。
- 涉及真实文档样式、字体继承、批注和保存结果时，以容器内 LibreOffice/UNO 行为为准。
- 不要用 `python-docx` 替代 UNO 做最终格式判定。
