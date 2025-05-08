FROM nginx:1.25-alpine

# Install dependencies for certbot
RUN apk add --no-cache certbot certbot-nginx bash openssl

# Remove default Nginx config
RUN rm /etc/nginx/conf.d/default.conf

# Create directories for templates and snippets
RUN mkdir -p /etc/nginx/templates /etc/nginx/snippets

# Copy our custom Nginx config templates
COPY nginx/nginx.conf.template /etc/nginx/nginx.conf.template
COPY nginx/http_server_content.template /etc/nginx/http_server_content.template
COPY nginx/http_redirect.template /etc/nginx/http_redirect.template
COPY nginx/https_server.template /etc/nginx/https_server.template

# Create snippet files directory if it doesn't exist and copy files
RUN mkdir -p /tmp/nginx/snippets

# Create proxy_params.conf if it doesn't exist
RUN echo '# Common proxy parameters for all proxy_pass directives\n\nproxy_http_version 1.1;\nproxy_set_header Upgrade $http_upgrade;\nproxy_set_header Connection '"'"'upgrade'"'"';\nproxy_set_header Host $host;\nproxy_set_header X-Real-IP $remote_addr;\nproxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;\nproxy_set_header X-Forwarded-Proto $scheme;\nproxy_cache_bypass $http_upgrade;' > /tmp/nginx/snippets/proxy_params.conf

# Create ssl_params.conf if it doesn't exist
RUN echo '# Modern SSL configuration for enhanced security\n\n# SSL protocols and ciphers\nssl_protocols TLSv1.2 TLSv1.3;\nssl_prefer_server_ciphers off;\nssl_ciphers "ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:DHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES256-GCM-SHA384";\n\n# SSL session settings\nssl_session_cache shared:SSL:10m;\nssl_session_timeout 1h;\nssl_session_tickets off;\n\n# OCSP Stapling\nssl_stapling on;\nssl_stapling_verify on;\nresolver 8.8.8.8 8.8.4.4 valid=300s;\nresolver_timeout 5s;\n\n# Diffie-Hellman parameters\nssl_dhparam /etc/nginx/dhparam.pem;' > /tmp/nginx/snippets/ssl_params.conf

# Create cors_headers.conf if it doesn't exist
RUN echo '# CORS configuration with more restrictive approach\n\n# CORS headers with dynamic origin (variable defined in http context)\nadd_header '"'"'Access-Control-Allow-Origin'"'"' $cors_allow_origin always;\nadd_header '"'"'Access-Control-Allow-Methods'"'"' '"'"'GET, POST, OPTIONS, PUT, DELETE'"'"' always;\nadd_header '"'"'Access-Control-Allow-Headers'"'"' '"'"'Origin, X-Requested-With, Content-Type, Accept, Authorization'"'"' always;\nadd_header '"'"'Access-Control-Allow-Credentials'"'"' '"'"'true'"'"' always;\nadd_header '"'"'Access-Control-Max-Age'"'"' '"'"'86400'"'"' always;\nadd_header '"'"'Vary'"'"' '"'"'Origin'"'"' always;\n\n# Direct handling of OPTIONS requests\nif ($request_method = '"'"'OPTIONS'"'"') {\n    add_header '"'"'Access-Control-Allow-Origin'"'"' $cors_allow_origin;\n    add_header '"'"'Access-Control-Allow-Methods'"'"' '"'"'GET, POST, OPTIONS, PUT, DELETE'"'"';\n    add_header '"'"'Access-Control-Allow-Headers'"'"' '"'"'Origin, X-Requested-With, Content-Type, Accept, Authorization'"'"';\n    add_header '"'"'Access-Control-Allow-Credentials'"'"' '"'"'true'"'"';\n    add_header '"'"'Access-Control-Max-Age'"'"' '"'"'86400'"'"';\n    add_header '"'"'Content-Type'"'"' '"'"'text/plain charset=UTF-8'"'"';\n    add_header '"'"'Content-Length'"'"' '"'"'0'"'"';\n    add_header '"'"'Vary'"'"' '"'"'Origin'"'"';\n    return 204;\n}' > /tmp/nginx/snippets/cors_headers.conf

# First copy our default generated snippets to ensure we have them
RUN cp /tmp/nginx/snippets/proxy_params.conf /etc/nginx/snippets/ && \
    cp /tmp/nginx/snippets/ssl_params.conf /etc/nginx/snippets/ && \
    cp /tmp/nginx/snippets/cors_headers.conf /etc/nginx/snippets/

# Now try to copy user-provided snippets (if they exist, they will overwrite the defaults)
# We'll use a shell script to handle this properly
RUN mkdir -p /tmp/copy_snippets && \
    echo '#!/bin/sh' > /tmp/copy_snippets/copy.sh && \
    echo 'cp -f /nginx/snippets/proxy_params.conf /etc/nginx/snippets/ 2>/dev/null || true' >> /tmp/copy_snippets/copy.sh && \
    echo 'cp -f /nginx/snippets/ssl_params.conf /etc/nginx/snippets/ 2>/dev/null || true' >> /tmp/copy_snippets/copy.sh && \
    echo 'cp -f /nginx/snippets/cors_headers.conf /etc/nginx/snippets/ 2>/dev/null || true' >> /tmp/copy_snippets/copy.sh && \
    chmod +x /tmp/copy_snippets/copy.sh

# Copy the nginx/snippets directory to a temporary location
COPY nginx /nginx

# Run the copy script
RUN /tmp/copy_snippets/copy.sh

# Create directories for Let's Encrypt
RUN mkdir -p /etc/letsencrypt /var/www/certbot

# Copy the entrypoint script
COPY nginx/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Expose ports
EXPOSE 80
EXPOSE 443

# Use our custom entrypoint script
ENTRYPOINT ["/entrypoint.sh"]