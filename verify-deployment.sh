#!/bin/bash

# Task Timr - Deployment Verification Script
# Tests the deployment to ensure everything is working correctly

set -e

echo "🔍 Task Timr - Deployment Verification"
echo "====================================="

# Load environment variables if .env exists
if [ -f ".env" ]; then
    set -a  # Automatically export all variables
    source .env
    set +a  # Disable automatic export
fi

# Configuration - prioritize command line args, then env vars, then defaults
HOST="${1:-${BIND_IP:-localhost}}"
PORT="${2:-${PORT:-5000}}"
BASE_URL="http://$HOST:$PORT"

echo "Testing deployment at: $BASE_URL"
if [ -f ".env" ]; then
    echo "ℹ️  Using configuration from .env file (override with: $0 <host> <port>)"
else
    echo "ℹ️  Using default configuration (specify: $0 <host> <port>)"
fi
echo

# Test 1: Health check endpoint
echo "🏥 Testing health check endpoint..."
if curl -f -s "$BASE_URL/health" > /dev/null; then
    HEALTH_RESPONSE=$(curl -s "$BASE_URL/health")
    echo "✅ Health check passed"
    echo "   Response: $HEALTH_RESPONSE"
else
    echo "❌ Health check failed"
    exit 1
fi
echo

# Test 2: Main application endpoint
echo "🌐 Testing main application endpoint..."
if curl -f -s "$BASE_URL/" > /dev/null; then
    echo "✅ Main application endpoint is accessible"
else
    echo "❌ Main application endpoint failed"
    exit 1
fi
echo

# Test 3: Static assets (if any)
echo "📁 Testing static assets..."
if curl -f -s "$BASE_URL/static/" > /dev/null 2>&1; then
    echo "✅ Static assets are accessible"
else
    echo "ℹ️  Static assets endpoint not accessible (this may be normal)"
fi
echo

# Test 4: Response time check
echo "⏱️  Testing response time..."
RESPONSE_TIME=$(curl -o /dev/null -s -w "%{time_total}" "$BASE_URL/health")
echo "   Response time: ${RESPONSE_TIME}s"
if (( $(echo "$RESPONSE_TIME < 2.0" | bc -l) )); then
    echo "✅ Response time is acceptable"
else
    echo "⚠️  Response time is slow (${RESPONSE_TIME}s)"
fi
echo

# Test 5: Check if systemd service is running (if applicable)
if command -v systemctl &> /dev/null; then
    echo "🔧 Checking systemd service status..."
    if systemctl is-active --quiet task-timr 2>/dev/null; then
        echo "✅ Task Timr systemd service is running"
        SERVICE_STATUS=$(systemctl show task-timr --property=ActiveState,SubState --no-pager)
        echo "   Status: $SERVICE_STATUS"
    else
        echo "ℹ️  Task Timr systemd service is not running (may be using Docker or development mode)"
    fi
    echo
fi

# Test 6: Check Docker containers (if applicable)
if command -v docker &> /dev/null; then
    echo "🐳 Checking Docker containers..."
    if docker ps --filter "name=task-timr" --format "table {{.Names}}\t{{.Status}}" | grep -q task-timr; then
        echo "✅ Task Timr Docker container is running"
        docker ps --filter "name=task-timr" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
    else
        echo "ℹ️  No Task Timr Docker containers found"
    fi
    echo
fi

# Test 7: Port accessibility check
echo "🔌 Testing port accessibility..."
if nc -z "$HOST" "$PORT" 2>/dev/null; then
    echo "✅ Port $PORT is accessible on $HOST"
else
    echo "❌ Port $PORT is not accessible on $HOST"
fi
echo

# Test 8: SSL/TLS check (if HTTPS)
if [[ $BASE_URL == https* ]]; then
    echo "🔒 Testing SSL/TLS configuration..."
    if curl -f -s --insecure "$BASE_URL/health" > /dev/null; then
        echo "✅ HTTPS endpoint is accessible"
        # Check certificate validity
        CERT_INFO=$(echo | openssl s_client -servername "$HOST" -connect "$HOST:$PORT" 2>/dev/null | openssl x509 -noout -dates 2>/dev/null)
        echo "   Certificate info: $CERT_INFO"
    else
        echo "❌ HTTPS endpoint failed"
    fi
    echo
fi

# Summary
echo "📊 Verification Summary"
echo "======================"
echo "✅ All critical tests passed"
echo "🌐 Application URL: $BASE_URL"
echo "🏥 Health check URL: $BASE_URL/health"
echo
echo "📋 Next steps:"
echo "   1. Test login with your Timr.com credentials"
echo "   2. Create a working time entry"
echo "   3. Add some project times"
echo "   4. Verify data synchronization with Timr.com"
echo
echo "🎉 Deployment verification completed successfully!"