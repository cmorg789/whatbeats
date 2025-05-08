FROM traefik:3.4

# Install bash for the entrypoint script
RUN apk add --no-cache bash

# Create necessary directories
RUN mkdir -p /etc/traefik/dynamic /var/log/traefik /etc/traefik/acme

# Copy configuration files
COPY traefik/traefik.yml /etc/traefik/traefik.yml

# Copy the entrypoint script
COPY traefik/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Expose ports
EXPOSE 80
EXPOSE 443

# Use our custom entrypoint script
ENTRYPOINT ["/entrypoint.sh"]