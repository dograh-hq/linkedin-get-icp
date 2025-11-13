#!/bin/bash

# LinkedIn ICP Server Startup Script
# This script manages the backend server startup with proper process management

set -e  # Exit on error

# Define paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BACKEND_DIR="$PROJECT_ROOT/backend"
VENV_DIR="$BACKEND_DIR/venv"
ENV_FILE="$BACKEND_DIR/.env"
RUN_DIR="$PROJECT_ROOT/run"
PID_FILE="$RUN_DIR/server.pid"
REQUIREMENTS_FILE="$BACKEND_DIR/requirements.txt"

# Color codes for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to print colored messages
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if .env file exists
if [ ! -f "$ENV_FILE" ]; then
    print_error ".env file not found at $ENV_FILE"
    exit 1
fi

# Load SERVER_PORT from .env file
print_info "Loading configuration from .env..."
export $(grep "^SERVER_PORT=" "$ENV_FILE" | xargs)

if [ -z "$SERVER_PORT" ]; then
    print_error "SERVER_PORT not found in .env file"
    exit 1
fi

print_info "Server will start on port: $SERVER_PORT"

# Check if virtual environment exists
if [ ! -d "$VENV_DIR" ]; then
    print_error "Virtual environment not found at $VENV_DIR"
    print_info "Please create a virtual environment first: python3 -m venv $VENV_DIR"
    exit 1
fi

# Kill existing server process if running
if [ -f "$PID_FILE" ]; then
    OLD_PID=$(cat "$PID_FILE")
    if ps -p "$OLD_PID" > /dev/null 2>&1; then
        print_warning "Stopping existing server process (PID: $OLD_PID)..."
        kill "$OLD_PID" 2>/dev/null || true

        # Wait for process to terminate (max 10 seconds)
        for i in {1..10}; do
            if ! ps -p "$OLD_PID" > /dev/null 2>&1; then
                print_info "Previous server stopped successfully"
                break
            fi
            sleep 1
        done

        # Force kill if still running
        if ps -p "$OLD_PID" > /dev/null 2>&1; then
            print_warning "Force killing previous server..."
            kill -9 "$OLD_PID" 2>/dev/null || true
        fi
    else
        print_info "PID file exists but process is not running"
    fi
    rm -f "$PID_FILE"
fi

# Activate virtual environment
print_info "Activating virtual environment..."
source "$VENV_DIR/bin/activate"

# Install/update requirements
if [ -f "$REQUIREMENTS_FILE" ]; then
    print_info "Installing/updating dependencies from requirements.txt..."
    pip install -q --upgrade pip
    pip install -q -r "$REQUIREMENTS_FILE"
else
    print_warning "requirements.txt not found at $REQUIREMENTS_FILE"
fi

# Change to backend directory
cd "$BACKEND_DIR"

# Start the server
print_info "Starting FastAPI server on port $SERVER_PORT..."

# Run uvicorn in background and capture PID
nohup python -m uvicorn main:app \
    --host 0.0.0.0 \
    --port "$SERVER_PORT" \
    --reload \
    > "$RUN_DIR/server.log" 2>&1 &

SERVER_PID=$!

# Save PID to file
echo "$SERVER_PID" > "$PID_FILE"

# Wait a moment and check if server started successfully
sleep 2

if ps -p "$SERVER_PID" > /dev/null 2>&1; then
    print_info "Server started successfully!"
    print_info "PID: $SERVER_PID"
    print_info "Port: $SERVER_PORT"
    print_info "Log file: $RUN_DIR/server.log"
    print_info ""
    print_info "To stop the server, run: kill $SERVER_PID"
    print_info "Or delete the PID file and run this script again"
else
    print_error "Server failed to start. Check logs at $RUN_DIR/server.log"
    rm -f "$PID_FILE"
    exit 1
fi
