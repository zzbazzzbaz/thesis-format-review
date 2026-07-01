# 产品侧前端

Vue 3 + TypeScript + Vite 单页应用。前端只调用产品侧 Django API，不直接访问 `thesis_review`。

## 开发运行

```bash
npm install
npm run dev
```

默认 API 地址在 `.env` 和 `.env.example` 中配置：

```bash
VITE_API_BASE_URL=http://127.0.0.1:8000/
```

## 常用命令

```bash
npm run typecheck
npm run build
```

`npm run build` 会先执行 `vue-tsc --noEmit`，再执行 Vite 生产构建。

## 后端联调

从 `backend/` 目录运行产品侧 Django 后端：

```bash
uv sync
uv run python manage.py migrate
uv run python manage.py runserver 0.0.0.0:8000
```

后台审核 Worker：

```bash
uv run python manage.py review_worker
```

`review_worker` 会调用后端环境变量 `THESIS_REVIEW_BASE_URL` 指向的 `thesis_review` 服务。前端无需也不应直接访问该服务。

## 功能范围

- 学生端：登录、查看个人信息和剩余次数、上传 `.docx`、查看任务进度、历史记录、下载原文/标注 Word/`issues.json`。
- 教师端：登录、查看统计、查看自己学生提交、筛选任务、查看详情、下载原文和审核结果。
- 管理员：不提供 Vue 前端入口，请使用 Django Admin。
- `issues.json` 首版只下载，不在前端预览。
