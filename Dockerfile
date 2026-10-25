# ==============================================================================
# Failed Build Detective - Production Dockerfile
# Base Image: Python 3.10 Slim
# ==============================================================================
FROM python:3.10-slim

# Build-time argument to simulate failures during build or runtime
ARG SIMULATE_FAILURE=none

# Configure Python runtime behavior for containerized environments
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    SIMULATE_FAILURE=${SIMULATE_FAILURE}

# Set container working directory
WORKDIR /app

# Install application and test dependencies with layer caching
COPY app/requirements.txt ./app/requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r app/requirements.txt

# Copy application source code and test suite
COPY app/ ./app/
COPY tests/ ./tests/

# Default execution: run verbose pytest suite across tests directory
CMD ["pytest", "tests/", "-v"]
