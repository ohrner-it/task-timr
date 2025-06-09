/**
 * Unit tests for duration parser module
 * Tests the actual production code from static/js/modules/duration-parser.js
 */

// Import the production code
import { parseJiraDuration, isReasonableDuration } from '../../static/js/modules/duration-parser.js';

describe('Duration Parser', () => {
    describe('parseJiraDuration', () => {
        // Test basic hour formats
        test('should parse simple hour formats', () => {
            expect(parseJiraDuration('1h')).toBe(60);
            expect(parseJiraDuration('2h')).toBe(120);
            expect(parseJiraDuration('0.5h')).toBe(30);
            expect(parseJiraDuration('1.5h')).toBe(90);
            expect(parseJiraDuration('2.25h')).toBe(135);
        });

        // Test basic minute formats
        test('should parse simple minute formats', () => {
            expect(parseJiraDuration('30m')).toBe(30);
            expect(parseJiraDuration('45m')).toBe(45);
            expect(parseJiraDuration('90m')).toBe(90);
            expect(parseJiraDuration('1m')).toBe(1);
        });

        // Test combined hour and minute formats
        test('should parse combined hour and minute formats', () => {
            expect(parseJiraDuration('1h 30m')).toBe(90);
            expect(parseJiraDuration('2h 15m')).toBe(135);
            expect(parseJiraDuration('0.5h 15m')).toBe(45);
            expect(parseJiraDuration('1h30m')).toBe(90); // No space
        });

        // Test the specific "5h 35" case mentioned by user
        test('should interpret "5h 35" as "5h 35m"', () => {
            expect(parseJiraDuration('5h 35')).toBe(335); // 5*60 + 35 = 335
            expect(parseJiraDuration('1h 45')).toBe(105); // 1*60 + 45 = 105
            expect(parseJiraDuration('2h 30')).toBe(150); // 2*60 + 30 = 150
            expect(parseJiraDuration('0.5h 15')).toBe(45); // 0.5*60 + 15 = 45
            expect(parseJiraDuration('1h 5')).toBe(65); // 1*60 + 5 = 65 (single digit minutes)
        });

        // Test pure numeric input (already in minutes)
        test('should handle pure numeric input', () => {
            expect(parseJiraDuration('60')).toBe(60);
            expect(parseJiraDuration('120')).toBe(120);
            expect(parseJiraDuration(90)).toBe(90);
            expect(parseJiraDuration('0')).toBe(NaN); // Zero is not reasonable
        });

        // Test case insensitivity
        test('should be case insensitive', () => {
            expect(parseJiraDuration('1H')).toBe(60);
            expect(parseJiraDuration('30M')).toBe(30);
            expect(parseJiraDuration('1H 30M')).toBe(90);
            expect(parseJiraDuration('2H 45m')).toBe(165);
        });

        // Test German locale decimal formatting
        test('should handle German locale decimal formatting', () => {
            expect(parseJiraDuration('1,5h')).toBe(90); // German: 1,5 hours = 90 minutes
            expect(parseJiraDuration('2,25h')).toBe(135); // German: 2,25 hours = 135 minutes
            expect(parseJiraDuration('0,5h 15')).toBe(45); // Mixed: 0,5h + 15m = 45 minutes
            expect(parseJiraDuration('1,h')).toBe(60); // Edge case: 1,h = 1.0h = 60 minutes
        });

        // Test whitespace handling
        test('should handle various whitespace patterns', () => {
            expect(parseJiraDuration(' 1h 30m ')).toBe(90);
            expect(parseJiraDuration('1h  30m')).toBe(90); // Extra spaces
            expect(parseJiraDuration('1h\t30m')).toBe(90); // Tab
            expect(parseJiraDuration('  2h   45   ')).toBe(165); // "2h 45" format
        });

        // Test invalid inputs
        test('should return NaN for invalid inputs', () => {
            expect(parseJiraDuration('')).toBe(NaN);
            expect(parseJiraDuration(null)).toBe(NaN);
            expect(parseJiraDuration(undefined)).toBe(NaN);
            expect(parseJiraDuration('invalid')).toBe(NaN);
            expect(parseJiraDuration('5h 35x')).toBe(NaN); // Extra characters
            expect(parseJiraDuration('h30m')).toBe(NaN); // Missing hour value
            expect(parseJiraDuration('1h m')).toBe(NaN); // Missing minute value
            expect(parseJiraDuration('-1h')).toBe(NaN); // Negative hours
            expect(parseJiraDuration('1h -30m')).toBe(NaN); // Negative minutes
        });

        // Test edge cases with decimal points
        test('should handle decimal edge cases', () => {
            expect(parseJiraDuration('1.h')).toBe(60); // Decimal point with no fractional part
            expect(parseJiraDuration('1.0h')).toBe(60);
            expect(parseJiraDuration('2.5h')).toBe(150);
        });

        // Test unreasonable durations
        test('should reject unreasonable durations', () => {
            expect(parseJiraDuration('25h')).toBe(NaN); // More than 24 hours
            expect(parseJiraDuration('1500m')).toBe(NaN); // More than 24 hours in minutes
            expect(parseJiraDuration('24h 1m')).toBe(NaN); // Just over 24 hours
        });

        // Test boundary cases
        test('should handle boundary cases', () => {
            expect(parseJiraDuration('24h')).toBe(1440); // Exactly 24 hours
            expect(parseJiraDuration('1440m')).toBe(1440); // 24 hours in minutes
            expect(parseJiraDuration('1m')).toBe(1); // Minimum reasonable duration
        });
    });

    describe('isReasonableDuration', () => {
        test('should validate reasonable durations', () => {
            expect(isReasonableDuration(1)).toBe(true); // 1 minute
            expect(isReasonableDuration(60)).toBe(true); // 1 hour
            expect(isReasonableDuration(480)).toBe(true); // 8 hours
            expect(isReasonableDuration(1440)).toBe(true); // 24 hours
        });

        test('should reject unreasonable durations', () => {
            expect(isReasonableDuration(0)).toBe(false); // Zero
            expect(isReasonableDuration(-1)).toBe(false); // Negative
            expect(isReasonableDuration(1441)).toBe(false); // More than 24 hours
            expect(isReasonableDuration(2000)).toBe(false); // Way too much
        });
    });

    // Integration tests that verify the parsing works with real-world scenarios
    describe('Real-world scenarios', () => {
        test('should handle typical user inputs', () => {
            // Common work durations
            expect(parseJiraDuration('8h')).toBe(480); // Full work day
            expect(parseJiraDuration('4h 30m')).toBe(270); // Half day
            expect(parseJiraDuration('1h 15m')).toBe(75); // Meeting duration
            expect(parseJiraDuration('30m')).toBe(30); // Short task
            
            // The specific issue mentioned by the user
            expect(parseJiraDuration('5h 35')).toBe(335); // Should work as "5h 35m"
            
            // Other similar patterns
            expect(parseJiraDuration('2h 45')).toBe(165);
            expect(parseJiraDuration('1h 20')).toBe(80);
        });

        test('should handle user typing scenarios', () => {
            // These should all be invalid during typing but valid when complete
            expect(parseJiraDuration('5h ')).toBe(300); // Just hours with trailing space
            expect(parseJiraDuration('5h 3')).toBe(303); // Valid: 5h 3m = 5*60 + 3 = 303
            expect(parseJiraDuration('5h 35')).toBe(335); // Complete - should be valid
        });
        
        // Test the exact scenarios reported by the user
        test('should handle the exact user-reported issues', () => {
            // The main issue: "5h 35" should work as "5h 35m"
            expect(parseJiraDuration('5h 35')).toBe(335);
            
            // The secondary issue: "1h 5m" should work (was being rejected)
            expect(parseJiraDuration('1h 5m')).toBe(65);
            
            // German locale support
            expect(parseJiraDuration('1,5h')).toBe(90);
            
            // Both formats should work
            expect(parseJiraDuration('1h 30m')).toBe(90); // Traditional format
            expect(parseJiraDuration('1h 30')).toBe(90);  // Simplified format
        });
    });
});