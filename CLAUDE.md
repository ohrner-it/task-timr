# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Essential Commands

### Setup and Development
```bash
# Initial setup (creates venv, installs dependencies)
./setup.sh

# Start development server (localhost:5000)
./start.sh

# Start with custom host/port
./start.sh --host 0.0.0.0 --port 8080
```

### Testing
```bash
# Run all tests (Python + JavaScript)
./run_all_tests.sh

# Run only Python tests
python3 run_tests.py

# Run only JavaScript tests
npm test

# Run specific JavaScript test
npx jest duration-parser.test.js

# Run Python tests with coverage
python3 -m coverage run -m unittest discover tests/ && python3 -m coverage report
```

### Environment and Dependencies
```bash
# Activate virtual environment
source venv/bin/activate

# Install/update Python dependencies
pip install -e .

# Install/update JavaScript dependencies
npm install
```

## Architecture Overview

### Core Components

**Backend (Python Flask)**
- `app.py`: Main Flask application with routes and UI logic
- `timr_api.py`: TimrApi class - handles all Timr.com API communication with automatic pagination
- `timr_utils.py`: ProjectTimeConsolidator class - converts between Timr.com's time-slot model and Task Timr's task-duration model
- `config.py`: Configuration management (environment variables, constants)

**Frontend (Vanilla JavaScript)**
- `static/js/main.js`: Main application logic and UI state management
- `static/js/project-time-handler.js`: Project time allocation and distribution logic
- `static/js/modules/`: Modular utilities (time parsing, DOM manipulation, error handling, etc.)

### Key Data Models

**UIProjectTime Class**: Frontend-friendly representation that aggregates multiple Timr.com project times into single task-duration entries. This is the core abstraction that allows task-focused time tracking instead of time-slot management.

**ProjectTimeConsolidator Class**: Handles the complex bidirectional mapping between:
- Timr.com's time-slot model (specific start/end times for projects)
- Task Timr's task-duration model (total time spent on tasks)

### API Integration
- All data is stored in Timr.com via their REST API
- No local database - the application is a frontend for Timr.com
- Automatic pagination handling for all list endpoints
- Comprehensive error handling and API response validation

## Development Patterns

### Testing Philosophy
Follows "Ten Laws for Unit Tests" (see `doc/README.Testing Guide.md`):
- Test real implementation, not mocks
- Mock only external boundaries (Timr.com API)
- Integration tests run against real Timr.com API
- Test files follow naming convention: `test_<module>[_<topic>].py` for Python, `<module>.test.js` for JavaScript

### Environment Configuration
- `.env` file contains sensitive credentials (Timr.com API access)
- `config.py` loads environment variables with fallbacks
- Environment variables: `TIMR_COMPANY_ID`, `TASKLIST_TIMR_USER`, `TASKLIST_TIMR_PASSWORD`, `SESSION_SECRET`

### Frontend Module Structure
- ES6 modules with explicit imports/exports
- Utility functions grouped by concern (time, DOM, state, etc.)
- Error handling centralized in `error-handler.js`
- State management for UI persistence in `state-management.js`

## Important Implementation Details

### Time Handling
- All internal calculations use minutes as the base unit
- Support for Jira-style duration input (e.g., "2h 30m", "1d 4h")
- Timezone handling via pytz for API communication
- Duration parsing supports flexible formats: "2:30", "2h30m", "150m", etc.

### Project Time Consolidation
The `ProjectTimeConsolidator` class performs complex operations:
- **Consolidation**: Aggregates multiple Timr.com project times into single UIProjectTime entries
- **Distribution**: Splits UIProjectTime entries back into time-slot-based Timr.com entries
- **Incremental updates**: Optimizes API calls by only updating changed entries

### Security Considerations
- Session management with secure cookies
- Input sanitization and validation
- API credential protection via environment variables
- Secure file permissions on .env (600)

## Deployment Notes

### Docker
```bash
# Development (localhost only)
./create_docker_container.sh

# Production (network accessible)
./create_docker_container.sh --global
```

### systemd Service
```bash
# Automated production deployment
./deploy-systemd.sh
```

### Health Monitoring
- Health check endpoint at `/health`
- Deployment verification via `./verify-deployment.sh`