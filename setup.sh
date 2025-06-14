#!/bin/bash

# Setup script for Task Timr
# This script creates a Python virtual environment and installs all dependencies

set -e  # Exit on any error

echo "🚀 Setting up Task Timr..."

# Check if Python 3.10+ is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 is not installed. Please install Python 3.10 or higher."
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 -c "import sys; print('.'.join(map(str, sys.version_info[:2])))")
REQUIRED_VERSION="3.10"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo "❌ Error: Python $REQUIRED_VERSION or higher is required. Found Python $PYTHON_VERSION"
    exit 1
fi

echo "✅ Python $PYTHON_VERSION found"

# Create virtual environment
echo "📦 Creating virtual environment..."
if [ -d "venv" ]; then
    echo "⚠️  Virtual environment already exists. Removing old one..."
    rm -rf venv
fi

python3 -m venv venv
echo "✅ Virtual environment created"

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install dependencies from pyproject.toml
echo "📥 Installing dependencies from pyproject.toml..."
pip install -e .

echo "✅ All dependencies installed successfully!"

# Set up environment variables
echo "📋 Creating environment configuration..."

# Create .env.example if it doesn't exist
if [ ! -f ".env.example" ]; then
    cat > .env.example << 'EOF'
# Task Timr - Environment Configuration Template
# Copy this file to .env and fill in your actual values

# Security Configuration
# Strong random string for session security (32+ characters recommended)
# Generate with: python -c "import secrets; print(secrets.token_urlsafe(32))"
SESSION_SECRET=your-production-session-secret-here

# Timr.com Configuration
# Your company ID in Timr.com
TIMR_COMPANY_ID=ohrnerit

# Task List Access Credentials
# Timr.com user account with task list access permissions
TASKLIST_TIMR_USER=your-tasklist-user@company.com
TASKLIST_TIMR_PASSWORD=your-tasklist-password

# Optional Configuration
# Flask environment (development, production)
FLASK_ENV=production

# Development Configuration (only for development)
# Uncomment and use these for local development
# FLASK_DEBUG=True
# FLASK_ENV=development
EOF
    echo "✅ Created .env.example template"
fi

# Create .env if it doesn't exist
if [ ! -f ".env" ]; then
    # Create .env with secure permissions from the start
    install -m 600 .env.example .env
    echo "✅ Created .env from template with secure permissions (600)"
    echo "⚠️  IMPORTANT: Edit .env with your actual Timr.com credentials before starting the application"
else
    echo "ℹ️  .env file already exists"
    # Ensure existing .env has secure permissions
    chmod 600 .env
    echo "✅ Set secure permissions on existing .env file"
fi

echo ""
echo "🎉 Setup complete! Here's how to get started:"
echo ""
echo "1. Configure your environment:"
echo "   Edit .env with your actual Timr.com credentials"
echo ""
echo "2. Start the application:"
echo "   ./start.sh                    # Development: secure localhost:5000"
echo "   ./start.sh --port 8080        # Development: different port"
echo ""
echo "   For production deployment only:"
echo "   ./start.sh --host 0.0.0.0     # Network accessible (use behind firewall)"
echo ""
echo "   Alternative methods:"
echo "   source venv/bin/activate && python main.py"
echo "   source venv/bin/activate && gunicorn --bind 0.0.0.0:5000 main:app"
echo ""
echo "📝 Note: Make sure to configure Timr.com API credentials with Task access permissions in .env"
echo "     Your app connects to the external Timr.com API for all data storage"
echo ""
