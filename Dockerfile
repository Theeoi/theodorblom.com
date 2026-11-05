FROM docker.io/library/debian:trixie-slim AS development

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
COPY scripts/compile_sass.py ./scripts/compile_sass.py

RUN uv sync --locked --extra dev

RUN uv run --locked --extra dev --no-sync scripts/compile_sass.py


FROM development AS production-build

RUN uv sync --locked --no-dev --extra deploy --no-editable


FROM docker.io/library/debian:trixie-slim AS production

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY --from=production-build /opt/python /opt/python
COPY --from=production-build /opt/venv /opt/venv

ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV THEODORBLOM_INSTANCE_PATH=/instance

WORKDIR /app

EXPOSE 8000

CMD ["gunicorn", \
     "--workers=2", \
     "--bind=0.0.0.0:8000", \
     "--access-logfile=-", \
     "--error-logfile=-", \
     "app:create_app(mode=\"production\")"]
