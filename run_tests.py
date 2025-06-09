#!/usr/bin/env python3
"""
Test runner script for Task Timr

This script runs all available Python tests for the application.
For JavaScript tests, use npm test separately from the tests/frontend directory.

Copyright (c) 2025 Ohrner IT GmbH
Licensed under the MIT License
"""

import unittest
import sys
import logging

# Configure logging for tests
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    # Discover and run all tests
    test_suite = unittest.defaultTestLoader.discover("tests", pattern="test_*.py")
    
    # Run the tests
    test_runner = unittest.TextTestRunner(verbosity=2)
    result = test_runner.run(test_suite)
    
    # Exit with non-zero code if tests failed
    sys.exit(not result.wasSuccessful())