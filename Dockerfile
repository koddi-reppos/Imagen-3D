# Multi-stage Docker build for production
FROM python:3.11-slim as builder

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies into a virtual environment
RUN python -m venv /app/venv
ENV PATH="/app/venv/bin:$PATH"
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Production stage
FROM python:3.11-slim

# Install curl for healthcheck
RUN apt-get update && apt-get install -y curl && \
    rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy virtual environment from builder stage
COPY --from=builder /app/venv /app/venv

# Copy application code
COPY src/ src/
COPY data/ data/

# Create non-root user
RUN useradd --create-home --shell /bin/bash appuser && \
    chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# Set environment variables
ENV PYTHONPATH=/app
ENV PATH="/app/venv/bin:$PATH"

# Start application using Python module approach to avoid permission issues
CMD ["python", "-m", "uvicorn", "src.backend.app.main:app", "--host", "0.0.0.0", "--port", "5000"]
