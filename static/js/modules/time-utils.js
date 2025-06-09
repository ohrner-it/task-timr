/**
 * Time Utility Functions Module
 * Pure functions for time parsing, formatting, and calculations
 * Can be used in both browser and Node.js (Jest) environments
 */

/**
 * Parse time string (HH:MM) to minutes since midnight
 * @param {string} timeString - Time in HH:MM format
 * @returns {number|null} - Minutes since midnight, or null if invalid
 */
export function parseTimeToMinutes(timeString) {
    const timeParts = timeString.split(":");
    if (timeParts.length !== 2) return null;

    const hours = parseInt(timeParts[0]);
    const minutes = parseInt(timeParts[1]);

    if (
        isNaN(hours) ||
        isNaN(minutes) ||
        hours < 0 ||
        hours > 23 ||
        minutes < 0 ||
        minutes > 59
    ) {
        return null;
    }

    return hours * 60 + minutes;
}

/**
 * Get current time in minutes since midnight
 * @returns {number} - Minutes since midnight
 */
export function getCurrentTimeMinutes() {
    const now = new Date();
    return now.getHours() * 60 + now.getMinutes();
}

/**
 * Calculate time distance score for working time selection
 * @param {number} currentMinutes - Current time in minutes since midnight
 * @param {number} startMinutes - Working time start in minutes since midnight
 * @param {number} endMinutes - Working time end in minutes since midnight
 * @returns {number} - Distance score (0 = perfect match, higher = further away)
 */
export function calculateTimeDistance(currentMinutes, startMinutes, endMinutes) {
    if (currentMinutes >= startMinutes && currentMinutes <= endMinutes) {
        // Currently within this working time - perfect match
        return 0;
    } else if (currentMinutes < startMinutes) {
        // Before this working time
        return startMinutes - currentMinutes;
    } else {
        // After this working time
        return currentMinutes - endMinutes;
    }
}

/**
 * Format datetime in local timezone as ISO string without timezone conversion
 * @param {Date} date - Date object to format
 * @returns {string} - ISO format string in local timezone
 */
export function formatDateTimeForAPI(date) {
    // Get local timezone offset in minutes
    const timezoneOffset = date.getTimezoneOffset();
    const offsetHours = Math.floor(Math.abs(timezoneOffset) / 60);
    const offsetMinutes = Math.abs(timezoneOffset) % 60;
    const offsetSign = timezoneOffset <= 0 ? "+" : "-";

    // Format the date in local timezone
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, "0");
    const day = String(date.getDate()).padStart(2, "0");
    const hours = String(date.getHours()).padStart(2, "0");
    const minutes = String(date.getMinutes()).padStart(2, "0");
    const seconds = String(date.getSeconds()).padStart(2, "0");

    // Create ISO string with local timezone offset
    const timezoneString = `${offsetSign}${String(offsetHours).padStart(2, "0")}:${String(offsetMinutes).padStart(2, "0")}`;

    return `${year}-${month}-${day}T${hours}:${minutes}:${seconds}${timezoneString}`;
}

/**
 * Format duration in minutes to a human-readable string (e.g., "2h 30m")
 * @param {number} minutes - Duration in minutes
 * @returns {string} - Formatted duration string
 */
export function formatDuration(minutes) {
    if (!minutes && minutes !== 0) return "";

    const hours = Math.floor(minutes / 60);
    const remainingMinutes = minutes % 60;

    if (hours > 0) {
        return `${hours}h ${remainingMinutes}m`;
    } else {
        return `${remainingMinutes}m`;
    }
}

/**
 * Get date key for current view date
 * @param {Date} currentViewDate - The current view date
 * @returns {string} - Date key in YYYY-MM-DD format
 */
export function getDateKey(currentViewDate) {
    const dateObj = new Date(currentViewDate || new Date());
    const year = dateObj.getFullYear();
    const month = String(dateObj.getMonth() + 1).padStart(2, "0");
    const day = String(dateObj.getDate()).padStart(2, "0");
    return `${year}-${month}-${day}`;
}