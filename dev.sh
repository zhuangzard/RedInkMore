#!/bin/bash

# Function to kill child processes on exit
cleanup() {
    echo "Stopping servers..."
    kill $(jobs -p) 2>/dev/null
    exit
}

# Trap Ctrl+C (SIGINT) and call cleanup
trap cleanup SIGINT

echo "🚀 Starting Redit.io Development Environment..."

# 1. Start Backend in the background
echo "📦 Starting Backend (Port 12398)..."
uv run python -m backend.app &

# Wait for backend to initialize
sleep 2

# 2. Start Frontend in the foreground
echo "🎨 Starting Frontend (Port 5173)..."
cd frontend
pnpm dev

# Wait for any process to exit
wait
