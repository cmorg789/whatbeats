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
   - Build and start the WhatBeats application container
   - Create a dedicated Docker network for secure communication between containers
   - Make the application available at:
     - Frontend: http://localhost:3000
     - Backend API: http://localhost:8000
     - API Documentation: http://localhost:8000/docs

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

# Run the WhatBeats application
docker run -d \
  --name whatbeats-app \
  --network whatbeats-network \
  -p 8000:8000 \
  -p 3000:3000 \
  -e MONGODB_URI=mongodb://whatbeats-mongodb:27017 \
  -e MONGODB_DB=whatbeats \
  -v $(pwd)/.env:/app/.env:ro \
  whatbeats
```

## Environment Variables

The following environment variables can be set in the `.env` file or passed directly to the container:

- `MONGODB_URI`: MongoDB connection URI (default: mongodb://localhost:27017)
- `MONGODB_DB`: MongoDB database name (default: whatbeats)
- `JWT_SECRET_KEY`: Secret key for JWT token generation
- `ADMIN_PASSWORD_HASH`: Bcrypt hash of the admin password
- `LLM_API_KEY`: API key for the LLM service

See `.env.example` for a complete list of available environment variables.

## Container Architecture

The WhatBeats Docker setup uses a multi-container architecture:

1. **MongoDB Container**: A dedicated container running MongoDB 6.0 for data storage
2. **WhatBeats Application Container**: Contains both the backend and frontend components

These containers communicate through a dedicated Docker network named `whatbeats-network`, which provides:
- Isolation from other Docker containers on the host
- Secure communication between the application and database
- Service discovery (containers can reference each other by name)

## Data Persistence

MongoDB data is persisted in a Docker volume named `whatbeats-mongodb-data`. This ensures your data is preserved even if the containers are removed.

## Troubleshooting

### Container fails to start

Check the container logs:

```bash
docker logs whatbeats
```

### MongoDB connection issues

Make sure the MongoDB container is running:

```bash
docker ps | grep mongodb
```

If it's not running, check its logs:

```bash
docker logs whatbeats-mongodb