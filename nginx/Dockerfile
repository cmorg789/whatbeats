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

# Copy snippet files
COPY nginx/snippets/ /etc/nginx/snippets/

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