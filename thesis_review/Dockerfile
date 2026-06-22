FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive
ENV PATH="/root/.local/bin:/opt/venv/bin:${PATH}"
ENV SOFFICE_BIN="/usr/bin/soffice"
ENV PYTHONPATH="/app/src"
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
        fontconfig \
        fonts-noto-cjk \
        fonts-noto-cjk-extra \
        libreoffice-writer \
        python3 \
        python3-pip \
        python3-uno \
        python3-venv; \
    rm -rf /var/lib/apt/lists/*

RUN curl -LsSf https://astral.sh/uv/install.sh | sh

WORKDIR /app

COPY pyproject.toml uv.lock .python-version ./
RUN uv venv --python 3.12 --system-site-packages /opt/venv \
    && UV_PROJECT_ENVIRONMENT=/opt/venv uv sync --frozen

COPY src ./src
COPY docs/rules ./docs/rules

EXPOSE 8000

CMD ["/opt/venv/bin/python", "-m", "uvicorn", "thesis_review.interfaces.web.app:app", "--host", "0.0.0.0", "--port", "8000"]
