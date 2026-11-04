FROM docker.io/library/debian:trixie-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

ENV UV_PYTHON_PREFERENCE=only-managed
ENV UV_PYTHON_INSTALL_DIR=/opt/python
ENV UV_PROJECT_ENVIRONMENT=/opt/venv
ENV PATH="/opt/venv/bin:$PATH"

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates nodejs npm \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml uv.lock ./

RUN uv sync --locked --extra dev --no-install-project

RUN sass_version=$( \
    python -c 'import tomllib; \
        print( \
            tomllib.load( \
                open("pyproject.toml", "rb") \
            )["tool"]["sass"]["version"] \
        )') \
    && npm install --global "sass@$sass_version" \
    && npm cache clean --force

COPY README.md ./
COPY src/ ./src/

RUN uv sync --locked --extra dev
