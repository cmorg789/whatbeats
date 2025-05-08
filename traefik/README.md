# Traefik Configuration for WhatBeats

This directory contains the Traefik configuration files for the WhatBeats application. Traefik is used as a reverse proxy to route traffic to the frontend and backend services.

## Files

- `Dockerfile`: Builds the Traefik container with the necessary configuration
- `entrypoint.sh`: Script that runs when the container starts, configuring Traefik based on environment variables
- `traefik.yml`: Static configuration for Traefik

## Configuration

Traefik is configured to:

1. Route traffic to the frontend and backend services
2. Handle SSL/TLS with Let's Encrypt (when enabled)
3. Apply security headers
4. Redirect HTTP to HTTPS (when SSL is enabled)

## Environment Variables

The following environment variables are used to configure Traefik:

- `DOMAIN`: The domain name for the application (default: localhost)
- `ENABLE_SSL`: Whether to enable SSL/TLS (default: false)
- `SSL_EMAIL`: Email address for Let's Encrypt registration

## SSL/TLS

When `ENABLE_SSL` is set to `true`, Traefik will:

1. Obtain SSL certificates from Let's Encrypt
2. Redirect HTTP traffic to HTTPS
3. Apply strict security headers

## Usage

Traefik is configured in the docker-compose.yml file and will start automatically when the application is started.

```bash
# Start the application with docker-compose
docker-compose up -d
```

## Dashboard

The Traefik dashboard is disabled by default for security reasons. To enable it, modify the `traefik.yml` file to set `api.insecure: true`.