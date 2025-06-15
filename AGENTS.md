# Instructions for Developers and AI Agents

Task Timr is an alternative web frontend for the Timr.com time tracking service.
For an overview see the README.

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

## Development Workflow
- Use **test driven development**. Write or adapt tests first, then implement the
  desired functionality.
- Run all tests before committing. The recommended command is:
  ```bash
  ./run_all_tests.sh
  ```
  This executes Python tests via `python3 run_tests.py` and JavaScript tests via
  `npm test` in `tests/frontend`.
  - Integration tests that talk to the real Timr.com API are required when adding
    or adjusting code that interacts with external services.

## Testing Guidelines
- Follow the **Test Structure and Naming Conventions** from the Testing Guide.
  Each Python module should have its own test file named
  `test_<module_under_test>[_<specific_test_topic>].py`.
- Keep unrelated tests in separate modules. Do not combine tests for different
  production modules in one file and avoid renaming test modules without a
  compelling reason.
- Avoid redundant test classes; each test class should have a clear, unique purpose.
- JavaScript tests belong in files following the pattern
  `<module_under_test>.test.js`.

## How to Deal With Unexpected Application or Code Behaviour
- First make sure you really understand the problem properly.
- Challenge and validate your assumptions. Is there really happening what you assume to happen? Incorrect assumptions about what is happening are a frequent reason for unexpected problems. Tests and logging can be used to confirm what's really happening.
- Assume external systems and services you need to interface with are working correctly according to the specification, unless you explicitly know otherwise. Do not create workaround code for hypothetical problems in other services which most likely don't exist.
- Always focus on identifying and resolving the root cause instead of adding “work-around code.” Such work-around code is nearly always the wrong approach and adds unnecessary complexity and maintenance issues.

## Code Quality
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

## Commit and PR Guidelines
- Use concise commit messages: a single short summary line, followed by an empty
  line and optional details.
- Ensure the repository is in a clean state and all tests pass before creating a
  pull request.
- Pull request descriptions should summarise **all** changes contained in the
  pull request and mention the test results.
