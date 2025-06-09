# Task Timr - Docker Container
# Task duration-focused alternative frontend to Timr.com
#
# Copyright (c) 2025 Ohrner IT GmbH
# Licensed under the MIT License

FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive

# Create application user
RUN groupadd --gid 1000 task-timr && \
    useradd --uid 1000 --gid task-timr --shell /bin/bash --create-home task-timr

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        curl \
        git && \
    rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml ./
COPY package.json package-lock.json ./

# Install Node.js for frontend testing (optional)
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs && \
    npm ci

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -e .

# Copy application code
COPY . .

# Create logs directory
RUN mkdir -p logs && \
    chown -R task-timr:task-timr /app

# Switch to non-root user
USER task-timr

# Set default environment variables
ENV FLASK_ENV=production \
    BIND_IP=0.0.0.0 \
    PORT=5000

# Health check - use environment variable for port
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

# Expose port
EXPOSE ${PORT}

# Start application with configurable bind address
CMD sh -c "gunicorn --bind ${BIND_IP}:${PORT} --workers 4 --timeout 120 --keep-alive 5 --max-requests 1000 --max-requests-jitter 100 --preload --access-logfile logs/access.log --error-logfile logs/error.log main:app"