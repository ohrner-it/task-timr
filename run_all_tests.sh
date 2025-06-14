#!/bin/bash

# Activate Python virtual environment when available
if [ -d "venv" ]; then
    echo "Activating Python virtual environment..."
    if ! source venv/bin/activate; then
        echo "Failed to activate virtual environment" >&2
        exit 1
    fi
fi

# Run Python tests
echo "====================== Running Python Tests ======================"
python3 run_tests.py

PYTHON_TEST_RESULT=$?

# Run JavaScript tests from the frontend directory
echo "====================== Running JavaScript Tests ======================"
cd tests/frontend && npm test

JS_TEST_RESULT=$?

# Determine overall test results
if [ $PYTHON_TEST_RESULT -ne 0 ] || [ $JS_TEST_RESULT -ne 0 ]; then
    echo "Tests failed!"
    exit 1
else
    echo "All tests passed!"
    exit 0
fi
