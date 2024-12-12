#!/bin/bash

# AirSeal Project Setup Script

# Check Python version
PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
REQUIRED_VERSION="3.9"

version_compare() {
    if [[ "$(printf '%s\n' "$@" | sort -V | head -n1)" == "$1" ]]; then
        return 0
    fi
    return 1
}

# Verify Python version
if ! version_compare "$PYTHON_VERSION" "$REQUIRED_VERSION"; then
    echo "Error: Python 3.9+ required. Current version: $PYTHON_VERSION"
    exit 1
fi

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
if [ ! -f .env ]; then
    echo "DOCKER_BUILD_DIR=$(pwd)/builds" > .env
fi

# Verify Docker installation
if ! command -v docker &> /dev/null; then
    echo "Warning: Docker not found. Please install Docker."
    exit 1
fi

echo "AirSeal setup complete!"
echo "Run with: streamlit run app.py"
