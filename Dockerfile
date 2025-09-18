# ---------- Base (common setup) ----------
FROM python:3.9-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONFAULTHANDLER=1 \
    PIP_NO_CACHE_DIR=1 \
    VIRTUAL_ENV=/venv \
    PATH="/venv/bin:$PATH"

WORKDIR /app

# Minimal runtime deps
RUN set -eux; \
    apt-get update; \
    apt-get install -y --no-install-recommends \
        libpq5 \
        ca-certificates \
        gettext \
    ; \
    rm -rf /var/lib/apt/lists/*

# Non-root user
ARG uid=1000
ARG guid=${uid}
ARG user=appuser
RUN set -eux; \
    groupadd -g "${guid}" "${user}"; \
    useradd --no-log-init -r -u "${uid}" -g "${guid}" -d /app "${user}"; \
    chown "${user}:${user}" /app

# ---------- Build (install dependencies) ----------
FROM base AS build

# Install build dependencies for psycopg2 and other compiled libs
RUN set -eux; \
    apt-get update; \
    apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
    ; \
    rm -rf /var/lib/apt/lists/*

# Virtualenv
RUN python -m venv "$VIRTUAL_ENV"

# Copy only requirements first for better cache
COPY requirements.txt .

# Install deps (upgrade pip first)
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# ---------- Runtime ----------
FROM base AS runtime

# Re-declare build args for this stage
ARG uid=1000
ARG guid=${uid}
ARG user=appuser

# Copy venv with installed packages
COPY --from=build /venv /venv

# Copy project code with correct ownership
COPY --chown=${user}:${user} . /app

# Entrypoint scripts
RUN chmod +x django-entrypoint.sh celery-entrypoint.sh celery-beat-entrypoint.sh

USER ${user}:${user}
EXPOSE 8000

ENV GUNICORN_CMD_ARGS="--bind 0.0.0.0:8000 --workers 3 --timeout 60 --access-logfile - --error-logfile -"
CMD ["gunicorn", "config.wsgi"]