"""Django settings for the product-side thesis review backend."""
from __future__ import annotations

from pathlib import Path

import environ


# -----------------------------------------------------------------------------
# Paths and environment
# -----------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env()
env.read_env(BASE_DIR / ".env")


# -----------------------------------------------------------------------------
# Core settings
# -----------------------------------------------------------------------------
SECRET_KEY = env("DJANGO_SECRET_KEY", default="dev-only-thesis-review-backend-secret-key")
DEBUG = env.bool("DJANGO_DEBUG", default=True)
DJANGO_LOG_LEVEL = env("DJANGO_LOG_LEVEL", default="INFO")

ALLOWED_HOSTS = env.list(
    "DJANGO_ALLOWED_HOSTS",
    default=["localhost", "127.0.0.1", "0.0.0.0"],
)
CSRF_TRUSTED_ORIGINS = env.list("DJANGO_CSRF_TRUSTED_ORIGINS", default=[])


# -----------------------------------------------------------------------------
# Applications and middleware
# -----------------------------------------------------------------------------
INSTALLED_APPS = [
    "simpleui",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "apps.accounts.apps.AccountsConfig",
    "apps.reviews.apps.ReviewsConfig",
    "apps.teachers.apps.TeachersConfig",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"


# -----------------------------------------------------------------------------
# Templates and ASGI/WSGI
# -----------------------------------------------------------------------------
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"


# -----------------------------------------------------------------------------
# Logging
# -----------------------------------------------------------------------------
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "console": {
            "format": "%(asctime)s %(levelname)s [%(name)s] %(message)s",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "console",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": DJANGO_LOG_LEVEL,
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": DJANGO_LOG_LEVEL,
            "propagate": False,
        },
        "django.request": {
            "handlers": ["console"],
            "level": "WARNING",
            "propagate": False,
        },
    },
}


# -----------------------------------------------------------------------------
# Database
# -----------------------------------------------------------------------------
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": env("SQLITE_DB_PATH", default=str(BASE_DIR / "data" / "db.sqlite3")),
    }
}


# -----------------------------------------------------------------------------
# Authentication and localization
# -----------------------------------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    # {
    #     "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    # },
    # {
    #     "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    # },
    # {
    #     "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    # },
    # {
    #     "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    # },
]

LANGUAGE_CODE = "zh-hans"
TIME_ZONE = "Asia/Shanghai"
USE_I18N = True
USE_TZ = True

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
AUTH_USER_MODEL = "accounts.User"


# -----------------------------------------------------------------------------
# Static and media files
# -----------------------------------------------------------------------------
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"] if (BASE_DIR / "static").exists() else []
MEDIA_ROOT = env("MEDIA_ROOT", default=str(BASE_DIR / "media"))
MEDIA_URL = "/media/"


# -----------------------------------------------------------------------------
# Security
# -----------------------------------------------------------------------------
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SESSION_COOKIE_SECURE = env.bool("DJANGO_SESSION_COOKIE_SECURE", default=False)
CSRF_COOKIE_SECURE = env.bool("DJANGO_CSRF_COOKIE_SECURE", default=False)


# -----------------------------------------------------------------------------
# Thesis review service and API tokens
# -----------------------------------------------------------------------------
THESIS_REVIEW_BASE_URL = env(
    "THESIS_REVIEW_BASE_URL",
    default="http://127.0.0.1:8001",
).rstrip("/")
THESIS_REVIEW_TIMEOUT_SECONDS = env.float("THESIS_REVIEW_TIMEOUT_SECONDS", default=300.0)

JWT_ACCESS_TOKEN_SECONDS = env.int("JWT_ACCESS_TOKEN_SECONDS", default=7200)
JWT_REFRESH_TOKEN_SECONDS = env.int("JWT_REFRESH_TOKEN_SECONDS", default=604800)


# -----------------------------------------------------------------------------
# SimpleUI
# -----------------------------------------------------------------------------
SIMPLEUI_HOME_TITLE = "毕业设计格式审核系统"
SIMPLEUI_HOME_ICON = "fa fa-file-word-o"
SIMPLEUI_HOME_INFO = False
SIMPLEUI_ANALYSIS = False
SIMPLEUI_HOME_ACTION = False
SIMPLEUI_CONFIG = {
    "system_keep": False,
    "menus": [
        {
            "name": "账号与人员",
            "icon": "fas fa-users",
            "permission": "accounts.view_user",
            "models": [
                {
                    "name": "后台账号",
                    "icon": "fas fa-user-shield",
                    "url": "/admin/accounts/user/",
                    "permission": "accounts.view_user",
                },
                {
                    "name": "学生资料",
                    "icon": "fas fa-user-graduate",
                    "url": "/admin/accounts/studentprofile/",
                    "permission": "accounts.view_studentprofile",
                },
                {
                    "name": "教师资料",
                    "icon": "fas fa-chalkboard-teacher",
                    "url": "/admin/accounts/teacherprofile/",
                    "permission": "accounts.view_teacherprofile",
                },
            ],
        },
        {
            "name": "论文审核",
            "icon": "fas fa-file-word",
            "permission": "reviews.view_reviewtask",
            "models": [
                {
                    "name": "审核任务",
                    "icon": "fas fa-tasks",
                    "url": "/admin/reviews/reviewtask/",
                    "permission": "reviews.view_reviewtask",
                },
                {
                    "name": "次数流水",
                    "icon": "fas fa-list",
                    "url": "/admin/reviews/reviewquotaledger/",
                    "permission": "reviews.view_reviewquotaledger",
                },
            ],
        },
    ],
    "dynamic": False,
}
