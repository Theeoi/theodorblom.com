FROM docker.io/library/python:3.14-slim

COPY --from=ghcr.io/astral-sh/uv:0.13.7 /uv /uvx /usr/local/bin/

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends nodejs npm \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./

RUN sass_version=$( \
    python -c 'import tomllib; \
    print(tomllib.load(open("pyproject.toml", "rb"))["tool"]["sass"]["version"])' \
    ) \
    && npm install --global "sass@$sass_version" \
    && npm cache clean --force

ENV UV_PROJECT_ENVIRONMENT=/opt/venv
ENV PATH="/opt/venv/bin:$PATH"
ENV UV_PYTHON_DOWNLOADS=never

COPY uv.lock ./

RUN uv sync --locked --extra dev --no-install-project

COPY README.md ./
COPY src/ ./src

RUN uv sync --locked --extra dev
