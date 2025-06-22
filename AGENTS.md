# Instructions for Developers and AI Agents

Task Timr is an alternative web frontend for the Timr.com time tracking service.
For an overview see the README.

## Application Basics

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

## Scope
These guidelines apply to the entire repository.

## Documentation
- The main documentation lives in the `doc` directory and the repository root.
- Key references:
  - [Project README](README.md)
  - [Documentation Index](doc/README.md)
  - [Developer Guide](doc/README.Developer%20Guide.md)
  - [Testing Guide](doc/README.Testing%20Guide.md)
  - [User Guide](doc/README.User%20Guide.md)
  - [Timr API Specification](doc/timr_api_0_2_11_openapi_v3.md)
  
  These files may evolve, so always consult them for up-to-date guidelines.

## Setup and Development
```bash
# Initial setup (creates venv, installs dependencies)
./setup.sh

# Start development server (localhost:5000)
./start.sh

# Start with custom host/port
./start.sh --host 0.0.0.0 --port 8080
```

## IMPORTANT: Follow This Development Workflow
1. If the task is not fully clear or is lacking relevant information, please ask back
   and obtain this information before starting the task. You may suggest solutions,
   but also let the user confirm them.
2. Use **test driven development**. Write or adapt tests first, then implement the
   desired functionality.
3. Before you consider a task as completed or finished, critically review all
   changes you did and verify that these follow the project's coding and testing
   guidelines and rules.
   - In particular, tests MUST test the real code. Tests which only work on
     Mocks or duplicate the logic under test in their own implementation are
     meaningless and MUST be rewritten to follow the "Ten Laws for Unit Tests"
     (see below).
   - If you find violations of the guidelines or rules laid out in here or the
     project documentation, go back to step 2. and restart your work to resolve
     these findings. After you consider the issues resolved, make sure all tests
     really pass, and then critically review again. Repeat until the review does
     not find any violations of the project's coding and testing guidelines and
     rules any more.
4. Run all tests before committing. The recommended command is:
   ```bash
   ./run_all_tests.sh
   ```
   This executes Python tests via `python3 run_tests.py` and JavaScript tests via
   `npm test` in `tests/frontend`.
   - Integration tests that talk to the real Timr.com API are required when adding
     or adjusting code that interacts with external services.
   - ALL tests MUST finish successfully before any modifications are allowed to
     be committed.
5. Refrain from creating new documentation files which in detail describe the
   changes performed for the current task. Such documentation files serve no
   long-term purpose, clutter the documentation folder and get obsolete nearly
   immediately. See the instructions on how to update the documentation below.

## Commit and PR Guidelines
- Use concise commit messages: a single short summary line, followed by an empty
  line and optional details.
- Ensure the repository is in a clean state and all tests pass before creating a
  pull request.
- Pull request descriptions should summarise **all** changes contained in the
  pull request and mention the test results.

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
- All tests must adhere to the "Ten Laws for Unit Tests" defined in the
  [Testing Guide](doc/README.Testing%20Guide.md).
- Follow the **Test Structure and Naming Conventions** from the Testing Guide.
  Each Python module should have its own test file named
  `test_<module_under_test>[_<specific_test_topic>].py`.
- JavaScript tests belong in files following the pattern
  `<module_under_test>.test.js`.
- Keep unrelated tests in separate modules. Do not combine tests for different
  production modules in one file and avoid renaming test modules without a
  compelling reason.
- Avoid redundant test classes; each test class should have a clear, unique purpose.

### Environment Configuration
- `.env` file contains sensitive credentials (Timr.com API access)
- `config.py` loads environment variables with fallbacks
- Environment variables: `TIMR_COMPANY_ID`, `TASKLIST_TIMR_USER`, `TASKLIST_TIMR_PASSWORD`, `SESSION_SECRET`

### Frontend Module Structure
- ES6 modules with explicit imports/exports
- Utility functions grouped by concern (time, DOM, state, etc.)
- Error handling centralized in `error-handler.js`
- State management for UI persistence in `state-management.js`

## Coding Conventions and Implementation Rules
- Follow established best practices: separation of concerns, encapsulation,
  extracting common functionality / modularization, and in general write maintainable
  code. Avoid duplicating logic and use properly tested common methods and functions
  instead. Leave modified code in a better state than it was before.
- When changing interfaces, update all callers, tests and relevant documentation.
- Remove or correct defective code instead of layering workarounds.
- Focus on identifying the root cause of problems; validate assumptions using tests and logging.
- Do not add production code solely to satisfy older tests. Update the tests
  instead so that they cover real production behaviour.
- When refactoring, remove obsolete comments. Avoid notes about where code used
  to live; keep the codebase clean and focused on its current structure.

### Error Handling Guidelines
- Use consistent error response formats from the backend to the frontend.
- Log all unexpected exceptions with enough context for debugging, but avoid logging sensitive data.
- Frontend should provide user-friendly error messages for common issues like network failures.
- The user should always be notified if something goes wrong.

### Python Coding Guidelines
- place imports at the beginning of the file, not somewhere inside methods

### JavaScript / HTML / CSS / Web
- Take great care to extract logic into helper methods or functions, and to move as
  many of such methods as possible into separate JavaScript modules to keep the
  actual browser scripts small.
- Do not parse your own web UI, especially not display texts! Pass or remember required
  data in more suitable ways like using specialised HTML elements, using Cookies or
  local storage.

## Dealing With Unexpected Application or Code Behaviour
- First make sure you really understand the occurring problem properly.
- Challenge and validate your assumptions. Is there really happening what you
  assume to happen? Incorrect assumptions about what is happening are a frequent
  reason for unexpected problems. Use additional tests and logging as required to
  confirm what's really happening.
- Assume external systems and services you need to interface with are working
  correctly according to the specification, unless you explicitly know otherwise.
  Do not create workaround code for hypothetical problems in other services which
  most likely don't exist.
- Always focus on identifying and resolving the root cause instead of adding
  “work-around code.” Such work-around code is nearly always the wrong approach
  and adds unnecessary complexity and maintenance issues.

### Security Considerations
- Session management with secure cookies
- Input sanitization and validation
- API credential protection via environment variables
- Secure file permissions on .env (600)
- Never expose API keys or tokens to the frontend.
- Sanitize all inputs from the frontend before using them in backend logic or requests.
- Avoid using `eval` or unsafe dynamic code execution in either frontend or backend.
- Enforce CORS policy and use HTTPS for all communication.
- Never log sensitive values like passwords or access tokens, mask them in log messages.

### Documentation
- The documentation should focus on the current state of the application - neither on
  a former state which no longer exists, nor on the current task which only matters at
  this moment, but not in the longer term.
- Important key points or new concepts need to be documented, but not every
  implementation detail. Documenting too many details soon will very soon lead to an
  outdated and inconsistent documentation, because you or someone else will forget
  to update it.
- Strive to keep the documentation up-to-date and relevant. Everytime you change
  something in the application, check if the documentation needs to be extended or
  updated.

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
