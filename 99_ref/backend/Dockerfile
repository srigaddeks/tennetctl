# ── Stage 1: Build dependencies into an isolated venv ─────────────────────────
FROM python:3.13-slim AS deps

WORKDIR /app

# Install build tools only in this stage — never carried into production
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Create a venv so the final stage gets a clean, self-contained copy
RUN python -m venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# ── Stage 2: Production image ─────────────────────────────────────────────────
FROM python:3.13-slim AS production

WORKDIR /app

# Install system deps: curl + tar + gzip needed by Steampipe installer
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl ca-certificates tar gzip \
    && rm -rf /var/lib/apt/lists/*

# Install Steampipe binary to /usr/local/bin (runs as root, system-wide)
# Note: steampipe refuses to run as root — only install the binary, don't invoke it here
RUN curl -fsSL https://steampipe.io/install/steampipe.sh | sh

# Non-root user — created before any file copies so COPY --chown works
RUN addgroup --gid 10001 appgroup \
    && adduser --uid 10001 --gid 10001 --disabled-password --gecos '' appuser

# Pre-install the GitHub plugin into /home/appuser/.steampipe
# --install-dir is a global flag on the steampipe binary (v2+)
RUN mkdir -p /home/appuser/.steampipe \
    && chown -R appuser:appgroup /home/appuser/.steampipe
USER appuser
RUN steampipe --install-dir /home/appuser/.steampipe plugin install github azuread googledirectory --progress=false --skip-config
USER root

# Copy only the venv — no pip, no setuptools, no compilers
COPY --from=deps --chown=appuser:appgroup /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
# Ensure Python uses the venv even when called as `python`
ENV VIRTUAL_ENV="/app/.venv"

# Copy backend source — 91_scripts included (needed by migration job)
COPY --chown=appuser:appgroup . /app/backend/

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/livez')" || exit 1

CMD ["python", "-m", "uvicorn", "backend.main:app", \
     "--host", "0.0.0.0", \
     "--port", "8000"]
