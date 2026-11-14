FROM python:3.13-slim AS build

COPY --from=ghcr.io/astral-sh/uv:0.8.14 /uv /bin/uv
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=0

WORKDIR /app

# Dependencies first, so this layer is cached until uv.lock changes.
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev --no-install-project

COPY README.md ./
COPY jumbaq ./jumbaq
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev --no-editable


FROM python:3.13-slim

RUN groupadd --system --gid 1000 jumbaq \
    && useradd --system --uid 1000 --gid jumbaq --no-create-home jumbaq

COPY --from=build --chown=jumbaq:jumbaq /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1

USER jumbaq
WORKDIR /app
COPY --chown=jumbaq:jumbaq alembic.ini ./
COPY --chown=jumbaq:jumbaq migrations ./migrations
EXPOSE 8000

# X-Forwarded-* headers are trusted only from FORWARDED_ALLOW_IPS (uvicorn reads it).
ENV FORWARDED_ALLOW_IPS=127.0.0.1
CMD ["uvicorn", "jumbaq.main:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000", \
     "--proxy-headers"]
