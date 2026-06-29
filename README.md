# 毕业设计论文格式审核系统

本项目用于审核 `.docx` 毕业设计论文格式，输出带标注的 `marked.docx` 和结构化问题清单 `issues.json`。

## 目录

```text
thesis_review/
├── Dockerfile          # CI 构建和发布的应用镜像
├── Dockerfile.uno-dev  # 本地开发和测试使用的 Docker 镜像
├── pyproject.toml
├── src/
├── tests/
└── docs/rules/
```

## 构建本地测试镜像

```bash
cd thesis_review
docker build -f Dockerfile.uno-dev -t thesis-review-uno-dev .
```

## 测试

只保留两种测试方式，全部通过 Docker 镜像运行。

### 不启用 UNO 的测试

```bash
cd thesis_review
docker run --rm -v "$PWD":/workspace -w /workspace \
  thesis-review-uno-dev \
  /opt/venv/bin/python -m pytest tests -m "not uno" -q
```

### 启用 UNO 的测试

```bash
cd thesis_review
docker run --rm -v "$PWD":/workspace -w /workspace \
  thesis-review-uno-dev \
  /opt/venv/bin/python -m pytest tests -m uno -v
```

## 启动方式

#### cli启动

```bash
cd thesis_review
docker run --rm -v "$PWD":/workspace -w /workspace \
  thesis-review-uno-dev \
  /opt/venv/bin/python -m thesis_review.interfaces.cli review \
  docs/rules/table-of-contents/samples/table-of-contents-clean.docx \
  --out-dir outputs/review
```

#### Web 服务

```bash
cd thesis_review
docker run --rm -p 8000:8000 -v "$PWD":/workspace -w /workspace \
  thesis-review-uno-dev \
  /opt/venv/bin/python -m uvicorn thesis_review.interfaces.web.app:app \
  --host 0.0.0.0 --port 8000
```

浏览器访问 `http://127.0.0.1:8000/`。
