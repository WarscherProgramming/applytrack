# ============================================================
# Stage 1: base — shared environment, virtual env creation
# ============================================================
FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH"

WORKDIR /app

RUN python -m venv /opt/venv && \
    pip install --no-cache-dir --upgrade pip


# ============================================================
# Stage 2: development — editable install + dev dependencies
# ============================================================
FROM base AS development

COPY pyproject.toml .

# Editable install (-e) creates a .pth file pointing to /app.
# When the source is volume-mounted at /app at runtime, Python
# picks up live changes without rebuilding the image.
RUN pip install --no-cache-dir -e ".[dev]"

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]


# ============================================================
# Stage 3: production — locked deps, minimal image, non-root user
# ============================================================
FROM base AS production

COPY pyproject.toml .
RUN pip install --no-cache-dir .

COPY . .

# Run as a non-root user to limit blast radius if the app is compromised.
RUN adduser --disabled-password --gecos "" appuser && \
    chown -R appuser:appuser /app /opt/venv
USER appuser

EXPOSE 8000
# Adjust --workers to match your container's CPU allocation (2 * cores + 1).
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
