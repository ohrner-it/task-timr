# Developer Guide: Timr.com Alternative Frontend

This guide provides information for developers working on the Timr.com alternative frontend, including architecture details, coding patterns, and best practices.

## Development Setup

To contribute to the development:

1. Fork this repository
2. Create a feature branch
3. Make your changes
4. Run the tests (see [Testing Guide](README.Testing%20Guide.md) for detailed instructions)
5. Submit a pull request

### Installation

#### Quick Setup (Recommended)

1. Clone this repository
2. Run the setup script (requires Python 3.10+ and npm):
   ```bash
   chmod +x setup.sh
   ./setup.sh
   ```
   The script installs Python and Node.js dependencies, running `npm install` automatically.
3. Configure your environment:
   ```bash
   cp .env.example .env
   # Edit .env with your Timr.com credentials
   ```
4. Start the application:
   ```bash
   chmod +x start.sh
   ./start.sh
   ```

#### Manual Setup

1. Clone this repository
2. Create a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -e .
   ```
4. Install frontend dependencies:
   ```bash
   npm install
   ```
5. Configure environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your actual Timr.com credentials
   ```
6. Run the application:
   ```bash
   # Using the start script (recommended):
   ./start.sh
   
   # Or manually with gunicorn:
   gunicorn --bind localhost:5000 --reuse-port --reload main:app
   
   # Or with Flask development server:
   python main.py
   ```

#### Configurable Network Settings

Task Timr supports configurable network binding for different deployment scenarios:

**Environment Variables:**
- `BIND_IP`: IP address to bind to (default: 127.0.0.1)
- `PORT`: Port number to use (default: 5000)

**Command Line Options:**
```bash
# Development (secure default):
./start.sh                    # localhost:5000

# Different port for development:
./start.sh --port 8080        # localhost:8080

# Production deployment (accessible from network):
./start.sh --host 0.0.0.0 --port 5000

# Behind reverse proxy:
./start.sh --host 127.0.0.1 --port 8000

# Get help:
./start.sh --help
```

**Interactive Configuration:**
```bash
# Guided setup for different scenarios:
./start-with-custom-network.sh
```

**Environment File Configuration:**
Set `BIND_IP` and `PORT` in your `.env` file:
```env
BIND_IP=127.0.0.1
PORT=5000
```

Command line arguments override environment variables, which override defaults.

**Security Note:** Only use `--host 0.0.0.0` for production deployments behind proper firewalls. Development should always use localhost to prevent unauthorized network access.

### Development Security

When developing Task Timr, follow these security practices:

**Network Binding:**
- Always use localhost (127.0.0.1) for development
- Never bind to 0.0.0.0 unless specifically deploying for production
- Use Docker port mapping `127.0.0.1:5000:5000` instead of `5000:5000`

**Credential Management:**
- Keep all credentials in `.env` files (excluded from git)
- Never commit credentials to version control
- Use strong, unique session secrets in production
- Store Timr.com credentials securely

**Environment File Security:**
- Use only simple KEY=value pairs in .env files
- Avoid shell metacharacters like `;`, `` ` ``, `$()`, or `$()`

**Environment Separation:**
- Use `FLASK_ENV=development` for local development
- Set `FLASK_DEBUG=True` only for debugging (never in production)
- Test with production-like settings before deployment

### Configuration

Edit `config.py` to configure:
- `COMPANY_ID`: Your Timr.com company ID (default: "ohrnerit")
- `API_BASE_URL`: The Timr API base URL (Timr.com API v1)
- `OAUTH_ISSUER`: The Timr.com OAuth2 authorization server; its endpoints are read from the OpenID Provider metadata (`<issuer>/.well-known/openid-configuration`) on first use
- Date and time formats

Users log in via OAuth2 at Timr.com. Create an OAuth client with grant type
"Authorization Code" in Timr.com under Administration > Settings > Integrations > API
Credentials and register the redirect URL of your Task Timr installation for it, e.g.
`http://localhost:5000/oauth/callback` for local development. Configure the client via
`TIMR_OAUTH_CLIENT_ID`, `TIMR_OAUTH_CLIENT_SECRET` and `TIMR_OAUTH_REDIRECT_URI` (see
[Environment Variables](#environment-variables)).

## Deployment

Task Timr provides multiple deployment options for different environments and use cases.

### Production Deployment with systemd

For production Linux servers, use the automated deployment script with configurable network settings:

#### Automated Deployment

```bash
chmod +x deploy-systemd.sh
./deploy-systemd.sh
```

The script will prompt for:
- **Security Configuration**: Session secret, Timr.com credentials
- **Network Configuration**: Bind IP address and port number
  - `127.0.0.1:5000` - Localhost only (recommended for reverse proxy)
  - `0.0.0.0:5000` - All network interfaces (direct access)
  - Custom IP and port combinations

#### Manual Installation Steps

1. **Create application user:**
   ```bash
   sudo useradd --system --shell /bin/bash --create-home --home-dir /opt/task-timr task-timr
   ```

2. **Deploy application files:**
   ```bash
   sudo mkdir -p /opt/task-timr
   sudo cp -r . /opt/task-timr/
   sudo chown -R task-timr:task-timr /opt/task-timr
   ```

3. **Set up Python environment:**
   ```bash
   sudo -u task-timr bash -c "cd /opt/task-timr && python3 -m venv venv && source venv/bin/activate && pip install -e ."
   ```

4. **Configure environment variables:**
   Create `/etc/task-timr/environment` with:
   ```env
   FLASK_ENV=production
   SESSION_SECRET=your-strong-secret
   TIMR_COMPANY_ID=your-company-id
   TIMR_OAUTH_CLIENT_ID=your-oauth-client-id
   TIMR_OAUTH_CLIENT_SECRET=your-oauth-client-secret
   TIMR_OAUTH_REDIRECT_URI=https://tasktimr.example.com/oauth/callback
   BIND_IP=127.0.0.1
   PORT=5000
   ```

5. **Install systemd service:**
   The deployment script creates a service with configurable network binding using environment variables.

6. **Verify the service:**
   ```bash
   sudo systemctl status task-timr
   curl http://localhost:PORT/health
   ```

#### Reverse Proxy Configuration

For production deployments, bind to localhost and use a reverse proxy:

**Nginx Example:**
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

**Apache Example:**
```apache
<VirtualHost *:80>
    ServerName your-domain.com
    ProxyPass / http://127.0.0.1:5000/
    ProxyPassReverse / http://127.0.0.1:5000/
    ProxyPreserveHost On
</VirtualHost>
```

#### Service Management

```bash
# Start the service
sudo systemctl start task-timr

# Stop the service
sudo systemctl stop task-timr

# Restart the service
sudo systemctl restart task-timr

# Check service status
sudo systemctl status task-timr

# View logs
sudo journalctl -u task-timr -f
```

### Docker Deployment

For containerized deployments, use the provided Docker configuration:

#### Single Container Deployment

1. **Build the Docker image:**
   ```bash
   docker build -t task-timr .
   ```

2. **Run the container:**
   ```bash
   docker run -d \
     --name task-timr \
     -p 5000:5000 \
     -e SESSION_SECRET="your-production-secret" \
     -e TIMR_COMPANY_ID="your-company-id" \
     -e TIMR_OAUTH_CLIENT_ID="your-oauth-client-id" \
     -e TIMR_OAUTH_CLIENT_SECRET="your-oauth-client-secret" \
     -e TIMR_OAUTH_REDIRECT_URI="http://localhost:5000/oauth/callback" \
     task-timr
   ```

#### Simplified Docker Deployment

Use the provided script for easy container management:

```bash
# Development (secure localhost only):
./create_docker_container.sh

# Development with custom port:
./create_docker_container.sh --port 8080

# Production (all interfaces):
./create_docker_container.sh --global

# Specific interface:
./create_docker_container.sh --host 192.168.1.100

# Get help:
./create_docker_container.sh --help
```

The script will:
- Create .env from template if it doesn't exist
- Build the Docker image
- Run the container with configurable network binding
- Default to localhost for security
- Provide management commands

#### Docker Management

```bash
# View logs
docker logs task-timr

# Stop container
docker stop task-timr

# Start container
docker start task-timr

# Restart container
docker restart task-timr

# Remove container
docker rm task-timr
```

### Environment Variables

Required environment variables for production:

| Variable | Description | Example |
|----------|-------------|---------|
| `SESSION_SECRET` | Secret key for session security | Strong random string (32+ characters) |
| `TIMR_COMPANY_ID` | Your Timr.com company identifier | `ohrnerit` |
| `TIMR_OAUTH_CLIENT_ID` | ID of the Timr.com OAuth client (grant type "Authorization Code") | `1234…@company.timr.com` |
| `TIMR_OAUTH_CLIENT_SECRET` | Secret of that OAuth client | Shown in Timr.com when creating the client |
| `TIMR_OAUTH_REDIRECT_URI` | Callback URL of this installation, must exactly match a redirect URL of the OAuth client | `https://tasktimr.example.com/oauth/callback` |

Optional environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `FLASK_ENV` | Flask environment mode | `production` |
| `TIMR_SERVICE_CLIENT_ID`, `TIMR_SERVICE_CLIENT_SECRET` | OAuth client with grant type "Client Credentials", only for developer tools (`raw_timr_responses.py`) and integration tests. It grants access to all data of the Timr.com account, so never configure it for the web application. | – |
| `TIMR_TEST_USER_ID` | Timr.com user ID whose data developer tools and integration tests work with | – |

### Health Monitoring

Both deployment methods include health check endpoints:

- **Health endpoint:** `GET /health`
- **Returns:** JSON with status, timestamp, and service information
- **Use for:** Load balancer health checks, monitoring systems

### Security Considerations

- Use strong, unique `SESSION_SECRET` values in production
- Run the application as a non-root user (systemd service does this automatically)
- Ensure secure network access to Timr.com API (HTTPS)
- Consider running behind a reverse proxy (nginx, Apache) for SSL termination
- Regularly update dependencies and base images
- Monitor logs for security events
- Store Timr.com credentials securely using environment variables

### Performance Tuning

The provided configurations include optimized settings:

- **Gunicorn workers:** 4 workers for balanced CPU utilization
- **Request limits:** Protection against memory leaks with request cycling
- **Timeouts:** Appropriate timeouts for web requests
- **Session storage:** In-memory sessions for simplicity (no external dependencies)



## Project Structure

```
task-timr/
├── app.py                           # Main Flask application
├── main.py                          # Application entry point
├── timr_api.py                      # Timr API client with pagination support
├── timr_oauth.py                    # OAuth2 client for the Timr.com authorization server
├── timr_utils.py                    # Helper classes including ProjectTimeConsolidator
├── config.py                        # Configuration settings and environment variables
├── pyproject.toml                   # Python project metadata and dependencies
├── uv.lock                          # Dependency lockfile for reproducible builds
├── package.json                     # Node.js dependencies for testing
├── package-lock.json                # Node.js dependency lockfile
├── babel.config.js                  # Babel configuration for JavaScript transpilation
├── setup.sh                        # Automated setup script
├── start.sh                         # Application startup script
├── run_tests.py                     # Python test runner
├── templates/                       # Jinja2 HTML templates
│   ├── base.html                    # Base template with common layout
│   └── index.html                   # Main application interface
├── static/                          # Static web assets
│   ├── js/
│   │   ├── modules/                 # Modular JavaScript components
│   │   │   ├── time-utils.js        # Time parsing and formatting utilities
│   │   │   ├── duration-parser.js   # Duration input parsing (Jira-style)
│   │   │   ├── dom-utils.js         # DOM manipulation utilities
│   │   │   ├── state-management.js  # Application state handling
│   │   │   └── ui-utils.js          # UI interaction utilities
│   │   ├── main.js                  # Main application JavaScript
│   │   └── project-time-handler.js  # Project time CRUD operations
│   └── css/
│       └── custom.css               # Custom styles and Bootstrap overrides
├── tests/                           # Test suite
│   ├── utils/                       # Test utilities package
│   │   ├── __init__.py              # Package exports
│   │   ├── mock_validator.py        # Mock validation framework
│   │   ├── mock_data.py             # Reference mock data structures
│   │   ├── http_responses.py        # Real requests.Response objects for HTTP boundary mocks
│   │   └── integration.py           # Setup for integration tests against Timr.com
│   ├── __init__.py                  # Makes tests a Python package
│   ├── test_*.py                    # Python unit and integration tests
│   ├── test_comprehensive_mock_validation.py  # Mock validation tests
│   └── frontend/                    # Frontend JavaScript tests
│       ├── __init__.py
│       ├── *.test.js                # Jest test files
│       ├── setup.js                 # Test environment configuration
│       └── test_helpers.js          # Shared test utilities
├── README.md                        # Main project documentation
├── README.Developer Guide.md        # This developer guide
├── README.Testing Guide.md          # Testing documentation
├── README.User Guide.md             # End-user documentation
└── LICENSE                          # MIT license
```

### Key Configuration Files

#### Python Packaging
- **`pyproject.toml`**: Modern Python project specification (PEP 518/621) containing project metadata, Python version requirements (≥3.10), and all runtime dependencies with version constraints
- **`uv.lock`**: Automatically generated lockfile with exact dependency versions, cryptographic hashes, and complete dependency tree for reproducible builds across environments

#### JavaScript Testing
- **`package.json`**: Node.js dependencies for JavaScript testing with Jest configuration, test scripts, and Babel transpilation setup
- **`package-lock.json`**: Node.js dependency lockfile for consistent JavaScript testing environment
- **`babel.config.js`**: Babel configuration for JavaScript transpilation during testing

#### Platform Configuration
- **`.replit`**: Replit platform configuration specifying runtime environments (Python 3.11, Node.js 20), deployment settings with gunicorn, development workflows, and port mappings (5000→80)

### Dependency Management

**Python Dependencies**: Edit `pyproject.toml` then run `pip install -e .` for editable installation from single source of truth

**JavaScript Dependencies**: Use npm commands to update `package.json` and `package-lock.json`, then run `npm install`

**Installation Methods**: Both `setup.sh` and manual setup use `pip install -e .` ensuring consistency across all installation approaches

## Architecture Overview

The application uses a stateless three-tier architecture:

1. **Frontend**: Browser-based UI (HTML, CSS, JavaScript)
2. **Backend API**: Python Flask server (stateless, no local database)
3. **External Service**: Timr.com API (all data storage)

### Key Design Principles

- **Stateless Design**: No local database or persistent storage - all data comes from Timr.com API
- **Separation of Concerns**: The frontend never directly interacts with the Timr.com API
- **Model Abstraction**: Backend abstracts Timr's complex data model into a simpler UI model
- **Encapsulation**: All Timr-specific logic is encapsulated in the backend
- **External Data Only**: Application serves as a specialized interface to existing Timr.com data

## Data Models

### UIProjectTime (Frontend Model)

This model represents a time allocation for a specific task within a working time:

```javascript
{
  "task_id": "task123",          // Unique identifier of the task
  "task_name": "Development",    // Display name of the task
  "duration_minutes": 120,       // Time spent on this task in minutes
  "task_breadcrumbs": "Project/Feature/Development"  // Task hierarchy path
}
```

### Working Time with Project Times (Backend Model)

In Timr.com, a working time represents when an employee was at work, and project times represent specific tasks performed during that time:

```javascript
{
  "id": "wt123",                    // Working time ID
  "start": "2025-05-01T09:00:00Z",  // Start of work
  "end": "2025-05-01T17:00:00Z",    // End of work
  "break_time_total_minutes": 30,   // Break duration
  "status": "changeable",           // Status of this entry
  "ui_project_times": [...]         // Consolidated task times
}
```

## API Design

### RESTful Endpoint Structure

The application follows RESTful principles with working time-scoped UIProjectTime endpoints. All project time operations are nested under their parent working time to maintain data consistency.

### Key Components

- **TimrApi** (`timr_api.py`): Handles communication with the external Timr.com API
- **TimrOAuthClient** (`timr_oauth.py`): Obtains, refreshes and revokes OAuth2 tokens at the Timr.com authorization server
- **ProjectTimeConsolidator** (`timr_utils.py`): Translates between Timr's complex time slot model and our simplified task duration model
- **Flask Routes** (`app.py`): Provides the REST API for the frontend

The consolidator is the core abstraction layer that allows the frontend to work with simple task durations while maintaining compatibility with Timr's time slot requirements.

### Authentication with Timr.com

Task Timr uses the OAuth2 authorization code flow with PKCE of the Timr.com API v1:

1. `GET /login` redirects the browser to the Timr.com login page.
2. After the login, Timr.com redirects back to `GET /oauth/callback`, where the backend
   exchanges the authorization code for an access token and a refresh token, determines
   the Timr.com user ID via the OpenID Connect userinfo endpoint and loads the user.
3. Tokens, user ID and name are kept in the signed (not encrypted) Flask session cookie,
   which is marked `Secure` when the redirect URI uses HTTPS. `get_current_user()`
   refreshes the access token shortly before it expires and authorizes the `TimrApi`
   client for the request; if the access token has expired and cannot be refreshed, the
   user has to log in again. Timr.com rotates refresh tokens, so a refresh of concurrent
   requests may fail while the access token is still valid; this is tolerated.
4. `GET /logout` clears the session and revokes the refresh token.

All requests to the Timr.com API therefore run with the permissions of the logged-in
user. Tasks are retrieved via `/users/{id}/tasks`, which returns exactly the tasks the
user may book on; the API filters bookable tasks which are active today, including
end dates inherited from closed parent tasks.

Timr.com reports API errors as RFC 9457 problem details. `TimrApi` uses the `detail`
and field-level `errors` as error message and keeps the problem `type` URI in
`TimrApiError.problem_type` for detecting specific error conditions.

### Time Slot Handling Overview

Timr stores project times as individual time slots. Users, however, usually think in
terms of total time spent on a task during a working time. The `ProjectTimeConsolidator`
merges all slots of the same task into a single `UIProjectTime` object and generates
new sequential time slots when saving changes. Duplicate time slots returned from the
API are removed so that exactly one project time per task remains after an update.
Slots are created in descending order of the task names and may overlap if the working
time is shorter than the combined duration.

## Key Design Patterns

### Composite Key Pattern
UIProjectTime objects use `(working_time_id, task_id)` as a composite identifier, enabling task-focused time tracking where multiple time slots for the same task appear as a single duration entry.

### Abstraction Layer
The backend abstracts Timr's complex time slot model into a simplified task duration model, allowing the frontend to focus on "how long" rather than "when exactly."

## Testing

For comprehensive testing information, including test structure, naming conventions, running tests, and the Ten Laws for Unit Tests, see the [Testing Guide](README.Testing%20Guide.md).

## Getting Started as a Developer

1. **Study the Architecture**: Understand the three-tier design and abstraction principles
2. **Review the Data Models**: Focus on how UIProjectTime simplifies the Timr model
3. **Examine Key Files**: Start with `timr_utils.py` for the core logic, then `app.py` for the API
4. **Run the Tests**: Get familiar with the testing patterns and coverage
5. **Make Small Changes**: Begin with minor improvements to understand the data flow

The codebase prioritizes simplicity and maintainability - when in doubt, choose the simpler approach that maintains the abstraction boundaries.