#!/bin/bash

# Momentum Stock Screener - Start Script
# This script starts both the FastAPI backend and Next.js frontend

echo "🚀 Starting Momentum Stock Screener..."
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get the directory of this script
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Start FastAPI backend
echo -e "${BLUE}Starting FastAPI backend on port 8000...${NC}"
cd "$DIR"
python3 -m uvicorn api:app --reload --port 8000 &
BACKEND_PID=$!

# Wait for backend to start
sleep 2

# Start Next.js frontend
echo -e "${BLUE}Starting Next.js frontend on port 3000...${NC}"
cd "$DIR/frontend"
npm run dev &
FRONTEND_PID=$!

echo ""
echo -e "${GREEN}✅ Services started!${NC}"
echo ""
echo "   Backend API:  http://localhost:8000"
echo "   Frontend UI:  http://localhost:3000"
echo ""
echo "Press Ctrl+C to stop all services"

# Wait for both processes
wait $BACKEND_PID $FRONTEND_PID

