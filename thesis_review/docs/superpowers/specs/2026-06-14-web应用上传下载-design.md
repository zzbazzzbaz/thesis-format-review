# Web 应用上传下载 — 设计文档

日期：2026-06-14
状态：待评审

## 1. 背景与目标

当前系统是 CLI 工具：

```bash
thesis-review input.docx -o output.marked.docx
```

核心审核能力已经收敛在 `pipeline.review(input_docx, output_docx)` 中。Web 化的目标不是重写审核流程，而是在现有 pipeline 外面增加一层很薄的 HTTP 和页面适配：

```text
浏览器上传 .docx
    -> FastAPI 接收文件
    -> 保存到临时目录
    -> 调用 pipeline.review(input, output)
    -> 浏览器下载 marked.docx
```

首版只做单机同步处理。后期投入使用后，如果需要高并发、高可用，再扩展为任务队列、状态查询和异步下载。

## 2. 范围

首版包含：

- 一个 HTML 页面，用于选择并上传原始 `.docx`
- 一个 FastAPI 上传接口，接收 `.docx`
- 调用现有 `pipeline.review()` 生成标注后的 `.docx`
- 审核完成后直接返回文件下载
- 保留现有 CLI，不改变 `thesis-review input.docx -o output.docx`

首版不包含：

- 登录、用户、权限
- 数据库
- 任务队列、后台 worker、进度查询
- 文件长期存储和历史记录
- 多实例并发调度
- PDF 预览或在线查看
- 前端构建链

## 3. 技术选择

Web 框架使用 FastAPI。

接口采用 FastAPI 标准能力：

- `UploadFile` 接收上传文件
- `FileResponse` 返回生成后的 `.docx`
- `StaticFiles` 服务静态 HTML/CSS

页面使用静态 HTML，不引入 Jinja2。理由是页面只需要一个上传表单和基础状态提示，模板引擎没有实际收益。

运行方式采用标准 uvicorn：

```bash
cd thesis_review
uv run uvicorn thesis_review.web.app:app --host 0.0.0.0 --port 8000
```

不新增 `thesis-review-web` 脚本入口，避免和现有 CLI 入口混在一起。后续需要演示便利时再加脚本。

## 4. 目录规划

新增目录放在 `src/thesis_review/web/` 下，作为 `thesis_review` 包内的 Web 适配层。

```text
thesis_review/
├── src/thesis_review/
│   ├── web/
│   │   ├── __init__.py
│   │   ├── app.py          # 创建 FastAPI app，挂载静态资源，注册路由
│   │   ├── routes.py       # GET / 页面，POST /api/review 上传并返回 docx
│   │   ├── services.py     # 保存上传文件、调用 pipeline.review、管理临时输出
│   │   └── static/
│   │       ├── index.html  # 上传页面
│   │       └── style.css   # 简单样式
│   ├── pipeline.py         # 保持不变，CLI/Web 共同调用
│   └── cli.py              # 保持 CLI 可用
├── tests/
│   ├── test_web_app.py
│   └── test_web_routes.py
└── pyproject.toml
```

### 4.1 `app.py`

职责：

- 创建 `FastAPI(title="毕业设计格式审核系统")`
- 挂载 `/static`
- 注册 routes

`app.py` 不处理上传逻辑，不直接调用 `pipeline.review()`。

### 4.2 `routes.py`

职责：

- `GET /`：返回 `static/index.html`
- `POST /api/review`：接收上传文件，调用 service，返回 `FileResponse`
- 把用户输入错误转换为 HTTP 400

`routes.py` 不关心临时目录细节，也不直接操作 LibreOffice/UNO。

### 4.3 `services.py`

职责：

- 校验上传文件名后缀为 `.docx`
- 为单次请求创建临时工作目录
- 把 `UploadFile` 内容写入临时输入文件
- 生成输出文件名，例如 `原文件名.marked.docx`
- 调用 `pipeline.review(input_docx, output_docx)`
- 返回输出文件路径和下载文件名

服务层是后续扩展任务队列的替换点。首版同步调用 pipeline；后续可以把这里改成“创建任务并交给 worker”。

## 5. HTTP 接口

### 5.1 页面

```http
GET /
```

返回上传页面。

页面要求：

- 只显示一个 `.docx` 文件选择控件
- 一个提交按钮
- 上传过程中禁用按钮并显示“正在审核”
- 成功后浏览器下载返回文件
- 上传失败时显示简短错误

页面文案保持克制，不写大量功能说明。

### 5.2 上传审核

```http
POST /api/review
Content-Type: multipart/form-data

file=<uploaded .docx>
```

成功响应：

```http
200 OK
Content-Type: application/vnd.openxmlformats-officedocument.wordprocessingml.document
Content-Disposition: attachment; filename="<original-stem>.marked.docx"
```

错误响应：

- 非 `.docx`：`400 Bad Request`
- 空文件名：`400 Bad Request`
- FastAPI 参数缺失：`422 Unprocessable Entity`
- 审核过程异常：`500 Internal Server Error`

500 响应只返回简短错误，不暴露服务器路径和堆栈。

## 6. 临时文件策略

首版使用请求级临时目录，但不能用 `with TemporaryDirectory()` 包住 `FileResponse`，否则目录会在响应发送前被删除。实现应显式创建目录，再交给 `BackgroundTask` 在响应完成后清理：

```python
workdir = Path(tempfile.mkdtemp(prefix="thesis-review-"))
input_path = workdir / "input.docx"
output_path = workdir / "output.marked.docx"
cleanup = lambda: shutil.rmtree(workdir, ignore_errors=True)
```

`FileResponse` 需要在响应发送期间能读取输出文件。route 返回时把清理回调绑定到响应：

```python
return FileResponse(
    output_path,
    filename=download_name,
    background=BackgroundTask(cleanup),
)
```

上传文件名只用于生成下载名。实际保存路径应使用安全文件名或固定文件名，避免路径穿越。

## 7. 依赖变更

`pyproject.toml` 增加运行依赖：

```toml
dependencies = [
    "pydantic>=2.0",
    "fastapi>=0.115",
    "uvicorn[standard]>=0.30",
    "python-multipart>=0.0.9",
]
```

测试依赖增加：

```toml
dev = [
    "pytest>=8.0",
    "python-docx>=1.1",
    "httpx>=0.27",
]
```

`python-multipart` 是 FastAPI 处理 multipart 上传所需依赖。`httpx` 用于 FastAPI TestClient 相关测试。

## 8. 测试计划

纯 Python 测试：

- `GET /` 返回 200，内容包含上传表单
- `POST /api/review` 拒绝非 `.docx`
- service 能把上传文件保存到工作目录，并生成 `.marked.docx` 下载名
- route 层测试中 monkeypatch `pipeline.review()`，避免纯 Python 测试依赖 UNO

UNO 集成测试：

- 使用现有 `sample.docx` 调用 `POST /api/review`
- 响应为 `.docx` 下载
- 返回内容可写入文件并被 LibreOffice 打开

验证命令：

```bash
cd thesis_review
uv run pytest -m "not uno" -q
```

```bash
cd thesis_review
docker run --rm -v "$PWD":/workspace -w /workspace \
  thesis-review-uno-dev \
  /opt/venv/bin/python -m pytest -q
```

## 9. 后期扩展路径

当前同步流程：

```text
POST /api/review
    -> 保存上传文件
    -> review(input_docx, output_docx)
    -> FileResponse(output_docx)
```

后期高并发/高可用流程：

```text
POST /api/review
    -> 创建 job
    -> worker 执行 review(input_docx, output_docx)

GET /api/jobs/{id}
    -> 查询状态

GET /api/jobs/{id}/download
    -> 下载结果
```

为了保留这条演进路径，本次实现要求：

- Web route 不直接调用 `pipeline.review()`，只调用 `services.py`
- 临时文件管理集中在 `services.py`
- 不把任务状态、上传目录、输出目录散落到 route 或 app 初始化里
- CLI 不依赖 Web，Web 依赖 pipeline，二者保持单向关系
