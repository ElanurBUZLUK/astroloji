# Multi-stage build for production optimization
FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    wget \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Create Swiss Ephemeris directory
RUN mkdir -p /usr/share/swisseph

WORKDIR /app

# Development stage
FROM base as development

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install development dependencies
RUN pip install --no-cache-dir pytest pytest-asyncio pytest-cov black isort flake8

# Copy application code
COPY . .

# Copy Swiss Ephemeris files if they exist (development)
RUN if [ -d "swisseph" ] && [ "$(ls -A swisseph 2>/dev/null)" ]; then \
        cp swisseph/*.se1 /usr/share/swisseph/ 2>/dev/null || true; \
    fi

# Create non-root user
RUN groupadd -r astro && useradd -r -g astro astro
RUN chown -R astro:astro /app
USER astro

# Expose port
EXPOSE 8000

# Run the application in development mode
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# Production stage
FROM base as production

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Copy Swiss Ephemeris files if they exist (production)
RUN if [ -d "swisseph" ] && [ "$(ls -A swisseph 2>/dev/null)" ]; then \
        cp swisseph/*.se1 /usr/share/swisseph/ 2>/dev/null || true; \
    fi

# Create non-root user
RUN groupadd -r astro && useradd -r -g astro astro

# Create necessary directories
RUN mkdir -p /app/logs && chown -R astro:astro /app

# Switch to non-root user
USER astro

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]