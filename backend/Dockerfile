# Use Python 3.12 slim base image for minimal size
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies for Poetry and application
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
ENV POETRY_VERSION=1.8.3
RUN pip install --no-cache-dir poetry==${POETRY_VERSION}

# Copy Poetry files for dependency installation
COPY backend/pyproject.toml backend/poetry.lock ./

# Install dependencies with Poetry
# --no-dev excludes dev dependencies (e.g., pytest)
# --no-root avoids installing the project itself (we'll copy code later)
RUN poetry config virtualenvs.create false \
    && poetry install --no-dev --no-interaction --no-ansi

# Copy application code
COPY . .

# Expose API port
EXPOSE 8000

# Healthcheck to monitor application
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run Uvicorn with production settings
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]