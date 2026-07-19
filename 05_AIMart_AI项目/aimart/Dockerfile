# ---------------------------------------------------------------------------
# Stage 1 – builder: install Python dependencies
# ---------------------------------------------------------------------------
FROM python:3.12-slim AS builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy project metadata and install into a virtual env
COPY pyproject.toml README.md* ./
COPY src/ src/

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

RUN pip install --no-cache-dir --upgrade pip setuptools wheel \
    && pip install --no-cache-dir .

# ---------------------------------------------------------------------------
# Stage 2 – runtime: lean image with installed packages + source
# ---------------------------------------------------------------------------
FROM python:3.12-slim AS runtime

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Copy the virtual environment from the builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy application source
WORKDIR /app
COPY src/ src/

# Non-root user for security
RUN useradd --create-home appuser
USER appuser

EXPOSE 8080

CMD ["uvicorn", "aimart.main:app", "--host", "0.0.0.0", "--port", "8080"]
