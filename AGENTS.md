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
1. **Requirements Clarification**: If the task is not fully clear or is lacking relevant information, please ask back
   and obtain this information before starting the task. You may suggest solutions,
   but also let the user confirm them.

2. **Deep Planning and Architecture Analysis**: Before writing any code, think deep and thoroughly analyze the requirements and existing codebase:
   - **Question fundamental assumptions**: Don't just improve implementations - 
     question whether operations are necessary at all. Ask "Why does this need 
     to exist?" and "Is this data already available elsewhere?"
   - **Challenge existing implementations**: If modifying existing code, critically examine 
     whether the current approach is architecturally sound or needs redesign.
   - **Analyze data flow**: Trace where required data originates and how it flows through 
     the system. Avoid duplicating data or creating unnecessary transformations.
   - **Identify anti-patterns**: Look for GUI parsing, redundant calculations, DOM mining, 
     or format dancing. Plan to eliminate these completely, not improve them.
   - **Design the target architecture**: Plan a clean solution that works with structured 
     data from its source, follows separation of concerns, and avoids problematic patterns.
   - **Validate approach**: Ensure the planned solution aligns with the project's 
     architectural principles and doesn't introduce technical debt.

3. **Test Driven Development**: Write or adapt tests first, then implement the
   desired functionality. Tests must follow the target architecture from step 2.

4. **Implementation**: Implement the solution according to the plan from step 2.

5. **Test Execution**: Run all tests before committing. The recommended command is:
   ```bash
   ./run_all_tests.sh
   ```
   This executes Python tests via `python3 run_tests.py` and JavaScript tests via
   `npm test` in `tests/frontend`.
   - Integration tests that talk to the real Timr.com API are required when adding
     or adjusting code that interacts with external services.
   - ALL tests MUST finish successfully before any modifications are allowed to
     be committed.

6. **Independent Critical Review**: Use a subagent to perform an independent, constructive 
   review of all changes:
   - The subagent must critically examine both the implementation and the underlying 
     architectural decisions from step 2.
   - The review should validate that the solution eliminates anti-patterns completely 
     and follows sound architectural principles.
   - The subagent should question whether the implemented approach makes fundamental sense 
     and suggest improvements for overall software quality.
   - If the review identifies violations of guidelines, anti-patterns, or fundamental 
     architectural issues, **go back to step 2 (Planning)** and restart the process.
   - Only proceed if the review confirms the solution follows all project guidelines 
     and represents a high-quality, maintainable implementation.

7. **Documentation Maintenance**: Refrain from creating new documentation files which in detail describe the
   changes performed for the current task. Such documentation files serve no
   long-term purpose, clutter the documentation folder and get obsolete nearly
   immediately. See the instructions on how to update the documentation below.

### Subagent Review Instructions
When requesting a subagent review, provide these specific instructions:

```
Perform a constructive, critical review of the implemented changes with the goal of improving overall software quality. Your review should:

1. **Architectural Validation**: 
   - Examine whether the fundamental approach makes sense
   - Verify that anti-patterns (GUI parsing, DOM mining, redundant calculations, format dancing) have been completely eliminated
   - Check that the solution works with structured data from its source

2. **Code Quality Assessment**:
   - Verify adherence to project coding guidelines and conventions
   - Check for proper separation of concerns and encapsulation
   - Ensure tests follow the "Ten Laws for Unit Tests" and test real production code

3. **Implementation Review**:
   - Validate that deprecated code and tests have been completely removed
   - Check for proper error handling and edge case coverage
   - Verify that changes don't introduce technical debt or workarounds

4. **Recommendations**:
   - Provide specific, actionable feedback for any issues found
   - Suggest improvements for maintainability and code quality
   - If fundamental issues exist, recommend returning to the planning phase

Be constructively critical - the goal is to ensure high-quality, maintainable code that follows architectural best practices.
```

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

## Data Flow and Architecture Validation

When implementing or modifying functionality, always analyze the complete data flow:

### Data Flow Analysis Checklist
- **Trace data origins**: Where does the required data originate? (Backend API, user input, calculated values)
- **Identify data transformations**: How is data transformed as it flows through the system?
- **Avoid data duplication**: Don't extract, parse, or derive data that's already available in structured form
- **Question necessity**: Before implementing data extraction or parsing, verify the data isn't already accessible

### Common Anti-Patterns to Avoid
- **GUI Parsing**: Never parse your own display text to extract data - use the original data source
- **Redundant Calculations**: Don't recalculate values that are already computed and available
- **DOM Mining**: Don't query DOM elements to extract data that should be passed as parameters
- **Format Dancing**: Don't convert structured data to text and then parse it back to structure

### Architecture Decision Questions
Before implementing any data processing logic, ask:
1. "Is this data already available in the application state?"
2. "Can I access this data directly from its source instead of deriving it?"
3. "Am I creating unnecessary dependencies on UI structure?"
4. "Will this break if the UI display format changes?"

## Development Patterns

### Testing Philosophy
- All tests must adhere to the "Ten Laws for Unit Tests" defined in the
  [Testing Guide](doc/README.Testing%20Guide.md).
- **Deprecated Code Elimination**: When refactoring to remove anti-patterns or 
  deprecated functionality:
  - **Remove deprecated tests completely** - don't maintain parallel test suites
  - **Eliminate fallback code paths** - don't test "backwards compatibility" for 
    problematic patterns
  - **Test the new implementation only** - focus tests on the correct approach
  - **Verify complete removal** - ensure no traces of deprecated patterns remain
- **Clean Refactoring Strategy**:
  - Write tests for the target architecture first
  - Remove deprecated code and tests in the same commit
  - Ensure tests fail if deprecated patterns are reintroduced
  - Don't maintain "transitional" code that supports both old and new approaches
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
- **Do not parse your own web UI, especially not display texts!** Pass or remember 
  required data in more suitable ways like using specialised HTML elements, using 
  Cookies or local storage.
- **Data Flow Principle**: Always work with structured data objects from their 
  source rather than extracting data from DOM elements or display text. If you 
  need data for calculations, pass it as function parameters or access it from 
  application state.
- **Question Data Extraction**: Before implementing any text parsing or DOM 
  querying to extract data, verify that the data isn't already available in a 
  structured format from the backend response or application state.

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
