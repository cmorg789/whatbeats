#!/bin/bash
set -e

# Main logic
echo "Preparing Traefik configuration..."

# Create dynamic configuration directory if it doesn't exist
mkdir -p /etc/traefik/dynamic

# Create base dynamic configuration
cat > /etc/traefik/dynamic/base.yml << EOF
http:
  middlewares:
    securityHeaders:
      headers:
        frameDeny: true
        sslRedirect: true
        browserXssFilter: true
        contentTypeNosniff: true
        forceSTSHeader: true
        stsIncludeSubdomains: true
        stsPreload: true
        stsSeconds: 31536000
        customFrameOptionsValue: "SAMEORIGIN"
        
  routers:
    frontend:
      rule: "Host(\`${DOMAIN}\`)"
      entrypoints:
        - web
      service: frontend
    backend:
      rule: "Host(\`${DOMAIN}\`) && PathPrefix(\`/api/\`)"
      entrypoints:
        - web
      service: backend
      
  services:
    frontend:
      loadBalancer:
        servers:
          - url: "http://frontend:3000"
    backend:
      loadBalancer:
        servers:
          - url: "http://backend:8000"
EOF

# Check if SSL is enabled
if [ "${ENABLE_SSL}" = "true" ]; then
  echo "SSL is enabled. Configuring HTTPS redirection..."
  
  # Create SSL configuration
  cat > /etc/traefik/dynamic/ssl.yml << EOF
http:
  middlewares:
    redirect-to-https:
      redirectScheme:
        scheme: https
        permanent: true
        
  routers:
    # HTTP routers with redirect middleware
    frontend:
      rule: "Host(\`${DOMAIN}\`)"
      entrypoints:
        - web
      middlewares:
        - redirect-to-https
      service: frontend
    backend:
      rule: "Host(\`${DOMAIN}\`) && PathPrefix(\`/api/\`)"
      entrypoints:
        - web
      middlewares:
        - redirect-to-https
      service: backend
      
    # HTTPS secure routers
    frontend-secure:
      rule: "Host(\`${DOMAIN}\`)"
      entrypoints:
        - websecure
      service: frontend
      tls:
        certResolver: letsencrypt
    backend-secure:
      rule: "Host(\`${DOMAIN}\`) && PathPrefix(\`/api/\`)"
      entrypoints:
        - websecure
      service: backend
      tls:
        certResolver: letsencrypt
      
  services:
    frontend:
      loadBalancer:
        servers:
          - url: "http://frontend:3000"
    backend:
      loadBalancer:
        servers:
          - url: "http://backend:8000"
EOF

  echo "SSL configuration created."
else
  echo "SSL is disabled. Using HTTP only."
  
  # Create configuration for HTTP-only mode
  cat > /etc/traefik/dynamic/ssl.yml << EOF
http:
  routers:
    frontend:
      rule: "Host(\`${DOMAIN}\`)"
      entrypoints:
        - web
      service: frontend
    backend:
      rule: "Host(\`${DOMAIN}\`) && PathPrefix(\`/api/\`)"
      entrypoints:
        - web
      service: backend
      
  services:
    frontend:
      loadBalancer:
        servers:
          - url: "http://frontend:3000"
    backend:
      loadBalancer:
        servers:
          - url: "http://backend:8000"
EOF
fi

# Create middleware configuration for security headers
cat > /etc/traefik/dynamic/middlewares.yml << EOF
http:
  middlewares:
    securityHeaders:
      headers:
        frameDeny: true
        browserXssFilter: true
        contentTypeNosniff: true
        customFrameOptionsValue: "SAMEORIGIN"
        referrerPolicy: "same-origin"
        permissionsPolicy: "camera=(), microphone=(), geolocation=(), interest-cohort=()"
EOF

echo "Traefik configuration completed."

# Start Traefik
echo "Starting Traefik..."

# Debug: Print environment variables
echo "DEBUG: Environment variables:"
echo "DOMAIN: ${DOMAIN}"
echo "ENABLE_SSL: ${ENABLE_SSL}"
echo "SSL_EMAIL: '${SSL_EMAIL}'"

# Debug: List dynamic configuration files
echo "DEBUG: Dynamic configuration files:"
ls -la /etc/traefik/dynamic/

# Debug: Print content of dynamic configuration files
echo "DEBUG: Content of base.yml:"
cat /etc/traefik/dynamic/base.yml
echo "DEBUG: Content of ssl.yml:"
cat /etc/traefik/dynamic/ssl.yml
echo "DEBUG: Content of middlewares.yml:"
cat /etc/traefik/dynamic/middlewares.yml

# Start Traefik
exec traefik