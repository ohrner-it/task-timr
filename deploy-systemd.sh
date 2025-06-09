#!/bin/bash

# Task Timr - Systemd Deployment Script
# Automates the deployment of Task Timr as a systemd service

set -euo pipefail

# Cleanup function for rollback on failure
cleanup() {
    local exit_code=$?
    if [ $exit_code -ne 0 ]; then
        echo "❌ Deployment failed. Rolling back changes..."
        sudo systemctl stop task-timr 2>/dev/null || true
        sudo systemctl disable task-timr 2>/dev/null || true
        sudo rm -f /etc/systemd/system/task-timr.service
        sudo systemctl daemon-reload
        echo "⚠️  Rollback completed. Check the logs above for details."
    fi
    exit $exit_code
}

trap cleanup EXIT

echo "🚀 Task Timr - Systemd Deployment Script"
echo "========================================="

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   echo "❌ This script should not be run as root. Please run as a regular user with sudo privileges."
   exit 1
fi

# Check if systemd is available
if ! command -v systemctl &> /dev/null; then
    echo "❌ systemd is not available on this system"
    exit 1
fi

# Configuration variables
APP_USER="task-timr"
APP_DIR="/opt/task-timr"
SERVICE_FILE="task-timr.service"

echo "📋 Configuration:"
echo "   User: ${APP_USER}"
echo "   Directory: ${APP_DIR}"
echo "   Service file: ${SERVICE_FILE}"
echo

# Function to validate input for security
validate_input() {
    local input="$1"
    local field_name="$2"
    
    # Check for basic security issues
    if [[ "$input" =~ [\"\'\\] ]]; then
        echo "❌ ${field_name} contains invalid characters (quotes or backslashes)"
        exit 1
    fi
    
    if [ ${#input} -gt 1000 ]; then
        echo "❌ ${field_name} is too long (max 1000 characters)"
        exit 1
    fi
}

# Prompt for required environment variables
echo "🔐 Please provide the required configuration:"
read -p "Session secret (strong random string): " SESSION_SECRET
read -p "Timr company ID [ohrnerit]: " TIMR_COMPANY_ID
TIMR_COMPANY_ID=${TIMR_COMPANY_ID:-ohrnerit}
read -p "Tasklist Timr username: " TASKLIST_TIMR_USER
read -s -p "Tasklist Timr password: " TASKLIST_TIMR_PASSWORD
echo

echo
echo "🌐 Network configuration:"
read -p "Bind IP address [127.0.0.1]: " BIND_IP
BIND_IP=${BIND_IP:-127.0.0.1}
read -p "Port number [5000]: " PORT
PORT=${PORT:-5000}

echo "ℹ️  Network binding: ${BIND_IP}:${PORT}"
if [ "$BIND_IP" = "0.0.0.0" ]; then
    echo "⚠️  Warning: Binding to 0.0.0.0 makes the service accessible from all network interfaces"
elif [ "$BIND_IP" = "127.0.0.1" ]; then
    echo "🔒 Secure: Binding to localhost only (reverse proxy recommended for external access)"
fi

# Validate inputs
if [ -z "${SESSION_SECRET}" ] || [ -z "${TASKLIST_TIMR_USER}" ] || [ -z "${TASKLIST_TIMR_PASSWORD}" ]; then
    echo "❌ All configuration values are required"
    exit 1
fi

# Validate each input for security
validate_input "${SESSION_SECRET}" "Session secret"
validate_input "${TIMR_COMPANY_ID}" "Company ID"
validate_input "${TASKLIST_TIMR_USER}" "Username"
validate_input "${TASKLIST_TIMR_PASSWORD}" "Password"
validate_input "${BIND_IP}" "Bind IP"
validate_input "${PORT}" "Port"

# Ensure session secret is strong enough
if [ ${#SESSION_SECRET} -lt 32 ]; then
    echo "❌ Session secret must be at least 32 characters long"
    exit 1
fi

# Validate port number
if ! [[ "$PORT" =~ ^[0-9]+$ ]] || [ "$PORT" -lt 1 ] || [ "$PORT" -gt 65535 ]; then
    echo "❌ Port must be a number between 1 and 65535"
    exit 1
fi

# Validate IP address format
if ! [[ "$BIND_IP" =~ ^([0-9]{1,3}\.){3}[0-9]{1,3}$ ]] && [ "$BIND_IP" != "localhost" ]; then
    echo "❌ Invalid IP address format"
    exit 1
fi

echo "👤 Creating application user..."
if ! id "${APP_USER}" &>/dev/null; then
    sudo useradd --system --shell /bin/bash --create-home --home-dir "${APP_DIR}" "${APP_USER}"
    echo "✅ User ${APP_USER} created"
else
    echo "ℹ️  User ${APP_USER} already exists"
fi

echo "📁 Creating application directory..."
sudo mkdir -p "${APP_DIR}"
sudo mkdir -p "${APP_DIR}/logs"
sudo chown -R "${APP_USER}:${APP_USER}" "${APP_DIR}"

echo "📦 Copying application files..."
# Copy files using .deployignore file if available, otherwise use manual excludes
if [ -f ".deployignore" ]; then
    sudo rsync -av --exclude-from='.deployignore' . "${APP_DIR}/"
else
    sudo rsync -av \
        --exclude='.env' \
        --exclude='.env.*' \
        --exclude='venv/' \
        --exclude='__pycache__/' \
        --exclude='*.pyc' \
        --exclude='*.pyo' \
        --exclude='.pytest_cache/' \
        --exclude='.coverage' \
        --exclude='htmlcov/' \
        --exclude='.git/' \
        --exclude='.gitignore' \
        --exclude='node_modules/' \
        --exclude='*.log' \
        --exclude='logs/' \
        --exclude='.DS_Store' \
        --exclude='Thumbs.db' \
        --exclude='*.tmp' \
        --exclude='*.swp' \
        --exclude='*.swo' \
        --exclude='.vscode/' \
        --exclude='.idea/' \
        . "${APP_DIR}/"
fi
sudo chown -R "${APP_USER}:${APP_USER}" "${APP_DIR}"

echo "🐍 Setting up Python environment..."
# Remove any existing venv to ensure clean setup
sudo -u "${APP_USER}" bash -c "cd '${APP_DIR}' && rm -rf venv"

# Create new virtual environment
sudo -u "${APP_USER}" bash -c "cd '${APP_DIR}' && python3 -m venv venv"

# Check if venv was created successfully
if [ ! -f "${APP_DIR}/venv/bin/activate" ]; then
    echo "❌ Failed to create virtual environment"
    exit 1
fi

# Install dependencies
echo "📦 Installing Python dependencies..."
sudo -u "${APP_USER}" bash -c "cd '${APP_DIR}' && source venv/bin/activate && pip install --upgrade pip"
sudo -u "${APP_USER}" bash -c "cd '${APP_DIR}' && source venv/bin/activate && pip install -e ."

# Verify installation
if ! sudo -u "${APP_USER}" bash -c "cd '${APP_DIR}' && source venv/bin/activate && python -c 'import flask; print(\"Flask installed successfully\")'"; then
    echo "❌ Failed to install dependencies properly"
    exit 1
fi



echo "⚙️  Configuring systemd service..."

# Create environment file with secrets securely (no race condition)
echo "Creating secure environment file..."
sudo mkdir -p /etc/task-timr

# Create file with secure permissions from the start
cat <<EOF | sudo install -m 640 -o root -g "${APP_USER}" /dev/stdin /etc/task-timr/environment
FLASK_ENV=production
SESSION_SECRET=${SESSION_SECRET}
TIMR_COMPANY_ID=${TIMR_COMPANY_ID}
TASKLIST_TIMR_USER=${TASKLIST_TIMR_USER}
TASKLIST_TIMR_PASSWORD=${TASKLIST_TIMR_PASSWORD}
BIND_IP=${BIND_IP}
PORT=${PORT}
EOF

# Create systemd service file without embedded secrets
cat > /tmp/task-timr.service <<EOF
[Unit]
Description=Task Timr - Task duration-focused alternative frontend to Timr.com
After=network.target
Requires=network.target

[Service]
Type=exec
User=${APP_USER}
Group=${APP_USER}
WorkingDirectory=${APP_DIR}
EnvironmentFile=/etc/task-timr/environment
ExecStart=${APP_DIR}/venv/bin/gunicorn --bind \${BIND_IP}:\${PORT} --workers 4 --timeout 120 --keep-alive 5 --max-requests 1000 --max-requests-jitter 100 --preload main:app
ExecReload=/bin/kill -s HUP \$MAINPID
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=task-timr

# Security settings
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=${APP_DIR}/logs ${APP_DIR}
CapabilityBoundingSet=CAP_NET_BIND_SERVICE
AmbientCapabilities=CAP_NET_BIND_SERVICE

# Resource limits
LimitNOFILE=65536
LimitNPROC=4096

[Install]
WantedBy=multi-user.target
EOF

# Set proper permissions and move service file
chmod 644 /tmp/task-timr.service
sudo mv /tmp/task-timr.service /etc/systemd/system/task-timr.service

echo "🔄 Reloading systemd configuration..."
sudo systemctl daemon-reload

echo "🎯 Enabling and starting Task Timr service..."
sudo systemctl enable task-timr
sudo systemctl start task-timr

echo "⏳ Waiting for service to start..."
sleep 5

echo "🔍 Checking service status..."
# Wait a bit longer for service to fully start
sleep 10

if sudo systemctl is-active --quiet task-timr; then
    echo "✅ Task Timr service is running successfully!"
    echo
    echo "📊 Service status:"
    sudo systemctl status task-timr --no-pager -l
    echo
    
    echo "🌐 Health check:"
    # Try health check multiple times in case of slow startup
    health_check_passed=false
    # Determine health check URL based on bind IP
    if [ "$BIND_IP" = "127.0.0.1" ] || [ "$BIND_IP" = "localhost" ]; then
        HEALTH_URL="http://localhost:${PORT}/health"
    else
        HEALTH_URL="http://${BIND_IP}:${PORT}/health"
    fi
    for i in {1..5}; do
        if curl -f -s "$HEALTH_URL" &>/dev/null; then
            health_check_passed=true
            break
        fi
        echo "   Attempt $i/5 - waiting for application to respond..."
        sleep 2
    done
    
    if [ "$health_check_passed" = true ]; then
        echo "✅ Application is responding to health checks"
        # Test the main page as well
        if curl -f -s "http://localhost:${PORT}/" &>/dev/null; then
            echo "✅ Main application page is accessible"
        else
            echo "⚠️  Main page check failed but health endpoint works"
        fi
    else
        echo "❌ Application health check failed - check logs below"
        sudo journalctl -u task-timr --no-pager -l --since="5 minutes ago"
        exit 1
    fi
    
    echo
    echo "🔒 Security verification:"
    echo "   Environment file permissions: $(stat -c '%a' /etc/task-timr/environment)"
    echo "   Application directory owner: $(stat -c '%U:%G' ${APP_DIR})"
    
    echo
    echo "📋 Management commands:"
    echo "   Status: sudo systemctl status task-timr"
    echo "   Logs:   sudo journalctl -u task-timr -f"
    echo "   Stop:   sudo systemctl stop task-timr"
    echo "   Start:  sudo systemctl start task-timr"
    echo "   Restart: sudo systemctl restart task-timr"
    echo
    echo "🎉 Deployment completed successfully!"
    if [ "$BIND_IP" = "127.0.0.1" ] || [ "$BIND_IP" = "localhost" ]; then
        echo "   Access your application at: http://localhost:${PORT}"
        echo "   Service is bound to localhost only - use a reverse proxy for external access"
    elif [ "$BIND_IP" = "0.0.0.0" ]; then
        echo "   Access your application at: http://localhost:${PORT}"
        echo "   Or from other machines at: http://$(hostname -I | awk '{print $1}'):${PORT}"
    else
        echo "   Access your application at: http://${BIND_IP}:${PORT}"
    fi
else
    echo "❌ Service failed to start. Detailed logs:"
    sudo journalctl -u task-timr --no-pager -l --since="10 minutes ago"
    echo
    echo "🔧 Troubleshooting steps:"
    echo "   1. Check application logs: sudo journalctl -u task-timr -f"
    echo "   2. Test manual startup: sudo -u ${APP_USER} bash -c 'cd ${APP_DIR} && source venv/bin/activate && python main.py'"
    echo "   3. Test application import: sudo -u ${APP_USER} bash -c 'cd ${APP_DIR} && source venv/bin/activate && python -c \"from app import app; print(\\\"App loaded successfully\\\")\"'"
    exit 1
fi