#!/bin/bash

# Start script for Task Timr
# This script activates the virtual environment and starts the application using gunicorn

set -e  # Exit on any error

# Load environment variables if .env exists
if [ -f ".env" ]; then
    set -a  # Automatically export all variables
    source .env
    set +a  # Disable automatic export
fi

# Default configuration - use environment variables if available
DEFAULT_HOST="${BIND_IP:-localhost}"
DEFAULT_PORT="${PORT:-5000}"

# Parse command line arguments
HOST="$DEFAULT_HOST"
PORT="$DEFAULT_PORT"

while [[ $# -gt 0 ]]; do
    case $1 in
        --host)
            HOST="$2"
            shift 2
            ;;
        --port)
            PORT="$2"
            shift 2
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --host HOST    Set the host/IP address (default: localhost)"
            echo "  --port PORT    Set the port number (default: 5000)"
            echo "  -h, --help     Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0                          # Start on localhost:5000"
            echo "  $0 --host 0.0.0.0          # Start on all interfaces"
            echo "  $0 --port 8080             # Start on localhost:8080"
            echo "  $0 --host 0.0.0.0 --port 8080  # Start on all interfaces, port 8080"
            exit 0
            ;;
        *)
            echo "❌ Error: Unknown option $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

BIND="${HOST}:${PORT}"

echo "🚀 Starting Task Timr..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Error: Virtual environment not found. Please run setup.sh first."
    exit 1
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚠️  Warning: .env file not found. Using default/environment variables."
    echo "   Consider copying .env.example to .env and configuring your settings."
fi

# Start the application with gunicorn
echo "📡 Starting server on ${BIND}..."

# Show appropriate URL for browser
if [ "$HOST" = "0.0.0.0" ] || [ "$HOST" = "::" ]; then
    echo "   Open your browser to: http://localhost:${PORT}"
    if [ "$HOST" = "::" ]; then
        echo "   (Server accessible from all IPv4/IPv6 interfaces)"
    else
        echo "   (Server accessible from all IPv4 network interfaces)"
    fi
else
    # Handle IPv6 addresses properly by wrapping them in brackets
    if [[ "$HOST" == *":"* ]] && [[ "$HOST" != "localhost" ]]; then
        echo "   Open your browser to: http://[${HOST}]:${PORT}"
    else
        echo "   Open your browser to: http://${BIND}"
    fi
fi

echo "   Press Ctrl+C to stop the server"
echo ""

exec gunicorn --bind "${BIND}" --reuse-port --reload main:app
