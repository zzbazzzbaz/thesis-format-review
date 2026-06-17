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
| `rules` | 注册表 + 各规则，读 `DocumentModel` → `Issue` | 仅 `models` |
| `annotator` | 按 `Issue.location` 写红色底纹 + 批注 | `uno_session` |
| `pipeline` + `cli` | 串联调用，命令行入口 | 以上全部 |

规则层完全不依赖 UNO/LibreOffice，新增一条规则只需写一个类然后注册。

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
docker run --rm -v "$PWD":/workspace -w /workspace \
    thesis-review-uno-dev \
    /opt/venv/bin/python -m thesis_review.cli \
    tests/word/111.docx \
    -o /tmp/marked.docx
```

输出示例：

```text
检查完成：89 处错误，64 处警告 → /tmp/marked.docx
```

### 4. Web 上传下载（浏览器前端）

Web 前端是 FastAPI 挂载的静态页面，不需要单独启动 Node.js/Vite。上传审核会调用 LibreOffice/UNO，因此推荐在 Docker 容器中启动：

```bash
cd thesis_review

docker run --rm -p 8000:8000 -v "$PWD":/workspace -w /workspace \
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
docker run --rm -p 8001:8000 -v "$PWD":/workspace -w /workspace \
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

| rule_id | 类别 | 检查内容 | 期望值 |
|---------|------|----------|--------|
| `format.body.font` | 格式 | 正文中文字体 | 宋体 |
| `format.body.size` | 格式 | 正文字号 | 12pt（小四） |
| `format.body.line_spacing` | 格式 | 正文行距 | 1.5 倍 |
| `format.body.indent` | 格式 | 正文首行缩进 | 2 字符 |
| `structure.heading.hierarchy` | 结构 | 标题层级不跳级 | 一级后不可直接三级 |
| `structure.section.required` | 结构 | 必备章节 | 摘要 / 关键词 / 参考文献 |

## 项目结构

```text
thesis_review/
├── pyproject.toml          # 项目配置（pydantic + pytest）
├── Dockerfile.uno-dev      # UNO 开发镜像
├── README.md
├── src/
│   └── thesis_review/
│       ├── cli.py              # 命令行入口
│       ├── pipeline.py         # 三步管道串联
│       ├── models.py           # DocumentModel / Issue / Location
│       ├── uno_session.py      # soffice 进程管理
│       ├── uno_traversal.py    # UNO 段落/run 定位遍历契约
│       ├── extractor.py        # UNO 读 → DocumentModel
│       ├── annotator.py        # Issue → marked.docx（红色底纹 + 批注）
│       └── rules/
│           ├── base.py         # Rule 协议
│           ├── registry.py     # 规则注册表
│           ├── format_rules.py # 4 条格式规则
│           └── structure_rules.py # 2 条结构规则
└── tests/
    ├── conftest.py
    ├── test_extractor.py
    ├── test_format_rules.py
    ├── test_structure_rules.py
    ├── test_annotator.py
    ├── test_roundtrip.py
    ├── test_pipeline.py
    └── word/               # 测试用 .docx 文档
```

## 设计决策

- **为什么用 LibreOffice + UNO 而不是 python-docx**：docx 格式属性大量依赖样式继承链和主题字体，python-docx 不解析这些，会返回 `None` 导致大面积漏检。LibreOffice 导入时已将所有继承与主题计算为最终生效值，UNO API 直接读有效格式。
- **为什么引擎不可替换**：extractor 与 annotator 使用同一套 UNO 枚举顺序分配/反查段落索引，定位契约单引擎闭环。换引擎意味着重建这一闭环。
- **并发模型**：单实例 soffice 串行处理，实现最简最稳。未来可升级为实例池，对上层接口不变。
