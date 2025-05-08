# Use multi-stage build for smaller final image
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

# Final stage
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install Node.js and npm
RUN apt-get update && \
    apt-get install -y curl gnupg && \
    mkdir -p /etc/apt/keyrings && \
    curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key | gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg && \
    echo "deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_20.x nodistro main" | tee /etc/apt/sources.list.d/nodesource.list && \
    apt-get update && \
    apt-get install -y nodejs && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copy installed dependencies from builder stages
COPY --from=python-deps /usr/local/lib/python3.9/site-packages /usr/local/lib/python3.9/site-packages
COPY --from=node-deps /app/frontend/node_modules /app/frontend/node_modules

# Copy the application
COPY whatbeats/ .

# Create a script to start both servers
RUN echo '#!/bin/bash\n\
# Check if .env file exists, if not, run generate_secrets.sh\n\
if [ ! -f ".env" ] || \\\n\
   ! grep -q "JWT_SECRET_KEY=.\\+" .env || \\\n\
   ! grep -q "ADMIN_PASSWORD_HASH=.\\+" .env || \\\n\
   ! grep -q "LLM_API_KEY=.\\+" .env; then\n\
    echo "Required secrets not found or have empty values in .env file."\n\
    echo "Please mount a valid .env file or provide environment variables."\n\
    exit 1\n\
fi\n\
\n\
# Start the backend server\n\
cd /app/backend\n\
python run.py &\n\
BACKEND_PID=$!\n\
echo "Backend server started with PID: $BACKEND_PID"\n\
\n\
# Wait for backend to initialize\n\
sleep 3\n\
\n\
# Start the frontend server\n\
cd /app/frontend\n\
node server.js &\n\
FRONTEND_PID=$!\n\
echo "Frontend server started with PID: $FRONTEND_PID"\n\
\n\
echo "Application is now running!"\n\
echo "- Frontend: http://localhost:3000"\n\
echo "- Backend API: http://localhost:8000"\n\
\n\
# Wait for any process to exit\n\
wait -n\n\
\n\
# Exit with status of process that exited first\n\
exit $?\n\
' > /app/docker-entrypoint.sh

# Make the entrypoint script executable
RUN chmod +x /app/docker-entrypoint.sh

# Expose ports for backend and frontend
EXPOSE 8000 3000

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

# Set the entrypoint
ENTRYPOINT ["/app/docker-entrypoint.sh"]

# Set the entrypoint
ENTRYPOINT ["/app/docker-entrypoint.sh"]