# 毕业论文格式审核平台

面向高校毕业论文的 DOCX 格式审核系统。学生上传论文后，系统按学校规范逐项检查，输出**带中文批注的 Word** 和**结构化问题清单**；教师按指导名单管理学生并查看审核统计；管理员维护学院、专业和账号。

## 架构

```text
Vue 3 前端
   │ REST / JWT
   ▼
Django 产品后端（用户 / 角色 / 任务 / 文件权限）
   │ 内网 HTTP
   ▼
FastAPI 审核引擎（DOCX 解析 + YAML 规则 + Word 批注）
```

## 目录结构

```text
backend/         Django 5 + Django Ninja 产品侧后端
frontend/        Vue 3 + TypeScript + Vite 前端
thesis_review/   FastAPI 审核引擎与规则库
deploy/          Docker Compose 部署配置
```

## 核心能力

- **规则驱动审核**：封面、摘要、目录、正文、图表、公式、参考文献、页眉页脚等规则以 YAML 配置，便于按学校规范调整。
- **Word 原生批注**：审核结果写回 DOCX 批注，学生可以直接在 Word 中查看修改意见。
- **角色隔离**：学生只能看到自己的论文，教师只能看到名下学生，管理员维护账号和专业目录。
- **异步审核 Worker**：上传后排队审核，支持状态查询、失败重试和结果下载。
- **可审计**：保留每次审核的问题数、状态和处理记录。

## 本地运行

### 审核引擎

```bash
cd thesis_review
uv sync
PYTHONPATH=src uv run python -m uvicorn thesis_review.interfaces.web.app:app --host 0.0.0.0 --port 8000
```

更完整的 CLI、Docker 和测试用法见 [`thesis_review/README.md`](thesis_review/README.md)。

### 产品后端

```bash
cd backend
cp .env.example .env
uv sync
uv run python manage.py migrate
uv run python manage.py runserver 0.0.0.0:8000
```

### 前端

```bash
cd frontend
npm install
npm run dev
```

## 测试

```bash
cd backend && uv run pytest
cd frontend && npm run typecheck
```

审核引擎的测试通过 Docker 运行，见 [`thesis_review/README.md`](thesis_review/README.md)。

## 说明

- 本仓库为求职作品集展示版：已移除真实论文、学生数据和部署密钥，规则样本均为脱敏示例。
- 部署配置中的镜像地址已替换为 `ghcr.io` / 示例域名，实际部署时按自己的环境修改。
