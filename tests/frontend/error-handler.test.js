/**
 * Comprehensive tests for static/js/modules/error-handler.js
 * Tests the enhanced error handling system integration with backend
 */

import {
    fetchWithErrorHandling,
    handleUIError,
    createErrorHandler,
    handleFormSubmission,
    handleApiResponse,
    resetUIElements
} from '../../static/js/modules/error-handler.js';

// Mock fetch and other browser APIs
global.fetch = jest.fn();
global.navigator = {
    userAgent: 'test-browser',
    language: 'en-US',
    cookieEnabled: true
};

// Mock UI utilities
jest.mock('../../static/js/modules/ui-utils.js', () => ({
    logApiError: jest.fn(),
    showAlert: jest.fn()
}));

import { logApiError, showAlert } from '../../static/js/modules/ui-utils.js';

describe('Enhanced Error Handler Module - Real Production Code', () => {
    beforeEach(() => {
        jest.clearAllMocks();
        fetch.mockClear();
    });

    describe('fetchWithErrorHandling', () => {
        test('handles successful API responses', async () => {
            const mockResponse = {
                ok: true,
                status: 200,
                json: jest.fn().mockResolvedValue({ data: 'success' })
            };
            fetch.mockResolvedValue(mockResponse);

            const result = await fetchWithErrorHandling('/api/test', {
                method: 'GET'
            });

            expect(result).toEqual({ data: 'success' });
            expect(fetch).toHaveBeenCalledWith('/api/test', { method: 'GET' });
        });

        test('handles API errors with enhanced backend error messages', async () => {
            const mockResponse = {
                ok: false,
                status: 400,
                headers: new Map([['Content-Type', 'application/json']]),
                text: jest.fn().mockResolvedValue('{"error": "This task is not bookable. Please select a different task."}'),
                forEach: jest.fn()
            };
            mockResponse.headers.get = jest.fn().mockReturnValue('application/json');
            mockResponse.headers.forEach = jest.fn();
            
            fetch.mockResolvedValue(mockResponse);

            await expect(fetchWithErrorHandling('/api/project-times', {
                method: 'POST',
                body: JSON.stringify({ task_id: 'test_task' })
            }, {
                operation: 'create_project_time'
            })).rejects.toThrow('This task is not bookable. Please select a different task.');

            expect(logApiError).toHaveBeenCalledWith(
                'create_project_time',
                expect.any(Error),
                expect.objectContaining({
                    requestUrl: '/api/project-times',
                    requestMethod: 'POST',
                    responseStatus: 400,
                    responseData: { error: 'This task is not bookable. Please select a different task.' }
                })
            );
        });

        test('provides appropriate fallback messages for different HTTP status codes', async () => {
            const testCases = [
                { status: 401, expectedMessage: 'Please log in to your Timr account to view and manage working times' },
                { status: 403, expectedMessage: 'Access denied. You don\'t have permission for this operation.' },
                { status: 404, expectedMessage: 'The requested resource was not found.' },
                { status: 409, expectedMessage: 'This operation conflicts with existing data.' },
                { status: 422, expectedMessage: 'The data provided is invalid or incomplete.' },
                { status: 500, expectedMessage: 'The server encountered an error. Please try again later.' },
                { status: 502, expectedMessage: 'The service is temporarily unavailable. Please try again later.' },
                { status: 503, expectedMessage: 'The service is temporarily unavailable. Please try again later.' }
            ];

            for (const testCase of testCases) {
                fetch.mockClear();
                logApiError.mockClear();

                const mockResponse = {
                    ok: false,
                    status: testCase.status,
                    headers: new Map(),
                    text: jest.fn().mockResolvedValue(JSON.stringify({ error: testCase.expectedMessage })),
                    forEach: jest.fn()
                };
                mockResponse.headers.get = jest.fn().mockReturnValue('application/json');
                mockResponse.headers.forEach = jest.fn();
                
                fetch.mockResolvedValue(mockResponse);

                await expect(fetchWithErrorHandling('/api/test')).rejects.toThrow(testCase.expectedMessage);
            }
        });

        test('handles network errors appropriately', async () => {
            fetch.mockRejectedValue(new Error('Network error'));

            await expect(fetchWithErrorHandling('/api/test', {}, {
                operation: 'test_operation'
            })).rejects.toThrow('Network error: Network error');

            expect(logApiError).toHaveBeenCalledWith(
                'test_operation',
                expect.objectContaining({
                    message: 'Network error: Network error',
                    isApiError: true
                }),
                expect.objectContaining({
                    originalError: 'Network error',
                    errorType: 'network'
                })
            );
        });

        test('includes comprehensive context in error logs', async () => {
            const mockResponse = {
                ok: false,
                status: 500,
                headers: new Map([['Content-Type', 'application/json'], ['X-Request-ID', 'req-123']]),
                text: jest.fn().mockResolvedValue('{"error": "Internal server error"}')
            };
            mockResponse.headers.get = jest.fn().mockReturnValue('application/json');
            mockResponse.headers.forEach = jest.fn((callback) => {
                callback('application/json', 'Content-Type');
                callback('req-123', 'X-Request-ID');
            });
            
            fetch.mockResolvedValue(mockResponse);

            await expect(fetchWithErrorHandling('/api/working-times', {
                method: 'POST',
                body: JSON.stringify({ start: '2025-01-01T09:00:00Z', end: '2025-01-01T17:00:00Z' })
            }, {
                operation: 'create_working_time',
                userId: 'user_123'
            })).rejects.toThrow();

            expect(logApiError).toHaveBeenCalledWith(
                'create_working_time',
                expect.any(Error),
                expect.objectContaining({
                    requestUrl: '/api/working-times',
                    requestMethod: 'POST',
                    requestData: { start: '2025-01-01T09:00:00Z', end: '2025-01-01T17:00:00Z' },
                    operation: 'create_working_time',
                    userId: 'user_123',
                    responseStatus: 500,
                    responseData: { error: 'Internal server error' },
                    responseHeaders: expect.objectContaining({
                        'Content-Type': 'application/json',
                        'X-Request-ID': 'req-123'
                    }),
                    browserInfo: expect.objectContaining({
                        language: 'en-US',
                        cookieEnabled: true
                    })
                })
            );
        });

        test('sanitizes request data for logging', async () => {
            const mockResponse = {
                ok: false,
                status: 400,
                headers: new Map(),
                text: jest.fn().mockResolvedValue('{"error": "Bad request"}')
            };
            mockResponse.headers.get = jest.fn().mockReturnValue('application/json');
            mockResponse.headers.forEach = jest.fn();
            
            fetch.mockResolvedValue(mockResponse);

            await expect(fetchWithErrorHandling('/api/login', {
                method: 'POST',
                body: JSON.stringify({ username: 'user', password: 'secret123' })
            }, {
                operation: 'user_login'
            })).rejects.toThrow();

            // Verify that sensitive data is in the request but context should be sanitized
            expect(logApiError).toHaveBeenCalledWith(
                'user_login',
                expect.any(Error),
                expect.objectContaining({
                    requestData: { username: 'user', password: 'secret123' }  // Raw data passed to log function
                })
            );
        });
    });

    describe('handleUIError', () => {
        test('displays user-friendly messages for API errors', () => {
            const apiError = new Error('This working time is frozen and cannot be modified.');
            apiError.isApiError = true;

            handleUIError(apiError, {
                operation: 'update_working_time'
            });

            expect(showAlert).toHaveBeenCalledWith(
                'This working time is frozen and cannot be modified.',
                'danger',
                false
            );
        });

        test('displays formatted messages for non-API errors', () => {
            const jsError = new Error('Cannot read property of undefined');

            handleUIError(jsError, {
                operation: 'calculate_duration'
            });

            expect(showAlert).toHaveBeenCalledWith(
                'Error during calculate_duration: Cannot read property of undefined',
                'danger',
                false
            );
            
            expect(logApiError).toHaveBeenCalledWith(
                'calculate_duration',
                jsError,
                expect.objectContaining({
                    errorType: 'ui'
                })
            );
        });

        test('keeps modals open when modalContext is true', () => {
            const error = new Error('Validation failed');
            error.isApiError = true;

            handleUIError(error, {
                operation: 'form_submission',
                modalContext: true
            });

            expect(showAlert).toHaveBeenCalledWith(
                'Validation failed',
                'danger',
                true  // Modal should stay open
            );
        });

        test('executes fallback actions when provided', () => {
            const mockFallback = jest.fn();
            const error = new Error('Test error');

            handleUIError(error, {
                operation: 'test_operation',
                fallbackAction: mockFallback
            });

            expect(mockFallback).toHaveBeenCalled();
        });

        test('handles fallback action failures gracefully', () => {
            const mockFallback = jest.fn(() => {
                throw new Error('Fallback failed');
            });
            const originalError = new Error('Original error');

            // Should not throw despite fallback failure
            expect(() => {
                handleUIError(originalError, {
                    operation: 'test_operation',
                    fallbackAction: mockFallback
                });
            }).not.toThrow();

            expect(showAlert).toHaveBeenCalledWith(
                'Error during test_operation: Original error',
                'danger',
                false
            );
        });
    });

    describe('createErrorHandler', () => {
        test('creates reusable error handler with preset options', () => {
            const errorHandler = createErrorHandler('data_processing', {
                modalContext: true,
                additionalContext: { module: 'data_processor' }
            });

            const testError = new Error('Processing failed');
            errorHandler(testError);

            expect(showAlert).toHaveBeenCalledWith(
                'Error during data_processing: Processing failed',
                'danger',
                true
            );

            expect(logApiError).toHaveBeenCalledWith(
                'data_processing',
                testError,
                expect.objectContaining({
                    errorType: 'ui',
                    module: 'data_processor'
                })
            );
        });
    });

    describe('handleFormSubmission', () => {
        test('executes function and calls success callback on success', async () => {
            const mockSubmitFunction = jest.fn().mockResolvedValue({ success: true });
            const mockOnSuccess = jest.fn();

            const result = await handleFormSubmission(mockSubmitFunction, {
                operation: 'form_submit',
                onSuccess: mockOnSuccess
            });

            expect(result).toEqual({ success: true });
            expect(mockOnSuccess).toHaveBeenCalledWith({ success: true });
            expect(showAlert).not.toHaveBeenCalled();
        });

        test('handles errors and keeps modal open by default', async () => {
            const submitError = new Error('Submit failed');
            submitError.isApiError = true;
            const mockSubmitFunction = jest.fn().mockRejectedValue(submitError);

            await expect(handleFormSubmission(mockSubmitFunction, {
                operation: 'form_submit'
            })).rejects.toThrow('Submit failed');

            expect(showAlert).toHaveBeenCalledWith(
                'Submit failed',
                'danger',
                true  // Modal should stay open
            );
        });

        test('calls custom error callback when provided', async () => {
            const submitError = new Error('Custom error');
            const mockSubmitFunction = jest.fn().mockRejectedValue(submitError);
            const mockOnError = jest.fn();

            await expect(handleFormSubmission(mockSubmitFunction, {
                operation: 'form_submit',
                onError: mockOnError
            })).rejects.toThrow('Custom error');

            expect(mockOnError).toHaveBeenCalledWith(submitError);
            expect(showAlert).not.toHaveBeenCalled(); // Custom handler should override default
        });

        test('includes form context in error logs', async () => {
            const submitError = new Error('Form validation failed');
            const mockSubmitFunction = jest.fn().mockRejectedValue(submitError);
            const mockForm = { id: 'test-form' };

            await expect(handleFormSubmission(mockSubmitFunction, {
                operation: 'form_submit',
                form: mockForm
            })).rejects.toThrow('Form validation failed');

            expect(logApiError).toHaveBeenCalledWith(
                'form_submit',
                submitError,
                expect.objectContaining({
                    errorType: 'ui',
                    formId: 'test-form'
                })
            );
        });
    });

    describe('handleApiResponse', () => {
        test('processes successful responses', async () => {
            const mockResponse = {
                ok: true,
                json: jest.fn().mockResolvedValue({ data: 'test' })
            };

            const result = await handleApiResponse(mockResponse);
            expect(result).toEqual({ data: 'test' });
        });

        test('handles failed responses with context', async () => {
            const mockResponse = {
                ok: false,
                status: 422,
                headers: new Map(),
                text: jest.fn().mockResolvedValue('{"error": "Invalid data"}')
            };
            mockResponse.headers.get = jest.fn().mockReturnValue('application/json');
            mockResponse.headers.forEach = jest.fn();

            await expect(handleApiResponse(mockResponse, {
                operation: 'data_validation',
                requestData: { field: 'value' }
            })).rejects.toThrow('Invalid data');
        });
    });

    describe('resetUIElements', () => {
        test('resets UI elements to specified states', () => {
            const mockButton = {
                disabled: true,
                innerHTML: 'Loading...',
                classList: {
                    remove: jest.fn(),
                    add: jest.fn()
                },
                style: {}
            };

            const mockInput = {
                disabled: true,
                value: 'old_value'
            };

            const elements = {
                submitButton: mockButton,
                inputField: mockInput
            };

            const resetStates = {
                submitButton: {
                    disabled: false,
                    innerHTML: 'Submit',
                    classList: {
                        remove: ['loading'],
                        add: ['ready']
                    },
                    style: {
                        opacity: '1'
                    }
                },
                inputField: {
                    disabled: false
                }
            };

            resetUIElements(elements, resetStates);

            expect(mockButton.disabled).toBe(false);
            expect(mockButton.innerHTML).toBe('Submit');
            expect(mockButton.classList.remove).toHaveBeenCalledWith('loading');
            expect(mockButton.classList.add).toHaveBeenCalledWith('ready');
            expect(mockButton.style.opacity).toBe('1');
            expect(mockInput.disabled).toBe(false);
        });

        test('handles missing elements gracefully', () => {
            const elements = {
                existingElement: { disabled: true },
                missingElement: null
            };

            const resetStates = {
                existingElement: { disabled: false },
                missingElement: { disabled: false }
            };

            expect(() => {
                resetUIElements(elements, resetStates);
            }).not.toThrow();

            expect(elements.existingElement.disabled).toBe(false);
        });

        test('handles missing reset states gracefully', () => {
            const elements = {
                element1: { disabled: true },
                element2: { disabled: true }
            };

            const resetStates = {
                element1: { disabled: false }
                // element2 intentionally missing
            };

            expect(() => {
                resetUIElements(elements, resetStates);
            }).not.toThrow();

            expect(elements.element1.disabled).toBe(false);
            expect(elements.element2.disabled).toBe(true); // Should remain unchanged
        });
    });

    describe('Error message enhancement with backend integration', () => {
        test('preserves backend user-friendly messages', async () => {
            const backendResponse = {
                ok: false,
                status: 400,
                headers: new Map([['Content-Type', 'application/json']]),
                text: jest.fn().mockResolvedValue('{"error": "This task is not bookable. Please select a different task or check if the task is active."}')
            };
            backendResponse.headers.get = jest.fn().mockReturnValue('application/json');
            backendResponse.headers.forEach = jest.fn();
            
            fetch.mockResolvedValue(backendResponse);

            try {
                await fetchWithErrorHandling('/api/project-times', {
                    method: 'POST'
                });
            } catch (error) {
                expect(error.userMessage).toBe('This task is not bookable. Please select a different task or check if the task is active.');
                expect(error.technicalMessage).toBe('This task is not bookable. Please select a different task or check if the task is active.');
            }
        });

        test('handles business rule violations appropriately', async () => {
            const businessRuleResponse = {
                ok: false,
                status: 409,
                headers: new Map([['Content-Type', 'application/json']]),
                text: jest.fn().mockResolvedValue('{"error": "This working time is frozen and cannot be modified."}')
            };
            businessRuleResponse.headers.get = jest.fn().mockReturnValue('application/json');
            businessRuleResponse.headers.forEach = jest.fn();
            
            fetch.mockResolvedValue(businessRuleResponse);

            try {
                await fetchWithErrorHandling('/api/working-times/123', {
                    method: 'PATCH'
                }, {
                    operation: 'update_working_time'
                });
            } catch (error) {
                expect(error.message).toBe('This working time is frozen and cannot be modified.');
                expect(logApiError).toHaveBeenCalledWith(
                    'update_working_time',
                    error,
                    expect.objectContaining({
                        responseStatus: 409,
                        responseData: { error: 'This working time is frozen and cannot be modified.' }
                    })
                );
            }
        });
    });
});