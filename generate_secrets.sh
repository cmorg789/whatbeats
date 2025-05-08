#!/bin/bash
# generate_secrets.sh
# This script generates secure secrets for the WhatBeats application
# It creates or updates:
# 1. A random JWT secret key
# 2. A bcrypt hash of the admin password
# 3. A secure storage for the LLM API key

# Parse command line arguments
FORCE_RESET=false
while getopts "f" opt; do
  case $opt in
    f) FORCE_RESET=true ;;
    *) echo "Usage: $0 [-f]" >&2
       echo "  -f  Force reset of all secrets even if they exist" >&2
       exit 1 ;;
  esac
done

echo "Setting up secure secrets for WhatBeats..."

# Create or update .env file
if [ ! -f ".env" ]; then
    # If .env doesn't exist, create it from .env.example
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo "Created .env file from .env.example"
    else
        # If .env.example doesn't exist, create an empty .env file
        touch .env
        echo "Created empty .env file"
    fi
else
    echo "Using existing .env file"
    # Create a backup of the existing .env file
    cp .env .env.backup
    echo "Created backup of existing .env file as .env.backup"
fi

# Function to check if a secret exists and has a non-empty value in .env
secret_exists() {
    # Check if the key exists and has a non-empty value
    grep -q "^$1=.\+" .env
    return $?
}

# Function to update a secret in .env
update_secret() {
    local key=$1
    local value=$2
    
    if grep -q "^$key=" .env; then
        # Secret exists, update it in place
        sed -i.bak "s|^$key=.*|$key=$value|" .env
        rm -f .env.bak
    else
        # Secret doesn't exist, append it
        echo "$key=$value" >> .env
    fi
}

# Generate and update JWT secret key if needed
if $FORCE_RESET || ! secret_exists "JWT_SECRET_KEY"; then
    echo "Generating JWT secret key..."
    JWT_SECRET_KEY=$(openssl rand -base64 32)
    update_secret "JWT_SECRET_KEY" "$JWT_SECRET_KEY"
    echo "JWT secret key updated"
else
    echo "JWT secret key already exists with a value (use -f to force reset)"
fi

# Generate and update admin password hash if needed
if $FORCE_RESET || ! secret_exists "ADMIN_PASSWORD_HASH"; then
    echo "Generating admin password hash..."
    read -sp "Enter admin password: " ADMIN_PASSWORD
    echo
    if [ -z "$ADMIN_PASSWORD" ]; then
        echo "Error: Password cannot be empty"
        exit 1
    fi
    
    # This requires bcrypt to be installed: pip install bcrypt
    ADMIN_PASSWORD_HASH=$(python -c "import bcrypt; print(bcrypt.hashpw('$ADMIN_PASSWORD'.encode(), bcrypt.gensalt()).decode())")
    update_secret "ADMIN_PASSWORD_HASH" "$ADMIN_PASSWORD_HASH"
    echo "Admin password hash updated"
else
    echo "Admin password hash already exists with a value (use -f to force reset)"
fi

# Store LLM API key if needed
if $FORCE_RESET || ! secret_exists "LLM_API_KEY"; then
    echo "Storing LLM API key..."
    read -sp "Enter LLM API key: " LLM_API_KEY
    echo
    if [ -z "$LLM_API_KEY" ]; then
        echo "Error: LLM API key cannot be empty"
        exit 1
    fi
    update_secret "LLM_API_KEY" "$LLM_API_KEY"
    echo "LLM API key updated"
else
    echo "LLM API key already exists with a value (use -f to force reset)"
fi

echo "Secret setup completed successfully!"
echo "All secrets have been stored in .env"
echo
echo "IMPORTANT: Add .env to your .gitignore file to prevent committing secrets to version control."
echo
echo "To reset all secrets in the future, run: ./generate_secrets.sh -f"