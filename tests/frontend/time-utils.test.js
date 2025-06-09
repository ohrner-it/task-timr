/**
 * Tests for static/js/modules/time-utils.js
 * Following testing guidelines: Test the real thing, mock only the boundary
 */

import { 
    parseTimeToMinutes, 
    getCurrentTimeMinutes, 
    calculateTimeDistance, 
    formatDateTimeForAPI, 
    formatDuration, 
    getDateKey 
} from '../../static/js/modules/time-utils.js';

describe('Time Utils Module - Real Production Code', () => {
    beforeEach(() => {
        jest.clearAllMocks();
    });

    describe('parseTimeToMinutes', () => {
        test('converts valid time strings to minutes', () => {
            expect(parseTimeToMinutes('09:30')).toBe(570);
            expect(parseTimeToMinutes('14:45')).toBe(885);
            expect(parseTimeToMinutes('00:00')).toBe(0);
            expect(parseTimeToMinutes('23:59')).toBe(1439);
        });

        test('handles edge cases and invalid input', () => {
            expect(parseTimeToMinutes('invalid')).toBeNull();
            expect(parseTimeToMinutes('25:00')).toBeNull();
            expect(parseTimeToMinutes('12:60')).toBeNull();
            // Note: null/undefined will throw errors as they don't have .split() method
            // This matches the production code behavior
        });

        test('handles single digit hours and minutes', () => {
            expect(parseTimeToMinutes('9:30')).toBe(570);
            expect(parseTimeToMinutes('09:5')).toBe(545);
            expect(parseTimeToMinutes('9:5')).toBe(545);
        });
    });

    describe('getCurrentTimeMinutes', () => {
        test('returns current time in minutes', () => {
            const result = getCurrentTimeMinutes();
            expect(typeof result).toBe('number');
            expect(result).toBeGreaterThanOrEqual(0);
            expect(result).toBeLessThan(1440); // Less than 24 hours
        });
    });

    describe('calculateTimeDistance', () => {
        test('returns 0 when current time is within working time', () => {
            expect(calculateTimeDistance(570, 540, 600)).toBe(0); // 9:30 within 9:00-10:00
            expect(calculateTimeDistance(540, 540, 600)).toBe(0); // At start time
            expect(calculateTimeDistance(600, 540, 600)).toBe(0); // At end time
        });

        test('calculates distance before working time', () => {
            expect(calculateTimeDistance(500, 540, 600)).toBe(40); // 8:20 before 9:00-10:00
            expect(calculateTimeDistance(480, 540, 600)).toBe(60); // 8:00 before 9:00-10:00
        });

        test('calculates distance after working time', () => {
            expect(calculateTimeDistance(630, 540, 600)).toBe(30); // 10:30 after 9:00-10:00
            expect(calculateTimeDistance(660, 540, 600)).toBe(60); // 11:00 after 9:00-10:00
        });

        test('handles edge cases', () => {
            expect(calculateTimeDistance(0, 0, 60)).toBe(0); // Midnight start
            expect(calculateTimeDistance(1439, 1380, 1439)).toBe(0); // Late night end
        });
    });

    describe('formatDateTimeForAPI', () => {
        test('formats dates for API consumption', () => {
            const testDate = new Date('2025-05-28T14:30:00');
            const result = formatDateTimeForAPI(testDate);
            expect(result).toContain('2025-05-28T14:30:00');
            expect(result).toMatch(/[\+\-]\d{2}:\d{2}$/); // Timezone offset
        });

        test('handles different date objects', () => {
            const date1 = new Date('2025-01-01T00:00:00');
            const date2 = new Date('2025-12-31T23:59:59');
            
            const result1 = formatDateTimeForAPI(date1);
            const result2 = formatDateTimeForAPI(date2);
            
            expect(result1).toContain('2025-01-01T00:00:00');
            expect(result2).toContain('2025-12-31T23:59:59');
        });
    });

    describe('formatDuration', () => {
        test('formats duration with hours correctly', () => {
            expect(formatDuration(60)).toBe('1h 0m');
            expect(formatDuration(90)).toBe('1h 30m');
            expect(formatDuration(480)).toBe('8h 0m');
            expect(formatDuration(61)).toBe('1h 1m');
        });

        test('formats duration without hours', () => {
            expect(formatDuration(30)).toBe('30m');
            expect(formatDuration(1)).toBe('1m');
            expect(formatDuration(59)).toBe('59m');
        });

        test('handles edge cases', () => {
            expect(formatDuration(0)).toBe('0m');
            expect(formatDuration(1440)).toBe('24h 0m');
            expect(formatDuration(1500)).toBe('25h 0m');
        });
    });

    describe('getDateKey', () => {
        test('generates consistent date keys', () => {
            const date1 = new Date('2025-05-28T14:30:00');
            const date2 = new Date('2025-05-28T09:15:00');
            const date3 = new Date('2025-05-29T14:30:00');
            
            expect(getDateKey(date1)).toBe(getDateKey(date2)); // Same date, different time
            expect(getDateKey(date1)).not.toBe(getDateKey(date3)); // Different date
        });

        test('returns string format YYYY-MM-DD', () => {
            const testDate = new Date('2025-05-28T14:30:00');
            const result = getDateKey(testDate);
            
            expect(typeof result).toBe('string');
            expect(result).toMatch(/^\d{4}-\d{2}-\d{2}$/);
            expect(result).toBe('2025-05-28');
        });

        test('handles different months and days', () => {
            expect(getDateKey(new Date('2025-01-01'))).toBe('2025-01-01');
            expect(getDateKey(new Date('2025-12-31'))).toBe('2025-12-31');
            expect(getDateKey(new Date('2025-02-15'))).toBe('2025-02-15');
        });
    });
});