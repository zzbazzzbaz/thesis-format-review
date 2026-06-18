# 毕业设计论文格式审核系统

自动检测 `.docx` 格式的毕业设计论文中的格式与结构问题，并在文档中以**红色底纹 + 批注**标注，输出 `marked.docx` 供学生/导师查看修改。

## 架构

三步管道，层间靠数据模型解耦：

```text
input.docx → extractor → DocumentModel → rules → list[Issue] → annotator → marked.docx
```

| 模块 | 职责 | 依赖 |
|------|------|------|
| `uno_session` | 管理 soffice 进程/连接，单实例串行 | pyuno |
| `extractor` | UNO 读取文档属性 → `DocumentModel` | `uno_session` |
| `models` | 定义 `DocumentModel` / `Issue` / `Location` | pydantic |
| `rules` | catalog + context + 检查器，读 `DocumentModel` → `Issue` | 仅 `models`/`sections` |
| `annotator` | 按 `Issue.location` 写红色底纹 + 批注 | `uno_session` |
| `pipeline` + `cli` | 串联调用，命令行入口 | 以上全部 |

规则层完全不依赖 UNO/LibreOffice。规则元数据集中在 `thesis_review/docs/rules/**/rule.yml`，代码只负责定位、判断、生成实际值和位置。

## 环境要求

- **Python 3.12**（见 `.python-version`）
- **LibreOffice** + **python3-uno**（不是 pip 包，随系统安装）
- 开发使用 `uv` 管理依赖

宿主机（macOS）无法直接安装 `python3-uno`，UNO 相关测试与运行通过 Docker 容器进行。

## 快速开始

### 1. 安装 Python 依赖

```bash
uv sync --extra dev
```

### 2. 构建 UNO 开发镜像

```bash
docker build -f Dockerfile.uno-dev -t thesis-review-uno-dev .
```

### 3. 运行格式审核

```bash
cd thesis_review
docker run --rm -v "$PWD":/workspace -w /workspace \
    thesis-review-uno-dev \
    /opt/venv/bin/python -m thesis_review.cli \
    tests/word/111.docx \
    -o /tmp/marked.docx
```

输出示例：

```text
检查完成：N 处错误，M 处警告 → /tmp/marked.docx
```

### 4. Web 上传下载（浏览器前端）

Web 前端是 FastAPI 挂载的静态页面，不需要单独启动 Node.js/Vite。上传审核会调用 LibreOffice/UNO，因此推荐在 Docker 容器中启动：

```bash
cd thesis_review

docker run --rm -p 8000:8000 \
    -v "$PWD":/workspace -w /workspace \
    thesis-review-uno-dev \
    /opt/venv/bin/python -m uvicorn thesis_review.web.app:app \
    --host 0.0.0.0 --port 8000
```

启动后浏览器访问：

```text
http://127.0.0.1:8000/
```

选择 `.docx` 文件并提交。服务会同步调用现有 `pipeline.review(input_docx, output_docx)`，审核完成后直接返回 `<原文件名>.marked.docx` 下载。终端中按 `Ctrl+C` 停止服务。

如果宿主机的 `8000` 端口已被占用，可以改用宿主机其他端口，例如：

```bash
docker run --rm -p 8001:8000 \
    -v "$PWD":/workspace -w /workspace \
    thesis-review-uno-dev \
    /opt/venv/bin/python -m uvicorn thesis_review.web.app:app \
    --host 0.0.0.0 --port 8000
```

此时浏览器访问 `http://127.0.0.1:8001/`。

仅在宿主机已经具备可用 LibreOffice/UNO 环境时，也可以直接启动 FastAPI：

```bash
uv run uvicorn thesis_review.web.app:app --host 127.0.0.1 --port 8000
```

首版 Web 层不包含登录、数据库、任务队列、历史记录或在线预览。CLI 入口保持不变：

```bash
thesis-review input.docx -o output.marked.docx
```

### 5. 运行测试

```bash
# 宿主机纯 Python 测试（不含 UNO）
uv run pytest -m "not uno" -q

# 容器内全量测试
docker run --rm -v "$PWD":/workspace -w /workspace \
    thesis-review-uno-dev \
    /opt/venv/bin/python -m pytest -q

# 仅 UNO 测试
docker run --rm -v "$PWD":/workspace -w /workspace \
    thesis-review-uno-dev \
    /opt/venv/bin/python -m pytest -m uno -v
```

## 规则清单

| rule_id | 检查内容 | 期望值 |
|---------|----------|--------|
| `table-of-contents-title-001` | 目录标题文本 | 目    录 |
| `table-of-contents-title-002` | 目录标题字号 | 三号（16pt） |
| `table-of-contents-title-003` | 目录标题中文字体 | 黑体 |
| `table-of-contents-title-004` | 目录标题居中 | 居中 |
| `table-of-contents-title-005` | 目录标题行距 | 1.5 倍 |
| `table-of-contents-title-006` | 目录标题后空行 | 1 个空段落 |
| `table-of-contents-entry-001` | 一级目录空格 | 2 个空格 |
| `table-of-contents-entry-002` | 二级目录空格 | 1 个空格 |
| `table-of-contents-entry-003` | 三级目录空格 | 1 个空格 |
| `table-of-contents-entry-004` | 目录条目中文字体 | 宋体 |
| `table-of-contents-entry-005` | 目录条目数字和西文字体 | Times New Roman |
| `table-of-contents-entry-006` | 目录条目字号 | 小四（12pt） |
| `table-of-contents-entry-007` | 目录条目行距 | 1.5 倍 |
| `table-of-contents-entry-008` | 目录条目不加粗 | 不加粗 |

## 项目结构

```text
thesis_review/
├── pyproject.toml          # 项目配置（pydantic + pytest）
├── Dockerfile.uno-dev      # UNO 开发镜像
├── README.md
├── docs/
│   └── rules/
│       └── table-of-contents/
│           ├── rule.yml          # 目录模块规则元数据
│           ├── case.yml          # 目录模块 Word 样本预期
│           └── samples/          # 用户手动维护的真实 Word 样本
├── src/
│   └── thesis_review/
│       ├── cli.py              # 命令行入口
│       ├── pipeline.py         # 三步管道串联
│       ├── models.py           # DocumentModel / Issue / Location
│       ├── uno_session.py      # soffice 进程管理
│       ├── uno_traversal.py    # UNO 段落/run 定位遍历契约
│       ├── extractor.py        # UNO 读 → DocumentModel
│       ├── annotator.py        # Issue → marked.docx（红色底纹 + 批注）
│       ├── sections.py         # 文档语义分区（目录/正文/参考文献等）
│       └── rules/
│           ├── base.py         # RuleChecker 协议
│           ├── context.py      # RuleContext 共享上下文
│           ├── issue_factory.py # 统一 Issue 创建
│           ├── registry.py     # 检查器注册表
│           ├── catalog/        # rule.yml / case.yml 加载
│           └── toc_rules.py    # 目录模块检查器
└── tests/
    ├── conftest.py
    ├── test_extractor.py
    ├── test_toc_rules.py
    ├── test_sections.py
    ├── test_annotator.py
    ├── test_roundtrip.py
    ├── test_pipeline.py
    └── word/               # 测试用 .docx 文档
```

## 设计决策

- **为什么用 LibreOffice + UNO 而不是 python-docx**：docx 格式属性大量依赖样式继承链和主题字体，python-docx 不解析这些，会返回 `None` 导致大面积漏检。LibreOffice 导入时已将所有继承与主题计算为最终生效值，UNO API 直接读有效格式。
- **为什么引擎不可替换**：extractor 与 annotator 使用同一套 UNO 枚举顺序分配/反查段落索引，定位契约单引擎闭环。换引擎意味着重建这一闭环。
- **并发模型**：单实例 soffice 串行处理，实现最简最稳。未来可升级为实例池，对上层接口不变。
