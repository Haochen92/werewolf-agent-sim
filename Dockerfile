# Server image — FastAPI + the game engine.
#
# Installs `server/requirements-server.txt`, NOT the full Poetry environment. That file is a
# lock-accurate `pip freeze` of the working venv with the ML stack filtered out
# (torch / sentence-transformers / transformers / scipy / pandas / matplotlib and friends):
# `server.app`'s entire import closure was measured and contains none of them, and live games
# are memory-OFF by project ruling, so the retrieval stack that needs them is never reached.
# The saving is multiple GB of GPU wheels in an image that would never import one.
#
# If a future slice turns memory back on for served games, this file is where that shows up —
# the import will fail loudly at startup rather than silently degrade.

FROM python:3.11.12-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# psycopg[binary] ships its own libpq, so no build toolchain is needed at runtime.
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

COPY server/requirements-server.txt ./server/requirements-server.txt
RUN pip install --no-cache-dir -r server/requirements-server.txt

# Only what the server actually serves with. Notebooks, evaluation/, evidence/ and the
# frontend are deliberately absent.
COPY Agents/ ./Agents/
COPY server/ ./server/
COPY alembic/ ./alembic/
COPY alembic.ini ./alembic.ini
COPY pyproject.toml ./pyproject.toml

RUN useradd --create-home --uid 1001 werewolf && chown -R werewolf:werewolf /app
USER werewolf

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD curl -fsS http://localhost:8000/health || exit 1

CMD ["uvicorn", "server.app:app", "--host", "0.0.0.0", "--port", "8000"]
