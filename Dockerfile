# Server image — FastAPI + the game engine.
#
# The packages are installed from `poetry.lock`, main dependencies only: the same versions the
# development environment and the tests run on, with no hand-kept list in between. (Until
# 2026-11-18 the image installed `server/requirements-server.txt`, a filtered `pip freeze` of the
# working environment, because the main dependencies then included sentence-transformers and with
# it several GB of GPU packages. Fine-tuning now has its own environment, `training/`.)
#
# Two stages. The first has Poetry and installs the packages into a virtual environment; the
# second copies that environment and the code, so Poetry itself is not in the served image.

FROM python:3.11.12-slim AS builder

ENV PIP_NO_CACHE_DIR=1 \
    POETRY_VERSION=2.1.3 \
    POETRY_NO_INTERACTION=1 \
    VIRTUAL_ENV=/opt/venv \
    PATH="/opt/venv/bin:$PATH"

# Poetry goes into the system Python and the application's packages into /opt/venv: Poetry
# installs into the virtual environment that is active (VIRTUAL_ENV), and only that is copied on.
RUN pip install "poetry==${POETRY_VERSION}" && python -m venv /opt/venv

WORKDIR /app
COPY pyproject.toml poetry.lock ./
# --no-root: the project's own code is copied in the next stage, not installed as a package.
RUN poetry install --only main --no-root

FROM python:3.11.12-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# psycopg[binary] ships its own libpq, so no build toolchain is needed at runtime.
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /opt/venv /opt/venv
ENV VIRTUAL_ENV=/opt/venv \
    PATH="/opt/venv/bin:$PATH"

# Only what the server actually serves with. Notebooks, evaluation/, evidence/ and the
# frontend are deliberately absent.
COPY Agents/ ./Agents/
COPY server/ ./server/
COPY alembic/ ./alembic/
COPY alembic.ini ./alembic.ini
COPY pyproject.toml ./pyproject.toml

RUN useradd --create-home --uid 1001 werewolf && chown -R werewolf:werewolf /app
USER werewolf

# The commit this image was built from, stamped on every trace as its release. The image has no
# git history, so without it the engine can only say "unknown". Last, so that a new commit
# rebuilds this layer and nothing above it. Build with:
#     GIT_COMMIT=$(git rev-parse HEAD) docker compose build wolf-server
ARG GIT_COMMIT=unknown
ENV LANGFUSE_RELEASE=${GIT_COMMIT}

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD curl -fsS http://localhost:8000/health || exit 1

CMD ["uvicorn", "server.app:app", "--host", "0.0.0.0", "--port", "8000"]
