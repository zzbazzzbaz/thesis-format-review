# 产品侧后端服务

这是毕业设计格式审核系统的产品侧 Django 后端，负责用户、角色、次数、审核任务、历史记录、文件下载权限和教师统计。真实论文审核由独立的 `thesis_review` 服务通过内网 HTTP API 完成。

## 开发运行

```bash
uv sync
cp .env.example .env
uv run python manage.py migrate
uv run python manage.py runserver 0.0.0.0:8000
```

Django Admin 使用 `django-simpleui`，管理后台在 `/admin/`。Django API 文档默认在 `/api/docs`，后端健康检查在 `/healthz` 和 `/api/healthz`。

## 后台审核 Worker

```bash
uv run python manage.py review_worker
```

首版 worker 使用 SQLite 中的任务状态作为轻量队列，只建议运行一个进程。

## 环境变量

| 变量 | 默认值 | 说明 |
|---|---|---|
| `DJANGO_SECRET_KEY` | 开发默认值 | Django 密钥，生产环境必须设置 |
| `DJANGO_DEBUG` | `true` | 是否开启调试 |
| `DJANGO_LOG_LEVEL` | `INFO` | 日志级别 |
| `DJANGO_ALLOWED_HOSTS` | `localhost,127.0.0.1,0.0.0.0` | 允许访问的 Host |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | 空 | CSRF 可信来源 |
| `SQLITE_DB_PATH` | `backend/data/db.sqlite3` | SQLite 数据库路径 |
| `MEDIA_ROOT` | `backend/media` | 上传和审核产物目录 |
| `THESIS_REVIEW_BASE_URL` | `http://127.0.0.1:8001` | `thesis_review` 服务地址 |
| `THESIS_REVIEW_TIMEOUT_SECONDS` | `300` | 审核请求超时时间 |
