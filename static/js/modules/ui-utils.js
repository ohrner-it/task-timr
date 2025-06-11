/**
 * UI Utility Functions Module
 * Functions for alerts, logging, and common UI interactions
 * Can be used in both browser and Node.js (Jest) environments
 */

/**
 * Enhanced logging function
 * @param {string} message - Log message
 * @param {string} level - Log level (info, warn, error)
 * @param {object} data - Additional data to log
 */
export function logMessage(message, level = "info", data = null) {
    // Get the calling function and line number where possible
    const stack = new Error().stack;
    const caller = stack ? stack.split("\n")[2].trim() : "unknown";

    // Create log object
    const logObject = {
        timestamp: new Date().toISOString(),
        message: message,
        level: level,
        source: caller,
    };

    // Add additional data if provided
    if (data) {
        logObject.data = data;
    }

    // Log to console with appropriate level (only in browser environment)
    if (typeof console !== 'undefined') {
        switch (level.toLowerCase()) {
            case "error":
                console.error("Error:", logObject);
                break;
            case "warn":
                console.warn("Warning:", logObject);
                break;
            default:
                console.log("Info:", logObject);
        }
    }

    return logObject;
}

/**
 * Enhanced error logging function for API errors
 * @param {string} operation - Operation that failed (e.g., "save time allocation")
 * @param {Error} error - The error object
 * @param {object} context - Additional context (request data, response, etc.)
 */
export function logApiError(operation, error, context = {}) {
    const errorDetails = {
        operation: operation,
        message: error.message,
        timestamp: new Date().toISOString(),
        userAgent: navigator?.userAgent || 'unknown',
        url: window?.location?.href || 'unknown',
        ...context
    };

    // Log comprehensive error information in a single message
    const logMessage = [
        `API Error: ${operation}`,
        `Message: ${error.message}`,
        context.requestMethod && context.requestUrl ? `Request: ${context.requestMethod} ${context.requestUrl}` : '',
        context.requestData ? `Request data: ${JSON.stringify(context.requestData)}` : '',
        context.responseStatus ? `Response status: ${context.responseStatus}` : '',
        context.responseData ? `Response: ${JSON.stringify(context.responseData)}` : '',
        `Browser: ${errorDetails.userAgent.split(' ')[0]}`, // Just browser name
        `Timestamp: ${errorDetails.timestamp}`
    ].filter(Boolean).join(' | ');
    
    console.error(logMessage, errorDetails);

    return errorDetails;
}

/**
 * Show an alert message to the user
 * @param {string} message - Alert message to display
 * @param {string} type - Bootstrap alert type (info, success, warning, danger)
 * @param {boolean} modalContext - Whether to show the alert in a modal
 */
export function showAlert(message, type = "info", modalContext = false) {
    // Skip DOM manipulation in Node.js testing environment
    if (typeof document === 'undefined') {
        return;
    }

    // Create the alert element
    const alertElement = document.createElement("div");
    alertElement.className = `alert alert-${type} alert-dismissible fade show`;
    alertElement.setAttribute("role", "alert");
    alertElement.innerHTML = `
        <i class="bi ${
            type === "danger"
                ? "bi-exclamation-triangle-fill"
                : type === "success"
                  ? "bi-check-circle-fill"
                  : type === "warning"
                    ? "bi-exclamation-triangle-fill"
                    : "bi-info-circle-fill"
        } me-2"></i>
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;

    // Add to appropriate container
    let container;
    if (modalContext) {
        // For modals, add to the modal alerts container
        const activeModal = document.querySelector(".modal.show .modal-alerts");
        if (activeModal) {
            container = activeModal;
        } else {
            // Fallback to global alerts if no modal is active
            container = document.getElementById("global-alerts");
        }
    } else {
        // Add to global alerts container
        container = document.getElementById("global-alerts");
    }

    // If container exists, add the alert
    if (container) {
        container.appendChild(alertElement);

        // Auto-remove after 5 seconds for non-error alerts
        if (type !== "danger") {
            setTimeout(() => {
                if (alertElement.parentNode === container) {
                    container.removeChild(alertElement);
                }
            }, 5000);
        }
    }
}

/**
 * Create a debounced function
 * @param {Function} func - Function to debounce
 * @param {number} wait - Wait time in milliseconds
 * @returns {Function} - Debounced function
 */
export function debounce(func, wait) {
    let timeout;
    return function (...args) {
        clearTimeout(timeout);
        timeout = setTimeout(() => func.apply(this, args), wait);
    };
}