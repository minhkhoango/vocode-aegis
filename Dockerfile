# Dockerfile

# Stage 1: Build React frontend
FROM node:18-alpine AS frontend-builder
WORKDIR /frontend
COPY frontend/package*.json ./
# Use `npm ci` for clean installs in CI/CD environments
RUN npm ci --only=production
COPY frontend/ ./
RUN npm run build

# Stage 2: Python backend with built frontend
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies required for build and runtime
# curl is used by the healthcheck
RUN apt-get update && apt-get install -y \
    curl \
    ca-certificates \
    --no-install-recommends \
    && rm -rf /var/lib/apt/lists/* \
    && update-ca-certificates

# Copy requirements first for better caching
COPY backend/requirements.txt .

# Install Python dependencies with simple, reliable approach
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend/ ./

# Copy built frontend from previous stage into the static directory of the backend
COPY --from=frontend-builder /frontend/build ./static

# Create non-root user for security
# Running as non-root is a best practice for production containers
RUN adduser --disabled-password --gecos '' appuser && \
    chown -R appuser:appuser /app

USER appuser

# Health check for the FastAPI application
# Ensures the container is truly ready to serve traffic
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Expose port on which FastAPI will run
EXPOSE 8000

# Start application using uvicorn
# The --reload flag should be removed for production deployments
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]