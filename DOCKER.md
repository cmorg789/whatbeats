# Docker Setup for WhatBeats

This document provides instructions for running the WhatBeats application using Docker.

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/)
- [Docker Compose](https://docs.docker.com/compose/install/)

## Quick Start

1. **Set up environment variables**

   Before running the application, you need to set up the required environment variables. If you don't have a `.env` file yet, create one from the example:

   ```bash
   cp .env.example .env
   ```

   Then run the script to generate the required secrets:

   ```bash
   ./generate_secrets.sh
   ```

2. **Build and run with Docker Compose**

   ```bash
   docker-compose up -d
   ```

   This will:
   - Start a MongoDB container
   - Build and start the WhatBeats backend container
   - Build and start the WhatBeats frontend container
   - Build and start the Nginx reverse proxy container
   - Create a dedicated Docker network for secure communication between containers
   - Make the application available at:
     - Application: http://localhost:80 (or http://localhost)
     - Admin interface: http://localhost/admin

3. **View logs**

   ```bash
   docker-compose logs -f
   ```

4. **Stop the application**

   ```bash
   docker-compose down
   ```

## Building the Docker Image Manually

If you want to build the Docker image manually:

```bash
docker build -t whatbeats -f Dockerfile ..
```

## Running the Container Manually

To run the container manually (without Docker Compose):

```bash
# Create a dedicated network
docker network create whatbeats-network

# Start MongoDB container
docker run -d \
  --name whatbeats-mongodb \
  --network whatbeats-network \
  -p 27017:27017 \
  -v whatbeats-mongodb-data:/data/db \
  mongo:6.0

# Run the WhatBeats backend
docker run -d \
  --name whatbeats-backend \
  --network whatbeats-network \
  -e MONGODB_URI=mongodb://whatbeats-mongodb:27017 \
  -e MONGODB_DB=whatbeats \
  -v $(pwd)/.env:/app/.env:ro \
  whatbeats:backend

# Run the WhatBeats frontend
docker run -d \
  --name whatbeats-frontend \
  --network whatbeats-network \
  -v $(pwd)/.env:/app/.env:ro \
  whatbeats:frontend

# Run the Nginx reverse proxy
docker run -d \
  --name whatbeats-nginx \
  --network whatbeats-network \
  -p 80:80 \
  -p 443:443 \
  -e DOMAIN=localhost \
  -e ENABLE_SSL=false \
  -e SSL_EMAIL=your-email@example.com \
  -v whatbeats-letsencrypt-certs:/etc/letsencrypt \
  -v whatbeats-letsencrypt-challenges:/var/www/certbot \
  whatbeats:nginx
```

For SSL in production, you would set:
```bash
-e DOMAIN=your-domain.com \
-e ENABLE_SSL=true \
-e SSL_EMAIL=your-email@example.com \
```

## Environment Variables

The following environment variables can be set in the `.env` file or passed directly to the container:

- `MONGODB_URI`: MongoDB connection URI (default: mongodb://localhost:27017)
- `MONGODB_DB`: MongoDB database name (default: whatbeats)
- `JWT_SECRET_KEY`: Secret key for JWT token generation
- `ADMIN_PASSWORD_HASH`: Bcrypt hash of the admin password
- `LLM_API_KEY`: API key for the LLM service
- `DOMAIN`: Domain name for the application (default: localhost)
- `ENABLE_SSL`: Enable Let's Encrypt SSL certificate generation (default: false)
- `SSL_EMAIL`: Email address for Let's Encrypt registration and recovery (required when ENABLE_SSL=true)

See `.env.example` for a complete list of available environment variables.

## SSL Configuration

WhatBeats supports automatic SSL certificate generation using Let's Encrypt. To enable SSL:

1. Set `ENABLE_SSL=true` in your `.env` file
2. Set `SSL_EMAIL=your-email@example.com` in your `.env` file (required for Let's Encrypt registration)
3. Set `DOMAIN=your-domain.com` to your actual domain name (must be publicly accessible)

When SSL is enabled:
- The application will automatically obtain and configure SSL certificates
- HTTP traffic will be redirected to HTTPS
- Certificates will be automatically renewed before expiration

Example configuration:
```
DOMAIN=whatbeats.example.com
ENABLE_SSL=true
SSL_EMAIL=admin@example.com
```

Note: For SSL to work properly, your server must:
- Have a public domain name pointing to your server's IP address
- Have ports 80 and 443 accessible from the internet
- Not have any other services using ports 80 or 443

## Container Architecture

The WhatBeats Docker setup uses a multi-container architecture:

1. **Nginx Container**: A reverse proxy that handles routing and CORS for all requests
2. **Backend Container**: The FastAPI backend service
3. **Frontend Container**: The Node.js frontend service
4. **MongoDB Container**: A dedicated container running MongoDB for data storage

These containers communicate through a dedicated Docker network named `whatbeats-network`, which provides:
- Isolation from other Docker containers on the host
- Secure communication between all services
- Service discovery (containers can reference each other by name)

### Nginx Reverse Proxy

The Nginx reverse proxy provides several benefits:
- Single entry point for all requests (port 80)
- Handles CORS headers for all requests
- Routes API requests to the backend service
- Routes frontend requests to the frontend service
- Improves security by not exposing backend services directly

## Data Persistence

MongoDB data is persisted in a Docker volume named `whatbeats-mongodb-data`. This ensures your data is preserved even if the containers are removed.

## Troubleshooting

### Container fails to start

Check the container logs:

```bash
docker logs whatbeats-nginx
docker logs whatbeats-backend
docker logs whatbeats-frontend
```

### MongoDB connection issues

Make sure the MongoDB container is running:

```bash
docker ps | grep mongodb
```

If it's not running, check its logs:

```bash
docker logs whatbeats-mongodb