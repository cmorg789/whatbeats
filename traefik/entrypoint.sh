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
    frontend:
      middlewares:
        - redirect-to-https
    backend:
      middlewares:
        - redirect-to-https
EOF

  echo "SSL configuration created."
else
  echo "SSL is disabled. Using HTTP only."
  
  # Create empty SSL configuration to avoid errors
  cat > /etc/traefik/dynamic/ssl.yml << EOF
# SSL disabled - no redirects configured
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
exec traefik