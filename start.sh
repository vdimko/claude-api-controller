#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo -e "${GREEN}Starting Claude API services...${NC}"

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}Docker is not running. Please start Docker first.${NC}"
    exit 1
fi

# Start MongoDB if not running
if ! docker ps | grep -q claude_api_mongo; then
    echo -e "${YELLOW}Starting MongoDB...${NC}"
    cd "$PROJECT_DIR/docker"
    docker-compose up -d
    echo "Waiting for MongoDB to be ready..."
    sleep 3
fi

# Check .env file
if [ ! -f "$PROJECT_DIR/.env" ]; then
    echo -e "${RED}.env file not found!${NC}"
    echo "Please copy .env.example to .env and configure your API key."
    exit 1
fi

# Source .env file
set -a
source "$PROJECT_DIR/.env"
set +a

# Install backend dependencies if needed
if [ ! -d "$PROJECT_DIR/backend/.venv" ] && ! python3 -c "import motor" 2>/dev/null; then
    echo -e "${YELLOW}Installing backend dependencies...${NC}"
    cd "$PROJECT_DIR/backend"
    python3 -m pip install -q -r requirements.txt
fi

# Install frontend dependencies if needed
if [ ! -d "$PROJECT_DIR/frontend/node_modules" ]; then
    echo -e "${YELLOW}Installing frontend dependencies...${NC}"
    cd "$PROJECT_DIR/frontend"
    npm install
fi

# Start FastAPI backend
echo -e "${YELLOW}Starting FastAPI backend...${NC}"
cd "$PROJECT_DIR/backend"
python3 -m uvicorn app.main:app --host 127.0.0.1 --port 8000 &
BACKEND_PID=$!

# Wait for backend to be ready
sleep 2
if ! curl -s http://localhost:8000/health > /dev/null; then
    echo -e "${RED}Backend failed to start${NC}"
    kill $BACKEND_PID 2>/dev/null
    exit 1
fi

# Start Next.js frontend
echo -e "${YELLOW}Starting Next.js frontend...${NC}"
cd "$PROJECT_DIR/frontend"
npm run dev &
FRONTEND_PID=$!

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Services started successfully!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "  MongoDB:  localhost:27018"
echo "  Backend:  http://localhost:8000"
echo "  Frontend: http://localhost:3000"
echo ""
echo "Press Ctrl+C to stop all services"
echo ""

# Trap SIGINT and SIGTERM to cleanup
cleanup() {
    echo ""
    echo -e "${YELLOW}Stopping services...${NC}"
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    echo -e "${GREEN}Services stopped.${NC}"
    exit 0
}

trap cleanup SIGINT SIGTERM

# Wait for processes
wait
