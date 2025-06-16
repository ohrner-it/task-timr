/**
 * Error Handling Utility Module
 * Provides consistent error handling and logging across the application
 */

import { logApiError, showAlert } from './ui-utils.js';

/**
 * Enhanced fetch wrapper with automatic error handling and logging
 * @param {string} url - The URL to fetch
 * @param {object} options - Fetch options (method, headers, body, etc.)
 * @param {object} context - Additional context for error logging
 * @returns {Promise<object>} - Response data on success
 * @throws {Error} - Enhanced error with detailed logging on failure
 */
export async function fetchWithErrorHandling(url, options = {}, context = {}) {
    const requestContext = {
        requestUrl: url,
        requestMethod: options.method || 'GET',
        requestData: options.body ? JSON.parse(options.body) : null,
        operation: context.operation || 'API request',
        ...context
    };

    try {
        const response = await fetch(url, options);
        
        if (!response.ok) {
            await handleApiError(response, requestContext);
        }

        return await response.json();
    } catch (error) {
        // If it's already an enhanced error from handleApiError, re-throw it
        if (error.isApiError) {
            throw error;
        }
        
        // Handle network or other fetch errors
        const networkError = new Error(`Network error: ${error.message}`);
        networkError.isApiError = true;
        
        logApiError(requestContext.operation, networkError, {
            ...requestContext,
            originalError: error.message,
            errorType: 'network'
        });
        
        throw networkError;
    }
}

/**
 * Handle API response errors with detailed logging
 * @param {Response} response - The failed response object
 * @param {object} requestContext - Request context for logging
 * @throws {Error} - Enhanced error with detailed logging
 */
async function handleApiError(response, requestContext) {
    let responseData;
    let responseText;
    
    try {
        responseText = await response.text();
        responseData = JSON.parse(responseText);
    } catch (parseError) {
        responseData = { error: `Server returned ${response.status}: ${responseText || 'Unknown error'}` };
    }

    // Collect response headers for debugging
    const responseHeaders = {};
    response.headers.forEach((value, key) => {
        responseHeaders[key] = value;
    });

    // Prepare enhanced error context
    const errorContext = {
        ...requestContext,
        responseStatus: response.status,
        responseData: responseData,
        responseHeaders: responseHeaders,
        browserInfo: {
            userAgent: navigator.userAgent,
            language: navigator.language,
            cookieEnabled: navigator.cookieEnabled
        }
    };

    // Enhanced error message handling with backend error categorization
    let errorMessage;
    
    if (response.status === 401) {
        errorMessage = "Please log in to your Timr account to view and manage working times";
    } else if (responseData.error) {
        // Use the user-friendly error message from the enhanced backend
        errorMessage = responseData.error;
    } else {
        // Fallback for cases where backend doesn't provide user message
        switch (response.status) {
            case 400:
                errorMessage = "Invalid request. Please check your input and try again.";
                break;
            case 403:
                errorMessage = "Access denied. You don't have permission for this operation.";
                break;
            case 404:
                errorMessage = "The requested resource was not found.";
                break;
            case 409:
                errorMessage = "This operation conflicts with existing data.";
                break;
            case 422:
                errorMessage = "The data provided is invalid or incomplete.";
                break;
            case 500:
                errorMessage = "The server encountered an error. Please try again later.";
                break;
            case 502:
            case 503:
                errorMessage = "The service is temporarily unavailable. Please try again later.";
                break;
            default:
                errorMessage = `HTTP ${response.status}: Failed to ${requestContext.operation}`;
        }
    }
    
    const apiError = new Error(errorMessage);
    apiError.isApiError = true;
    apiError.status = response.status;
    apiError.responseData = responseData;
    apiError.userMessage = errorMessage;  // Store user-friendly message separately
    apiError.technicalMessage = responseData.technical_message || responseData.error || errorMessage;
    
    // Log the error with detailed context
    logApiError(requestContext.operation, apiError, errorContext);
    
    throw apiError;
}

/**
 * Handle errors in UI operations with consistent error display and logging
 * @param {Error} error - The error that occurred
 * @param {object} options - Error handling options
 * @param {string} options.operation - Description of the operation that failed
 * @param {boolean} options.modalContext - Whether to show error in modal (keeps modal open)
 * @param {function} options.fallbackAction - Optional fallback action to execute
 * @param {object} options.additionalContext - Additional context for logging
 */
export function handleUIError(error, options = {}) {
    const {
        operation = 'operation',
        modalContext = false,
        fallbackAction = null,
        additionalContext = {}
    } = options;

    // Show user-friendly error message
    const errorMessage = error.isApiError 
        ? error.message 
        : `Error during ${operation}: ${error.message}`;
    
    showAlert(errorMessage, "danger", modalContext);
    
    // Log summary to console for quick reference
    console.error(`${operation} failed:`, error.message);
    
    // If it's not already an API error, log it with additional context
    if (!error.isApiError) {
        logApiError(operation, error, {
            errorType: 'ui',
            ...additionalContext
        });
    }
    
    // Execute fallback action if provided
    if (fallbackAction && typeof fallbackAction === 'function') {
        try {
            fallbackAction();
        } catch (fallbackError) {
            console.error(`Fallback action failed for ${operation}:`, fallbackError);
        }
    }
}

/**
 * Create a standardized error handler for async operations
 * @param {string} operation - Description of the operation
 * @param {object} options - Error handling options
 * @returns {function} - Error handler function
 */
export function createErrorHandler(operation, options = {}) {
    return (error) => handleUIError(error, { operation, ...options });
}

/**
 * Wrapper for form submission with error handling that keeps modals open on error
 * @param {function} submitFunction - The async function to execute
 * @param {object} options - Options for error handling
 * @param {string} options.operation - Description of the operation
 * @param {Element} options.form - The form element for context
 * @param {function} options.onSuccess - Success callback
 * @param {function} options.onError - Custom error callback
 * @returns {Promise} - The result of the operation
 */
export async function handleFormSubmission(submitFunction, options = {}) {
    const {
        operation = 'form submission',
        form = null,
        onSuccess = null,
        onError = null
    } = options;

    try {
        const result = await submitFunction();
        
        if (onSuccess && typeof onSuccess === 'function') {
            onSuccess(result);
        }
        
        return result;
    } catch (error) {
        // Always keep modal open on form submission errors
        const modalContext = true;
        
        if (onError && typeof onError === 'function') {
            onError(error);
        } else {
            handleUIError(error, { 
                operation, 
                modalContext,
                additionalContext: {
                    formId: form?.id,
                    formType: form?.tagName,
                    formAction: form?.action
                }
            });
        }
        
        // Re-throw the error to ensure the calling code knows an error occurred
        // This prevents success callbacks from running
        throw error;
    }
}

/**
 * Enhanced version of the original handleApiResponse function
 * @param {Response} response - The response object
 * @param {object} requestContext - Request context for logging
 * @returns {Promise<object>} - Response data on success
 */
export async function handleApiResponse(response, requestContext = {}) {
    if (!response.ok) {
        await handleApiError(response, requestContext);
    }
    return response.json();
}

/**
 * Utility to reset UI elements after an operation (success or failure)
 * @param {object} elements - Object containing UI elements to reset
 * @param {object} resetStates - Object containing reset states for each element
 */
export function resetUIElements(elements, resetStates) {
    Object.entries(elements).forEach(([key, element]) => {
        if (!element) return;
        
        const resetState = resetStates[key];
        if (!resetState) return;
        
        if (resetState.disabled !== undefined) {
            element.disabled = resetState.disabled;
        }
        
        if (resetState.innerHTML !== undefined) {
            element.innerHTML = resetState.innerHTML;
        }
        
        if (resetState.classList) {
            resetState.classList.remove?.forEach(cls => element.classList.remove(cls));
            resetState.classList.add?.forEach(cls => element.classList.add(cls));
        }
        
        if (resetState.style) {
            Object.entries(resetState.style).forEach(([prop, value]) => {
                element.style[prop] = value;
            });
        }
    });
}