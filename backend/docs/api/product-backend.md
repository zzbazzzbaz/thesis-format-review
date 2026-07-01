# 产品侧后端 API 与运行说明

## 服务边界

前端只访问 Django 产品侧后端。产品侧后端保存用户、次数、任务和文件产物，再由 `review_worker` 调用独立的 `thesis_review` 服务：

```text
POST {THESIS_REVIEW_BASE_URL}/api/review
```

`thesis_review` 仍保持无状态，不保存用户、任务、次数和历史记录。

## 启动

```bash
cd backend
uv sync
cp .env.example .env
uv run python manage.py migrate
uv run python manage.py runserver 0.0.0.0:8000
```

健康检查：

```http
GET /healthz
GET /api/healthz
```

OpenAPI 文档：

```http
GET /api/docs
```

后台 worker：

```bash
cd backend
uv run python manage.py review_worker
```

单次执行一条任务：

```bash
uv run python manage.py review_worker --once
```

## 环境变量

| 变量 | 默认值 |
|---|---|
| `DJANGO_SECRET_KEY` | `dev-only-thesis-review-backend-secret-key` |
| `DJANGO_DEBUG` | `true` |
| `DJANGO_LOG_LEVEL` | `INFO` |
| `DJANGO_ALLOWED_HOSTS` | `localhost,127.0.0.1,0.0.0.0` |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | 空 |
| `SQLITE_DB_PATH` | `backend/data/db.sqlite3` |
| `MEDIA_ROOT` | `backend/media` |
| `THESIS_REVIEW_BASE_URL` | `http://127.0.0.1:8001` |
| `THESIS_REVIEW_TIMEOUT_SECONDS` | `300` |

## 认证

```http
POST /api/auth/login/
POST /api/auth/refresh/
POST /api/auth/logout/
GET /api/me/
```

除登录、刷新、退出外，业务接口使用：

```http
Authorization: Bearer <access-token>
```

## 学生端

```http
GET  /api/student/profile/
POST /api/student/review-tasks/
GET  /api/student/review-tasks/?page=1&page_size=20&status=pending
GET  /api/student/review-tasks/{task_id}/
GET  /api/student/review-tasks/{task_id}/download/source/
GET  /api/student/review-tasks/{task_id}/download/marked/
GET  /api/student/review-tasks/{task_id}/download/issues/
```

上传接口只接受 `.docx`。创建任务成功后会在同一数据库事务中扣减学生剩余次数并记录次数流水。

## 教师端

```http
GET /api/teacher/review-tasks/
GET /api/teacher/review-tasks/{task_id}/
GET /api/teacher/review-tasks/{task_id}/download/source/
GET /api/teacher/review-tasks/{task_id}/download/marked/
GET /api/teacher/review-tasks/{task_id}/download/issues/
GET /api/teacher/stats/
```

任务列表支持筛选：

```text
student_no
student_name
status
submitted_from
submitted_to
page
page_size
```

教师只能访问绑定到自己名下学生的任务和文件。

## 测试

```bash
cd backend
uv run pytest
```
