# Product backend Dockerfile.
#
# Built by `.gitea/workflows/uno-docker.yml` and published as
# `ghcr.io/zzbazzzbaz/thesis-review-backend`.
FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive
ENV PATH="/root/.local/bin:/opt/venv/bin:${PATH}"
ENV PYTHONUNBUFFERED=1
ENV UV_INDEX_URL="https://pypi.tuna.tsinghua.edu.cn/simple"

RUN set -eux; \
    find /etc/apt -type f \( -name 'sources.list' -o -name '*.sources' \) -exec sed -i \
        -e 's|http://ports.ubuntu.com/ubuntu-ports|http://mirrors.tuna.tsinghua.edu.cn/ubuntu-ports|g' \
        -e 's|http://archive.ubuntu.com/ubuntu|http://mirrors.tuna.tsinghua.edu.cn/ubuntu|g' \
        -e 's|http://security.ubuntu.com/ubuntu|http://mirrors.tuna.tsinghua.edu.cn/ubuntu|g' \
        {} +; \
    printf '%s\n' \
        'Acquire::Retries "5";' \
        'Acquire::http::Timeout "30";' \
        'Acquire::https::Timeout "30";' \
        > /etc/apt/apt.conf.d/80-retries; \
    apt-get update; \
    apt-get install -y --no-install-recommends \
        ca-certificates \
        curl \
        python3 \
        python3-venv; \
    rm -rf /var/lib/apt/lists/*

RUN curl -LsSf https://astral.sh/uv/install.sh | sh

WORKDIR /app

COPY pyproject.toml uv.lock .python-version ./
RUN uv venv --python 3.12 /opt/venv \
    && UV_PROJECT_ENVIRONMENT=/opt/venv uv sync --frozen --no-dev

COPY manage.py ./
COPY apps ./apps
COPY config ./config

RUN mkdir -p /app/data /app/media /app/staticfiles

EXPOSE 8000

CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", "--timeout", "300"]
