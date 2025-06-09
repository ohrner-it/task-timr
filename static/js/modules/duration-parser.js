/**
 * Duration Parser Module
 * Parse Jira-like duration formats and validate durations
 * Can be used in both browser and Node.js (Jest) environments
 */

// Constants for duration parsing
export const JIRA_PARSE_DELAY_MS = 1000;
export const MAX_REASONABLE_DURATION_HOURS = 24;
export const MAX_REASONABLE_DURATION_MINUTES = MAX_REASONABLE_DURATION_HOURS * 60;

/**
 * Check if duration is within reasonable bounds
 * @param {number} minutes - Duration in minutes
 * @returns {boolean} - True if duration is reasonable
 */
export function isReasonableDuration(minutes) {
    return minutes > 0 && minutes <= MAX_REASONABLE_DURATION_MINUTES;
}

/**
 * Parse Jira-like duration format (e.g., "2h 30m", "45m", "1.5h") to minutes
 * @param {string} durationString - Duration string to parse
 * @returns {number} - Duration in minutes, or NaN if parsing fails
 */
export function parseJiraDuration(durationString) {
    if (!durationString) return NaN;

    // Handle non-string input types
    if (
        typeof durationString !== "string" &&
        typeof durationString !== "number"
    ) {
        return NaN;
    }

    // Handle pure number input (already in minutes)
    if (!isNaN(durationString)) {
        const minutes = parseInt(durationString);
        return isReasonableDuration(minutes) ? minutes : NaN;
    }

    // Convert to string and preserve spaces for smart parsing
    const input = String(durationString).toLowerCase().trim();

    // Initialize variables for hours and minutes
    let hours = 0;
    let minutes = 0;

    // Helper function to parse decimal numbers with locale support
    const parseDecimal = (str) => {
        // Support both English (.) and German (,) decimal separators
        const normalized = str.replace(',', '.');
        return parseFloat(normalized);
    };

    // Check for invalid patterns first (like "5h 35x" with extra characters)
    // But allow valid patterns like "1h 5m" (don't flag "m" as invalid)
    if (/^\d+(?:[.,]\d+)?h\s+\d+[a-zA-Z]/.test(input) && !/^\d+(?:[.,]\d+)?h\s+\d+m/.test(input)) {
        return NaN; // Invalid: has extra characters after the number (but not "m")
    }
    
    // Smart parsing for patterns like "5h 35" (interpret trailing number as minutes)
    // Match hour followed by space and 1-2 digit number, but ensure no extra characters
    const smartPattern = /^(\d+(?:[.,]\d+)?)h\s+(\d{1,2})$/;
    const smartMatch = input.match(smartPattern);
    if (smartMatch) {
        hours = parseDecimal(smartMatch[1]);
        minutes = parseInt(smartMatch[2]);
        
        // Validate parsed values and ensure minutes are reasonable (0-59)
        if (isNaN(hours) || isNaN(minutes) || hours < 0 || minutes < 0 || minutes >= 60) {
            return NaN;
        }
    } else {
        
        // Normalize by removing spaces for traditional parsing
        const normalized = input.replace(/\s+/g, "");

        // Match hours pattern with locale-aware decimals (e.g., "2h", "1.5h", "1,5h", "1.h", "-1h")
        // But ensure there's actually a number before the 'h'
        const hoursMatch = normalized.match(/(-?\d+[.,]?\d*)h/);
        if (hoursMatch && hoursMatch[1] !== "") {
            const hourValue = hoursMatch[1];
            // Handle cases like "1.h" or "1,h" (decimal point but no fractional part)
            if (hourValue.endsWith(".") || hourValue.endsWith(",")) {
                hours = parseDecimal(hourValue + "0");
            } else {
                hours = parseDecimal(hourValue);
            }
            // Validate parsed hours - reject negative values
            if (isNaN(hours) || hours < 0) {
                return NaN;
            }
        }

        // Match minutes pattern (e.g., "30m", "45m", "-15m")
        const minutesMatch = normalized.match(/(-?\d+)m/);
        if (minutesMatch) {
            minutes = parseInt(minutesMatch[1]);
            // Validate parsed minutes - reject negative values
            if (isNaN(minutes) || minutes < 0) {
                return NaN;
            }
        }

        // Check for invalid patterns like "h30m" (missing hour value) or "1h m" (missing minute value)
        if (normalized.startsWith('h') && minutesMatch) {
            return NaN; // Invalid: missing hour value before 'h'
        }
        if (input.includes('h m') || input.endsWith('h m')) {
            return NaN; // Invalid: missing minute value after 'h '
        }
        
        // If neither hours nor minutes were found, try parsing as pure minutes
        if (!hoursMatch && !minutesMatch) {
            return NaN;
        }
    }

    // Convert hours to minutes and add to minutes
    const totalMinutes = Math.round(hours * 60) + minutes;
    return isReasonableDuration(totalMinutes) ? totalMinutes : NaN;
}