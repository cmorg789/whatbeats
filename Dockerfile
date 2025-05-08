# Use multi-stage build for smaller final images
FROM python:3.9-slim AS python-deps

# Set working directory
WORKDIR /app

# Copy requirements.txt and install Python dependencies
COPY whatbeats/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Node.js dependencies stage
FROM node:20-slim AS node-deps

# Set working directory
WORKDIR /app

# Copy package.json and install Node.js dependencies
COPY whatbeats/frontend/package.json whatbeats/frontend/package-lock.json ./frontend/
RUN cd frontend && npm ci --only=production

# Backend stage
FROM python:3.9-slim AS backend-stage

# Set working directory
WORKDIR /app

# Copy installed dependencies from builder stage
COPY --from=python-deps /usr/local/lib/python3.9/site-packages /usr/local/lib/python3.9/site-packages

# Copy the backend application
COPY whatbeats/backend ./backend
COPY whatbeats/requirements.txt .

# Set environment variables
ENV LLM_API_URL=https://openrouter.ai/api/v1/chat/completions \
    LLM_MODEL=meta-llama/llama-4-maverick:free \
    LLM_LOGGING_ENABLED=true \
    LLM_LOG_LEVEL=INFO \
    LLM_LOG_DIR=logs \
    LLM_LOG_FILE=llm_responses.log \
    ADMIN_USERNAME=admin \
    JWT_ALGORITHM=HS256 \
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30 \
    RATE_LIMIT_ENABLED=true \
    RATE_LIMIT_REQUESTS=10 \
    RATE_LIMIT_PERIOD=60

# Expose backend port
EXPOSE 8000

# Default command
CMD ["python", "/app/backend/run.py"]

# Frontend stage
FROM node:20-slim AS frontend-stage

# Set working directory
WORKDIR /app

# Copy installed dependencies from builder stage
COPY --from=node-deps /app/frontend/node_modules ./frontend/node_modules

# Copy the frontend application
COPY whatbeats/frontend ./frontend

# Expose frontend port
EXPOSE 3000

# Default command
CMD ["node", "/app/frontend/server.js"]