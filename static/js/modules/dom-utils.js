/**
 * DOM Utility Functions Module
 * Pure functions for DOM manipulation and HTML processing
 * Can be used in both browser and Node.js (Jest) environments
 */

import { parseTimeToMinutes } from './time-utils.js';

/**
 * Escape HTML special characters to prevent XSS
 * @param {string} str - String to escape
 * @returns {string} - Escaped string
 */
export function escapeHtml(str) {
    if (!str && str !== "") return "";

    return String(str)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

