# syntax=docker/dockerfile:1

FROM python:3.14.9-slim-trixie AS build

COPY --from=ghcr.io/astral-sh/uv:0.13.5 /uv /bin/uv

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never \
    UV_PROJECT_ENVIRONMENT=/app/.venv

WORKDIR /app

# Install the exact versions pinned in uv.lock (the project itself is not a package).
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project


FROM python:3.14.9-slim-trixie

LABEL org.opencontainers.image.source="https://github.com/penguin-statistics/ArkPlanner"

RUN apt-get update \
    && apt-get install -y --no-install-recommends tini \
    && rm -rf /var/lib/apt/lists/*

RUN useradd --system --uid 10001 --home-dir /app --shell /usr/sbin/nologin planner

WORKDIR /app

COPY --from=build /app/.venv /app/.venv
COPY --chown=planner:planner . .

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1

USER planner

EXPOSE 8020

ENTRYPOINT ["/usr/bin/tini", "--"]
CMD [ "python", "-m", "sanic", "server.app", "--host=0.0.0.0", "--port=8020", "--workers=2" ]
