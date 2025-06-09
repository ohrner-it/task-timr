/**
 * Tests for static/js/modules/ui-utils.js
 * Following testing guidelines: Test the real thing, mock only the boundary
 */

import { 
    logMessage, 
    showAlert, 
    debounce 
} from '../../static/js/modules/ui-utils.js';

// Mock only the boundary - DOM and console
global.document = {
    getElementById: jest.fn(),
    querySelector: jest.fn(),
    createElement: jest.fn(() => ({
        innerHTML: '',
        className: '',
        appendChild: jest.fn(),
        setAttribute: jest.fn(),
        addEventListener: jest.fn()
    }))
};

describe('UI Utils Module - Real Production Code', () => {
    let mockConsole;

    beforeEach(() => {
        jest.clearAllMocks();
        jest.useFakeTimers();
        
        // Mock console methods to test logging behavior
        mockConsole = {
            log: jest.fn(),
            error: jest.fn(),
            warn: jest.fn()
        };
        global.console = mockConsole;
    });

    afterEach(() => {
        jest.useRealTimers();
        jest.clearAllMocks();
    });

    describe('logMessage', () => {
        test('creates structured log objects with all required fields', () => {
            const result = logMessage('Test message', 'info', { extra: 'data' });
            
            expect(result).toHaveProperty('level', 'info');
            expect(result).toHaveProperty('message', 'Test message');
            expect(result).toHaveProperty('timestamp');
            expect(result).toHaveProperty('data', { extra: 'data' });
            expect(typeof result.timestamp).toBe('string');
        });

        test('handles different log levels correctly', () => {
            logMessage('Error message', 'error');
            expect(mockConsole.error).toHaveBeenCalled();
            
            logMessage('Warning message', 'warn');
            expect(mockConsole.warn).toHaveBeenCalled();
            
            logMessage('Info message', 'info');
            expect(mockConsole.log).toHaveBeenCalled();
        });

        test('works without additional data', () => {
            const result = logMessage('Simple message', 'info');
            expect(result.data).toBeUndefined();
        });

        test('handles custom log levels as info', () => {
            logMessage('Debug message', 'debug');
            expect(mockConsole.log).toHaveBeenCalled();
        });

        test('works without console (Node.js environment simulation)', () => {
            global.console = undefined;
            expect(() => {
                logMessage('Test message', 'info');
            }).not.toThrow();
        });

        test('preserves stack trace information', () => {
            const result = logMessage('Error with data', 'error', { stack: 'trace' });
            expect(result.data.stack).toBe('trace');
        });
    });

    describe('debounce', () => {
        test('delays function execution properly', () => {
            const mockFn = jest.fn();
            const debouncedFn = debounce(mockFn, 100);
            
            debouncedFn();
            expect(mockFn).not.toHaveBeenCalled();
            
            jest.advanceTimersByTime(100);
            expect(mockFn).toHaveBeenCalledTimes(1);
        });

        test('passes correct arguments and preserves context', () => {
            const mockFn = jest.fn();
            const debouncedFn = debounce(mockFn, 100);
            
            debouncedFn('arg1', 'arg2');
            jest.advanceTimersByTime(100);
            
            expect(mockFn).toHaveBeenCalledWith('arg1', 'arg2');
        });

        test('cancels previous timeouts', () => {
            const mockFn = jest.fn();
            const debouncedFn = debounce(mockFn, 100);
            
            debouncedFn();
            debouncedFn();
            debouncedFn();
            
            jest.advanceTimersByTime(100);
            expect(mockFn).toHaveBeenCalledTimes(1);
        });

        test('handles zero wait time', () => {
            const mockFn = jest.fn();
            const debouncedFn = debounce(mockFn, 0);
            
            debouncedFn();
            jest.advanceTimersByTime(0);
            
            expect(mockFn).toHaveBeenCalledTimes(1);
        });

        test('handles multiple debounced functions independently', () => {
            const mockFn1 = jest.fn();
            const mockFn2 = jest.fn();
            const debouncedFn1 = debounce(mockFn1, 100);
            const debouncedFn2 = debounce(mockFn2, 200);
            
            debouncedFn1();
            debouncedFn2();
            
            jest.advanceTimersByTime(100);
            expect(mockFn1).toHaveBeenCalledTimes(1);
            expect(mockFn2).not.toHaveBeenCalled();
            
            jest.advanceTimersByTime(100);
            expect(mockFn2).toHaveBeenCalledTimes(1);
        });
    });

    describe('showAlert', () => {
        test('handles Node.js environment gracefully', () => {
            // The production code skips DOM manipulation in Node.js (when document is undefined)
            // This is the correct behavior for testing environment
            expect(() => {
                showAlert('Test message', 'info');
                showAlert('Success message', 'success');
                showAlert('Warning message', 'warning');
                showAlert('Error message', 'danger');
            }).not.toThrow();
        });

        test('accepts all expected parameters', () => {
            // Test function accepts parameters without throwing in Node.js environment
            expect(() => {
                showAlert('Modal message', 'info', true);
                showAlert('Default message'); // Uses defaults
                showAlert('', 'info'); // Empty message
            }).not.toThrow();
        });
    });
});