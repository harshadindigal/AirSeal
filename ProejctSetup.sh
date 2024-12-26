#!/bin/bash

# AirSeal Project Setup Script

# Check Python version
PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
REQUIRED_VERSION="3.9.0"

version_compare() {
    echo "Current Python version: $1"
    echo "Required minimum version: $2"
    
    # Extract major, minor, and patch versions
    local current_major=$(echo "$1" | cut -d. -f1)
    local current_minor=$(echo "$1" | cut -d. -f2)
    local current_patch=$(echo "$1" | cut -d. -f3)
    
    local required_major=$(echo "$2" | cut -d. -f1)
    local required_minor=$(echo "$2" | cut -d. -f2)
    local required_patch=$(echo "$2" | cut -d. -f3)
    
    # Compare major version first
    if [ "$current_major" -gt "$required_major" ]; then
        return 0
    elif [ "$current_major" -lt "$required_major" ]; then
        return 1
    fi
    
    # If major versions are equal, compare minor versions
    if [ "$current_minor" -gt "$required_minor" ]; then
        return 0
    elif [ "$current_minor" -lt "$required_minor" ]; then
        return 1
    fi
    
    # If minor versions are equal, compare patch versions
    if [ "$current_patch" -ge "$required_patch" ]; then
        return 0
    fi
    
    return 1
}

# Verify Python version
if ! version_compare "$PYTHON_VERSION" "$REQUIRED_VERSION"; then
    echo "Error: Python 3.9+ required. Current version: $PYTHON_VERSION"
    exit 1
fi

echo "Python version check passed successfully!"

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
if [ ! -f .env ]; then
    echo "DOCKER_BUILD_DIR=$(pwd)/builds" > .env
fi

# Create builds directory
mkdir -p $(pwd)/builds

# Verify Docker installation
if ! command -v docker &> /dev/null; then
    echo "Warning: Docker not found. Please install Docker."
    exit 1
fi

# Verify Docker daemon is running
if ! docker info >/dev/null 2>&1; then
    echo "Warning: Docker daemon is not running. Please start Docker."
    exit 1
fi

echo "AirSeal setup complete!"
echo "Run with: streamlit run app.py"
