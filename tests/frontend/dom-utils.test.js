/**
 * Tests for static/js/modules/dom-utils.js
 * Following testing guidelines: Test the real thing, mock only the boundary
 */

import { 
    escapeHtml, 
    extractTimeRangeFromWorkingTime 
} from '../../static/js/modules/dom-utils.js';

describe('DOM Utils Module - Real Production Code', () => {
    beforeEach(() => {
        jest.clearAllMocks();
    });

    describe('escapeHtml', () => {
        test('prevents XSS with all special characters', () => {
            expect(escapeHtml('<script>')).toBe('&lt;script&gt;');
            expect(escapeHtml('&')).toBe('&amp;');
            expect(escapeHtml('"quotes"')).toBe('&quot;quotes&quot;');
            expect(escapeHtml("'single'")).toBe('&#039;single&#039;');
            expect(escapeHtml('normal text')).toBe('normal text');
        });

        test('handles edge cases', () => {
            expect(escapeHtml('')).toBe('');
            expect(escapeHtml(null)).toBe('');
            expect(escapeHtml(undefined)).toBe('');
            expect(escapeHtml(0)).toBe('');        // Falsy values return empty string
            expect(escapeHtml(false)).toBe('');    // Falsy values return empty string
        });

        test('handles complex XSS attempts', () => {
            const malicious = '<script>alert("xss")</script>';
            const expected = '&lt;script&gt;alert(&quot;xss&quot;)&lt;/script&gt;';
            expect(escapeHtml(malicious)).toBe(expected);
            
            const withAttributes = '<img src="x" onerror="alert(1)">';
            const expectedAttr = '&lt;img src=&quot;x&quot; onerror=&quot;alert(1)&quot;&gt;';
            expect(escapeHtml(withAttributes)).toBe(expectedAttr);
        });
    });

    describe('extractTimeRangeFromWorkingTime', () => {
        test('parses valid time ranges correctly', () => {
            const mockWorkingTime = {
                querySelector: jest.fn().mockReturnValue({
                    textContent: '09:00 - 17:00'
                })
            };

            const result = extractTimeRangeFromWorkingTime(mockWorkingTime);
            expect(result).toEqual({
                start: 540,   // 9:00 AM in minutes
                end: 1020     // 5:00 PM in minutes
            });
        });

        test('handles missing elements', () => {
            const mockWorkingTime = {
                querySelector: jest.fn().mockReturnValue(null)
            };

            const result = extractTimeRangeFromWorkingTime(mockWorkingTime);
            expect(result).toBeNull();
        });

        test('handles invalid time formats', () => {
            const mockWorkingTime = {
                querySelector: jest.fn().mockReturnValue({
                    textContent: 'invalid - format'
                })
            };

            const result = extractTimeRangeFromWorkingTime(mockWorkingTime);
            expect(result).toBeNull();
        });

        test('handles malformed time ranges', () => {
            const mockWorkingTime = {
                querySelector: jest.fn().mockReturnValue({
                    textContent: 'not a time range'
                })
            };

            const result = extractTimeRangeFromWorkingTime(mockWorkingTime);
            expect(result).toBeNull();
        });
    });
});