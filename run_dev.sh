#!/bin/bash
# Development runner script

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Knowledge Capture MVP Development Server${NC}"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}⚠️  Virtual environment not found. Running setup...${NC}"
    python setup.py
fi

# Activate virtual environment
source venv/bin/activate

# Check if .env exists
if [ ! -f ".env" ]; then
    echo -e "${RED}❌ .env file not found. Please create one from .env.template${NC}"
    exit 1
fi

# Start backend and frontend
echo -e "${GREEN}🔄 Starting backend server...${NC}"
uvicorn main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

echo -e "${GREEN}🔄 Starting frontend server...${NC}"
streamlit run frontend/streamlit_app.py --server.port 8501 --server.address 0.0.0.0 &
FRONTEND_PID=$!

echo -e "${GREEN}✅ Servers started!${NC}"
echo -e "Backend API: http://localhost:8000"
echo -e "Frontend: http://localhost:8501"
echo -e "API Docs: http://localhost:8000/docs"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop servers${NC}"

# Function to cleanup on exit
cleanup() {
    echo -e "\n${YELLOW}🛑 Stopping servers...${NC}"
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
    exit 0
}

# Trap Ctrl+C
trap cleanup SIGINT

# Wait for processes
wait
