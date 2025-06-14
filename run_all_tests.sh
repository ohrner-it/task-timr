#!/bin/bash

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
