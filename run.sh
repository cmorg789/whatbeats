#!/bin/bash

# What Beats Rock? Application Launcher
# This script starts both the backend and frontend servers

echo "Starting What Beats Rock? Application..."

# Check if MongoDB is running
echo "Checking MongoDB status..."
if command -v mongod &> /dev/null; then
    if ! pgrep -x "mongod" > /dev/null; then
        echo "MongoDB is not running. Starting MongoDB..."
        mongod --fork --logpath /tmp/mongodb.log
        if [ $? -ne 0 ]; then
            echo "Failed to start MongoDB. Please start it manually."
            echo "You can typically start MongoDB with: mongod --dbpath /data/db"
            exit 1
        fi
    else
        echo "MongoDB is already running."
    fi
else
    echo "MongoDB command not found. Please ensure MongoDB is installed and running."
    echo "Visit https://www.mongodb.com/docs/manual/installation/ for installation instructions."
fi

# Create and use a virtual environment
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "Failed to create virtual environment. Please check your Python installation."
        echo "You may need to install the venv module: python3 -m pip install --user virtualenv"
        exit 1
    fi
fi

# Activate virtual environment
echo "Activating Python virtual environment..."
source venv/bin/activate 2>/dev/null || source venv/Scripts/activate 2>/dev/null
if [ $? -ne 0 ]; then
    echo "Failed to activate virtual environment."
    exit 1
fi
echo "Virtual environment activated successfully."

# Install dependencies in the virtual environment
if [ -f "requirements.txt" ]; then
    echo "Installing dependencies in virtual environment..."
    pip install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "Warning: Failed to install some dependencies. The application may not work correctly."
    else
        echo "Dependencies installed successfully."
    fi
else
    echo "Warning: requirements.txt not found. Dependencies may be missing."
fi

# Check if secrets are generated and have values
echo "Checking for application secrets..."
if [ ! -f ".env" ] || \
   ! grep -q "JWT_SECRET_KEY=.\+" .env || \
   ! grep -q "ADMIN_PASSWORD_HASH=.\+" .env || \
   ! grep -q "LLM_API_KEY=.\+" .env; then
    echo "Required secrets not found or have empty values in .env file. Running generate_secrets.sh to create them..."
    bash generate_secrets.sh
    if [ $? -ne 0 ]; then
        echo "Failed to generate secrets. Please run generate_secrets.sh manually."
        exit 1
    fi
    echo "Secrets generated successfully."
else
    echo "Required secrets found with values in .env file."
fi

# Start the backend server in a new terminal
echo "Starting backend server..."
# Get the absolute path to the script directory
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR/backend"

# Run the backend using the Python from the virtual environment
python run.py &
BACKEND_PID=$!
echo "Backend server started with PID: $BACKEND_PID"

# Wait for backend to initialize
echo "Waiting for backend to initialize..."
sleep 3

# Start the frontend server in a new terminal
echo "Starting frontend server..."
cd "$SCRIPT_DIR/frontend"

# Install frontend dependencies if package.json exists
if [ -f "package.json" ]; then
    echo "Installing frontend dependencies..."
    npm install
    if [ $? -ne 0 ]; then
        echo "Warning: Failed to install some frontend dependencies. The application may not work correctly."
    else
        echo "Frontend dependencies installed successfully."
    fi
fi

node server.js &
FRONTEND_PID=$!
echo "Frontend server started with PID: $FRONTEND_PID"

# Wait for frontend to initialize
echo "Waiting for frontend to initialize..."
sleep 2

echo "Application is now running!"
echo "- Frontend: http://localhost:3000"
echo "- Backend API: http://localhost:8000"
echo ""
echo "Press Ctrl+C to stop all servers."

# Wait for user to press Ctrl+C
trap "echo 'Stopping servers...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; echo 'Servers stopped.'; exit 0" INT
wait