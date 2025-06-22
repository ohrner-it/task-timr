/**
 * Tests for static/js/modules/dom-utils.js
 * Following testing guidelines: Test the real thing, mock only the boundary
 */

import { 
    escapeHtml
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

});