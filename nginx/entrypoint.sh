#!/bin/bash
set -e

# Function to generate SSL certificate using Let's Encrypt
generate_ssl_certificate() {
    echo "Generating Let's Encrypt SSL certificate for domain: $DOMAIN"
    
    # Check if SSL_EMAIL is provided
    if [ -z "$SSL_EMAIL" ]; then
        echo "ERROR: SSL_EMAIL environment variable is required for Let's Encrypt registration"
        exit 1
    fi
    
    # Check if certificates already exist
    if [ -d "/etc/letsencrypt/live/$DOMAIN" ]; then
        echo "SSL certificates already exist for $DOMAIN"
    else
        echo "Requesting new SSL certificate from Let's Encrypt..."
        certbot certonly --standalone \
            --preferred-challenges http \
            --agree-tos \
            --non-interactive \
            --email "$SSL_EMAIL" \
            -d "$DOMAIN" \
            --keep-until-expiring
        
        echo "SSL certificate successfully obtained!"
    fi
}

# Function to generate DH parameters if they don't exist
generate_dhparam() {
    if [ ! -f "/etc/nginx/dhparam.pem" ]; then
        echo "Generating DH parameters (2048 bit), this might take a moment..."
        openssl dhparam -out /etc/nginx/dhparam.pem 2048
        echo "DH parameters generated successfully!"
    else
        echo "DH parameters already exist"
    fi
}

# Main logic
echo "Preparing Nginx configuration..."
NGINX_CONF_FILE="/etc/nginx/nginx.conf"
NGINX_TEMPLATE="/etc/nginx/nginx.conf.template"

# Create directories for snippets if they don't exist
mkdir -p /etc/nginx/snippets

# Copy snippet files to the correct location
# First, ensure security_headers.conf exists in the target directory
cp /nginx/snippets/security_headers.conf /etc/nginx/snippets/ 2>/dev/null || echo "Warning: Could not copy security_headers.conf"

if [ "$ENABLE_SSL" = "true" ]; then
    echo "SSL is enabled. Setting up HTTPS configuration..."
    
    # Check if DOMAIN is set
    if [ -z "$DOMAIN" ]; then
        echo "ERROR: DOMAIN environment variable is required when ENABLE_SSL=true"
        exit 1
    fi
    
    # Generate SSL certificate
    generate_ssl_certificate
    
    # Generate DH parameters
    generate_dhparam
    
    # Set up auto-renewal cron job
    echo "Setting up certificate auto-renewal..."
    echo "0 0,12 * * * certbot renew --quiet" > /etc/crontabs/root
    crond
    
    # Use HTTP redirect template for HTTP server
    export HTTP_SERVER_CONTENT=$(cat /etc/nginx/http_redirect.template)
    
    # Include HTTPS server block
    export HTTPS_SERVER_BLOCK=$(cat /etc/nginx/https_server.template)
else
    echo "SSL is disabled. Using HTTP configuration only."
    
    # Use HTTP server content template
    export HTTP_SERVER_CONTENT=$(cat /etc/nginx/http_server_content.template)
    
    # Empty HTTPS server block
    export HTTPS_SERVER_BLOCK=""
fi

# Process the template and generate the final nginx.conf
echo "Generating final Nginx configuration..."
envsubst '${DOMAIN} ${HTTP_SERVER_CONTENT} ${HTTPS_SERVER_BLOCK}' < $NGINX_TEMPLATE > $NGINX_CONF_FILE

# Test the configuration
echo "Testing Nginx configuration..."
nginx -t

# Start Nginx
echo "Starting Nginx..."
exec nginx -g "daemon off;"