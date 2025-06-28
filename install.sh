#!/bin/bash
# Installation script for JSP CLI tool

set -e

echo "Installing JSP CLI tool..."

# Check if Python 3.9+ is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed."
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
REQUIRED_VERSION="3.9"

if ! python3 -c "import sys; exit(0 if sys.version_info >= (3, 9) else 1)"; then
    echo "Error: Python $REQUIRED_VERSION or higher is required (found $PYTHON_VERSION)"
    exit 1
fi

echo "Python $PYTHON_VERSION detected ✓"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Install the package in development mode
echo "Installing JSP in development mode..."
pip install -e .

echo ""
echo "✓ Installation complete!"
echo ""
echo "To use JSP:"
echo "  1. Activate the virtual environment: source venv/bin/activate"
echo "  2. Run the CLI: jsp <URL>"
echo ""
echo "Example:"
echo "  jsp https://www.josephsmithpapers.org/paper-summary/book-of-mormon-1830/1"