
#!/bin/bash
# Development server startup script

set -e

echo "Starting Pipewrench development server..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install/update dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "Warning: .env file not found. Copying from template..."
    cp .env.template .env
    echo "Please edit .env file with your configuration before running the server."
    exit 1
fi

# Create necessary directories
mkdir -p uploads logs

# Run database migrations (if alembic is set up)
# alembic upgrade head

# Start the development server
echo "Starting FastAPI server..."
python main.py
