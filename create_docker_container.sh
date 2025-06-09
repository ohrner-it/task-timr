#!/bin/bash

# Task Timr - Docker Container Creation Script
# Simple script to build and run Task Timr in Docker

set -e

CONTAINER_NAME="task-timr"
IMAGE_NAME="task-timr"

# Load environment variables if .env exists for defaults
if [ -f ".env" ]; then
    set -a  # Automatically export all variables
    source .env
    set +a  # Disable automatic export
fi

PORT="${PORT:-5000}"
HOST_INTERFACE="${BIND_IP:-127.0.0.1}"  # Default to localhost for security

# Parse command line arguments first
while [[ $# -gt 0 ]]; do
    case $1 in
        --host)
            HOST_INTERFACE="$2"
            shift 2
            ;;
        --port)
            PORT="$2"
            shift 2
            ;;
        --global)
            HOST_INTERFACE="0.0.0.0"
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --host HOST     Bind to specific host interface (default: 127.0.0.1)"
            echo "  --port PORT     Use specific port (default: 5000)"
            echo "  --global        Bind to all interfaces (0.0.0.0) - use only for production"
            echo "  -h, --help      Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0                          # Development: localhost:5000 (secure)"
            echo "  $0 --port 8080             # Development: localhost:8080"
            echo "  $0 --global                # Production: all interfaces:5000"
            echo "  $0 --host 192.168.1.100    # Specific interface"
            echo ""
            echo "Security Note: Use --global only for production deployments behind firewalls"
            exit 0
            ;;
        *)
            echo "❌ Error: Unknown option $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

echo "🐳 Task Timr - Docker Container Setup"
echo "====================================="

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "❌ .env file not found. Creating template..."
    cp .env.example .env
    echo "✅ Created .env from template"
    echo "⚠️  Please edit .env with your actual Timr.com credentials before running Docker"
    echo "   Required variables: SESSION_SECRET, TIMR_COMPANY_ID, TASKLIST_TIMR_USER, TASKLIST_TIMR_PASSWORD"
    exit 1
fi

# Check if Docker is available
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed or not in PATH"
    exit 1
fi

# Stop and remove existing container if it exists
if docker ps -a --format 'table {{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo "🛑 Stopping existing container..."
    docker stop "$CONTAINER_NAME" >/dev/null 2>&1 || true
    docker rm "$CONTAINER_NAME" >/dev/null 2>&1 || true
fi

# Build the Docker image
echo "🔨 Building Docker image..."
docker build -t "$IMAGE_NAME" .

# Run the container
echo "🚀 Starting container..."
# Container always binds to 0.0.0.0 internally, host interface controls external access
CONTAINER_PORT=5000  # Container always uses port 5000 internally
docker run -d \
  --name "$CONTAINER_NAME" \
  -p "${HOST_INTERFACE}:${PORT}:${CONTAINER_PORT}" \
  --env-file .env \
  -e BIND_IP=0.0.0.0 \
  -e PORT="${CONTAINER_PORT}" \
  "$IMAGE_NAME"

# Wait a moment for startup
echo "⏳ Waiting for application to start..."
sleep 3

# Check if container is running
if docker ps --format 'table {{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo "✅ Container started successfully"
    echo ""
    echo "📋 Container Information:"
    docker ps --filter "name=${CONTAINER_NAME}" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
    echo ""
    if [ "$HOST_INTERFACE" = "127.0.0.1" ] || [ "$HOST_INTERFACE" = "localhost" ]; then
        echo "🌐 Application URL: http://localhost:${PORT}"
        echo "🏥 Health check: http://localhost:${PORT}/health"
    else
        echo "🌐 Application URL: http://${HOST_INTERFACE}:${PORT}"
        echo "🏥 Health check: http://${HOST_INTERFACE}:${PORT}/health"
        echo "⚠️  Application is accessible from network - ensure proper firewall protection"
    fi
    echo ""
    echo "📋 Container Management:"
    echo "   View logs:    docker logs ${CONTAINER_NAME}"
    echo "   Stop:         docker stop ${CONTAINER_NAME}"
    echo "   Restart:      docker restart ${CONTAINER_NAME}"
    echo "   Remove:       docker rm ${CONTAINER_NAME}"
else
    echo "❌ Container failed to start"
    echo "📋 Check logs: docker logs ${CONTAINER_NAME}"
    exit 1
fi