/**
 * Jest setup file for frontend tests
 * This file sets up the testing environment and global mocks
 */

// Mock Bootstrap Modal for tests that need it
global.bootstrap = {
    Modal: {
        getInstance: jest.fn(() => ({
            hide: jest.fn(),
            show: jest.fn()
        }))
    }
};

// Mock fetch globally
global.fetch = jest.fn();

// Suppress console.log during tests unless explicitly needed
const originalConsoleLog = console.log;
const originalConsoleError = console.error;

// Only show console output in tests when DEBUG_TESTS environment variable is set
if (!process.env.DEBUG_TESTS) {
    console.log = jest.fn();
    console.error = jest.fn();
}

// Note: beforeEach will be called within individual test files

// Console methods will be restored in individual test files if needed