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

/**
 * Extract time range from working time DOM element
 * @param {Element} workingTimeItem - Working time DOM element
 * @returns {Object|null} - Object with start and end minutes, or null if invalid
 */
export function extractTimeRangeFromWorkingTime(workingTimeItem) {
    const timeDisplay = workingTimeItem.querySelector(".card-header .fw-bold");
    if (!timeDisplay) return null;

    const timeText = timeDisplay.textContent.trim();
    const timeRange = timeText.split(" - ");
    if (timeRange.length !== 2) return null;

    const [startTime, endTime] = timeRange;
    const startMinutes = parseTimeToMinutes(startTime);
    const endMinutes = parseTimeToMinutes(endTime);

    if (startMinutes === null || endMinutes === null) return null;

    return { start: startMinutes, end: endMinutes };
}