# Testing Guide for Task Timr

This comprehensive guide explains how to run, extend, and maintain the test suite for Task Timr, following established testing principles and naming conventions.

## Ten Laws for Unit Tests

Our testing philosophy follows these fundamental principles:

1. **Test the real thing.**
   Call production code—not copies, not helper facades—and assert on its *observable* outputs or side-effects.
2. **One reason to fail.**
   Structure each test around a single behaviour or branch (Arrange → Act → Assert). Multiple assertions are fine if they cover the same concept.
3. **Mock only the boundary, never the subject.**
   Stub or mock *external* collaborators you don’t control (DB, message bus, HTTP service), but never the class or function under test.
4. **Don’t re-implement logic in the test.**
   Hard-code simple inputs and the expected result; duplicating algorithms inside the test just hides bugs.
5. **Keep tests independent and stateless.**
   No shared globals, singletons, or reused objects across test cases; reset or re-create fresh fixtures every run.
6. **Fail fast, diagnostically.**
   A failing assertion must read like an error message a human can act on instantly—avoid cryptic comparisons or large diffs.
7. **Adapt the test, not the production code.**
   If a deliberate refactor breaks a test, fix the test. Add logic to production code *only* when it serves real behaviour, never as a shim to appease a test.
8. **Be deterministic and fast.**
   Eliminate randomness, real time, network, and file-system dependencies; aim for sub-second execution so the suite can be run constantly.
9. **Cover contracts, not percentages.**
   Strive for meaningful paths and edge cases; 100 % line-coverage is worthless if assertions are superficial or completely missing.
10. **Validate external-system assumptions separately.**
    Write contract/integration tests against a real instance, container, or contract verifier to ensure your mocks reflect reality.

## Test Structure and Naming Conventions

### Python Test Files

Follow the file name pattern: `test_<module_under_test>[_<specific_test_topic>].py`

Examples:
- `test_app.py` - Main application module tests
- `test_app_endpoints.py` - Specific focus on API endpoints
- `test_timr_api.py` - Timr API client tests
- `test_timr_utils.py` - Utility classes and helpers
- `test_config.py` - Configuration tests

### JavaScript Test Files

Follow the file name pattern: `<module_under_test>.test.js`

Examples:
- `time-utils.test.js` - Time parsing and formatting functions
- `duration-parser.test.js` - Duration input parsing
- `project-time-handler.test.js` - Project time management
- `integration.test.js` - Integration workflows

### Documentation Guidelines for Tests

1. **Keep documentation in test files**: Write detailed docstrings and comments within test files where they're more likely to stay current
2. **Avoid listing specific test files in guides**: File names change, but patterns and principles remain stable
3. **Focus on structure and principles**: Document how to understand and extend the test system rather than cataloging current files
4. **Use examples over exhaustive lists**: Show the pattern with a few examples rather than complete inventories

## Overview

The test suite consists of six main components:

1. **Backend CRUD Operations Tests**: Tests for the `ProjectTimeConsolidator` class CRUD methods
2. **Incremental Update Tests**: Tests for the differential update logic and performance optimizations
3. **API Endpoint Tests**: Tests for the Flask API endpoints that handle UI project times
4. **Frontend Module Tests**: Tests for individual JavaScript modules following the Ten Laws
5. **Duration Parsing Tests**: Tests for user input validation and Jira-style duration parsing
6. **Integration Tests**: Tests against the real Timr.com API service


## Integration Testing with Real APIs

Integration tests verify that our implementation works correctly with the actual Timr.com API service, rather than relying solely on mocked responses.

### Why Integration Tests Matter

Unit tests with mocks are useful for testing code in isolation, but they rely on assumptions about external API behavior. Integration tests help us:

1. **Verify API understanding**: Test how the API actually behaves, not assumptions
2. **Detect breaking changes**: Catch when Timr.com updates their API
3. **Test edge cases**: Discover real API behavior with overlapping times, boundary conditions
4. **Validate implementation**: Ensure code works with the live service

### Running Integration Tests

**WARNING**: Integration tests make real changes to your Timr.com account! They create and delete working times and project times. The tests use yesterday's date to avoid conflicts and stay within API restrictions, but use with caution.

1. Set environment variables for Timr.com credentials:
   ```bash
   export TIMR_USER=your_username
   export TIMR_PASSWORD=your_password
   ```

2. Run integration tests:
   ```bash
   python -m unittest test_timr_api_integration.py
   ```

### Integration Test Coverage

Integration tests cover the full lifecycle:
- **Authentication**: Login with valid and invalid credentials  
- **Working Times**: Complete CRUD operations
- **Tasks**: Retrieval and search functionality
- **Project Times**: Complete CRUD operations
- **Edge Cases**: Overlapping times, out-of-bounds scenarios

### Key API Behavior Findings

Integration tests reveal actual Timr.com API behavior in edge cases:
- Whether overlapping working times are allowed or rejected
- How overlapping project times are handled
- Whether project times can exist outside their working time boundaries

These findings are crucial for implementation decisions and error handling.

## Running Backend Tests

### Running All Python Tests

```bash
python -m unittest discover tests
```

### Running Specific Test Modules

Run tests for specific modules using the naming pattern:

```bash
# Core application tests
python -m unittest test_app_comprehensive.py

# API endpoint tests  
python -m unittest test_app_endpoints.py

# Utility function tests
python -m unittest test_timr_utils.py

# Integration tests
python -m unittest test_timr_api_integration.py
```

### Running Tests by Category

```bash
# All app-related tests
python -m unittest discover tests -p "test_app*.py"

# All timr API tests
python -m unittest discover tests -p "test_timr*.py"

# All integration tests
python -m unittest discover tests -p "*integration*.py"
```

## Running Frontend Tests

### Running All JavaScript Tests

```bash
npm test
```

### Running Specific Test Suites

Run frontend tests for specific modules:

```bash
npm test time-utils.test.js
npm test duration-parser.test.js
npm test project-time-handler.test.js
npm test integration.test.js
```

### Running Tests with Coverage

```bash
npm run test:coverage
```

## Checking Coverage

**Python Tests:**
```bash
pip install coverage
coverage run -m unittest discover
coverage report
coverage html  # Generate HTML report
```

**JavaScript Tests:**
```bash
npm run test:all  # Includes coverage report
```

### Current Coverage Metrics

| Component | Coverage | Critical Areas |
|-----------|----------|----------------|
| Incremental Updates | 90%+ | ✅ Differential logic |
| Duration Parsing | 95%+ | ✅ User input validation |
| CRUD Operations | 85%+ | ✅ Core functionality |
| API Endpoints | 80%+ | ✅ Error handling |
| Frontend Workflows | 75%+ | ✅ User interactions |

## Testing Principles in Practice

### Backend Testing Approach

**Following Law #1 (Test the real thing):**
- Tests use actual `ProjectTimeConsolidator` instances
- Real API response structures from Timr.com
- Authentic data flows through the system

**Following Law #3 (Mock only the boundary):**
- Mock external Timr API calls
- Mock Flask request contexts
- Don't mock internal application logic

**Example:**
```python
@patch('timr_api.TimrApi._request')
def test_consolidate_project_times_real_logic(self, mock_request):
    # Mock only the external API boundary
    mock_request.return_value = real_timr_response_data
    
    # Test the real consolidation logic
    consolidator = ProjectTimeConsolidator(self.mock_api)
    result = consolidator.consolidate_project_times(working_time)
    
    # Verify real behavior
    self.assertEqual(len(result), expected_count)
```

### Frontend Testing Approach

**Following Law #1 (Test the real thing):**
- Import and test actual production modules
- Use real function implementations
- Test with authentic data structures

**Following Law #3 (Mock only the boundary):**
- Mock localStorage and DOM APIs
- Mock fetch calls to backend
- Don't mock the JavaScript functions being tested

**Example:**
```javascript
// Import REAL production modules
import { parseTimeToMinutes } from '../../static/js/modules/time-utils.js';

// Mock only the boundary (localStorage)
global.localStorage = { /* mock implementation */ };

describe('Time Parsing - Real Implementation', () => {
    test('parseTimeToMinutes handles standard time format', () => {
        // Test the real function with real data
        expect(parseTimeToMinutes('14:30')).toBe(870);
    });
});
```

## Extending the Tests

### Adding Backend Tests

When adding new backend functionality, create or extend test files following the naming convention:

1. **Identify the module under test** (e.g., `app.py`, `timr_api.py`, `timr_utils.py`)
2. **Create or extend the corresponding test file** (e.g., `test_app_*.py`, `test_timr_api_*.py`)
3. **Follow established patterns** for mocking external dependencies
4. **Test both success and error scenarios**
5. **Use descriptive test method names** that explain the scenario

### Adding Frontend Tests

When adding frontend functionality:

1. **Identify the JavaScript module under test** 
2. **Create or extend the corresponding test file** (e.g., `module-name.test.js`)
3. **Import and test real production code** following the Ten Laws
4. **Mock only external boundaries** (DOM, localStorage, fetch calls)
5. **Test user interaction workflows and error states**

### Test Development Guidelines

1. **Write descriptive test names** that explain the scenario being tested
2. **Use realistic test data** that mirrors production scenarios
3. **Test error conditions** as thoroughly as success cases
4. **Keep tests focused** - one behavior per test method
5. **Use setup and teardown** to maintain test independence
6. **Document complex test scenarios** with inline comments

## Debugging Tests

### Common Issues and Solutions

**Python Test Issues:**
- Import errors: Check module paths and PYTHONPATH
- Mock failures: Verify mock target paths match actual imports
- Database errors: Ensure test database is properly configured

**JavaScript Test Issues:**
- Module import errors: Check Jest configuration and file paths
- DOM-related failures: Verify jsdom setup in test environment
- Async test failures: Use proper async/await or done() callbacks

### Debugging Commands

**Run specific test with verbose output:**
```bash
python -m unittest tests.test_module_name.TestClassName.test_method_name -v
```

**Run JavaScript tests in debug mode:**
```bash
npm test -- --verbose
```

## Integration with Development Workflow

### Pre-commit Testing

Run the test suite before committing changes:

```bash
# Run all Python tests
python -m unittest discover tests

# Run all JavaScript tests
npm test

# Check coverage
coverage run -m unittest discover && coverage report
npm run test:coverage
```

### Continuous Integration

The test suite is designed to run in CI environments:

- All tests are independent and can run in parallel
- No external dependencies beyond the test environment
- Deterministic results across different environments
- Comprehensive coverage reporting

## Best Practices

1. **Follow the Ten Laws** consistently across all tests
2. **Use the established naming conventions** for new test files
3. **Test real production code paths** rather than simplified versions
4. **Mock external dependencies** but not internal application logic
5. **Write tests that document expected behavior** through clear assertions
6. **Maintain test quality** with the same rigor as production code
7. **Keep tests fast** to encourage frequent execution
8. **Use meaningful test data** that represents real usage scenarios

This testing guide ensures consistent, reliable, and maintainable test coverage across the entire Task Timr application.