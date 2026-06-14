# 项目级 AGENTS.md

本项目默认使用简体中文沟通。除非用户另有说明，开发和测试以 `thesis_review/` Python 子项目为工作目录。

## 项目结构

- `docs/superpowers/specs/`：设计文档
- `docs/superpowers/plans/`：实现计划
- `thesis_review/`：毕业设计格式审核系统 Python 子项目

## Python 与依赖

- Python 版本固定为 3.12，见 `thesis_review/.python-version`
- `thesis_review/pyproject.toml` 使用 `requires-python = ">=3.12,<3.13"`
- 宿主机开发优先使用 `uv`
- Docker/UNO 开发镜像中也使用 `uv` 安装 Python 依赖
- LibreOffice/UNO 不是 pip 依赖；容器内通过 apt 安装 `libreoffice-writer` 和 `python3-uno`
- 容器中的虚拟环境固定在 `/opt/venv`，创建时使用 `--system-site-packages`，以便 `/opt/venv/bin/python` 能 import apt 安装的 `uno`

## UNO 开发镜像

镜像 Dockerfile 位于：

```bash
thesis_review/Dockerfile.uno-dev
```

构建镜像：

```bash
cd thesis_review
docker build -f Dockerfile.uno-dev -t thesis-review-uno-dev .
```

只有以下情况通常需要重建镜像：

- 修改 `Dockerfile.uno-dev`
- 修改 `pyproject.toml` 或 `uv.lock` 中的依赖
- 新增 apt 级依赖，例如字体或 LibreOffice 组件
- 主动刷新 Ubuntu/LibreOffice 基础环境

日常修改 Python 代码、测试、fixture 时，不需要重建镜像；源码通过 volume 挂载进容器。

## 测试命令

所有命令默认从 `thesis_review/` 目录运行。

宿主机纯 Python 测试：

```bash
uv run pytest -m "not uno" -q
```

容器内全量当前测试：

```bash
docker run --rm -v "$PWD":/workspace -w /workspace \
  thesis-review-uno-dev \
  /opt/venv/bin/python -m pytest -q
```

容器内纯 Python 测试：

```bash
docker run --rm -v "$PWD":/workspace -w /workspace \
  thesis-review-uno-dev \
  /opt/venv/bin/python -m pytest -m "not uno" -q
```

容器内 UNO 测试：

```bash
docker run --rm -v "$PWD":/workspace -w /workspace \
  thesis-review-uno-dev \
  /opt/venv/bin/python -m pytest -m uno -v
```

容器内单文件测试示例：

```bash
docker run --rm -v "$PWD":/workspace -w /workspace \
  thesis-review-uno-dev \
  /opt/venv/bin/python -m pytest tests/test_uno_session.py -m uno -v
```

容器内生成 fixture 示例：

```bash
docker run --rm -v "$PWD":/workspace -w /workspace \
  thesis-review-uno-dev \
  /opt/venv/bin/python tests/fixtures/make_fixtures.py
```

## UNO 开发约束

- 涉及 LibreOffice/UNO 的测试必须在 Docker 容器中运行，不依赖 macOS 宿主机 LibreOffice
- UNO 测试使用 `@pytest.mark.uno`
- `SOFFICE_BIN` 默认是 `/usr/bin/soffice`
- 优先使用一次性 `docker run --rm` 跑测试，避免残留 soffice 进程污染下一次测试
- 若需要调试容器环境，可进入 shell：

```bash
cd thesis_review
docker run --rm -it -v "$PWD":/workspace -w /workspace thesis-review-uno-dev bash
```

进入后使用：

```bash
/opt/venv/bin/python -m pytest -m uno -v
/opt/venv/bin/python -c "import uno; print('uno ok')"
soffice --version
```

## 实现方式

- 按 `docs/_chat/执行方式决策.md` 的任务分组执行
- Task 11-12 属于“UNO 会话”组：fixture + `uno_session`
- Task 11-12 使用独立 subagent + 独立 review
- 保留 TDD：先写失败测试，再实现，再在容器中验证
- UNO 层计划中的 API 代码只作为参考，真实实现以容器中 LibreOffice/UNO 行为和测试断言为准
