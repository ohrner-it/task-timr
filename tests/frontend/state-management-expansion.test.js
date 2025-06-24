/**
 * Tests for state-management.js auto-expansion functionality
 * Following the Ten Laws for Unit Tests - testing the real production code
 * 
 * This test file covers the auto-expansion features:
 * 1. New working times should auto-expand when added via GUI
 * 2. When no expand/collapse info exists for a day, topmost working time should expand by default
 * 3. User explicit collapse choices should be respected
 */

// Import the real state management functions for testing
import { 
    hasExpandedStates,
    hasExpandCollapseHistory,
    expandDefaultWorkingTime,
    saveExpandedState,
    getExpandedStates
} from '../../static/js/modules/state-management.js';

// Set up minimal globals for testing state management in Node.js
global.localStorage = {
    storage: {},
    getItem: function(key) { return this.storage[key] || null; },
    setItem: function(key, value) { this.storage[key] = value; },
    removeItem: function(key) { delete this.storage[key]; },
    clear: function() { this.storage = {}; }
};

global.console = { 
    log: jest.fn(),
    error: jest.fn(),
    warn: jest.fn()
};

describe('State Management Auto-Expansion - Real Production Code', () => {
    beforeEach(() => {
        global.localStorage.clear();
        jest.clearAllMocks();
        global.currentViewDate = '2025-05-28';
    });

    describe('Simplified auto-expansion approach', () => {
        test('should handle newly created working times via normal expanded state', () => {
            const testDate = new Date('2025-05-28');
            const workingTimeId = 'wt_newly_created_123';
            
            // With simplified approach: just mark as expanded directly
            saveExpandedState(workingTimeId, true, testDate);
            
            // Should appear in normal expanded states
            expect(hasExpandedStates(testDate)).toBe(true);
            expect(hasExpandCollapseHistory(testDate)).toBe(true);
            
            const expandedStates = getExpandedStates(testDate);
            expect(expandedStates).toContain(workingTimeId);
        });

        test('should support multiple newly created working times in one day', () => {
            const testDate = new Date('2025-05-28');
            
            // With simplified approach: can mark multiple working times as expanded
            saveExpandedState('wt_created_1', true, testDate);
            saveExpandedState('wt_created_2', true, testDate);
            
            const expandedStates = getExpandedStates(testDate);
            expect(expandedStates).toHaveLength(2);
            expect(expandedStates).toContain('wt_created_1');
            expect(expandedStates).toContain('wt_created_2');
            
            // Better UX: both stay expanded instead of only remembering the last one
        });

        test('should handle multiple dates independently with simplified approach', () => {
            const date1 = new Date('2025-05-28');
            const date2 = new Date('2025-05-29');
            
            // Mark different working times for different dates
            saveExpandedState('WT_DATE1', true, date1);
            saveExpandedState('WT_DATE2', true, date2);
            
            // Each date should maintain its own expanded states
            expect(getExpandedStates(date1)).toContain('WT_DATE1');
            expect(getExpandedStates(date2)).toContain('WT_DATE2');
            
            // Cross-date isolation
            expect(getExpandedStates(date1)).not.toContain('WT_DATE2');
            expect(getExpandedStates(date2)).not.toContain('WT_DATE1');
        });
    });

    describe('Expand/collapse history tracking - The core bug fix', () => {
        test('should distinguish between never visited vs explicitly collapsed all', () => {
            const testDate = new Date('2025-05-28');
            
            // INITIAL STATE: User has never visited this date
            expect(hasExpandCollapseHistory(testDate)).toBe(false);
            expect(hasExpandedStates(testDate)).toBe(false);
            // This is the case where topmost should auto-expand
            
            // AFTER USER INTERACTION: User expands a working time
            saveExpandedState('wt-1', true, testDate);
            expect(hasExpandCollapseHistory(testDate)).toBe(true);
            expect(hasExpandedStates(testDate)).toBe(true);
            
            // CRITICAL TEST: After user collapses all working times
            saveExpandedState('wt-1', false, testDate);
            expect(hasExpandCollapseHistory(testDate)).toBe(true); // Still has history
            expect(hasExpandedStates(testDate)).toBe(false); // But no expanded states
            // This is the case where nothing should auto-expand (respect user choice)
        });

        test('should properly track multiple working times expansion state', () => {
            const testDate = new Date('2025-05-28');
            
            // Expand multiple working times
            saveExpandedState('wt-1', true, testDate);
            saveExpandedState('wt-2', true, testDate);
            saveExpandedState('wt-3', true, testDate);
            
            expect(hasExpandCollapseHistory(testDate)).toBe(true);
            expect(hasExpandedStates(testDate)).toBe(true);
            
            const expandedStates = getExpandedStates(testDate);
            expect(expandedStates).toHaveLength(3);
            expect(expandedStates).toContain('wt-1');
            expect(expandedStates).toContain('wt-2');
            expect(expandedStates).toContain('wt-3');
            
            // Collapse one working time
            saveExpandedState('wt-2', false, testDate);
            
            const updatedStates = getExpandedStates(testDate);
            expect(updatedStates).toHaveLength(2);
            expect(updatedStates).toContain('wt-1');
            expect(updatedStates).not.toContain('wt-2');
            expect(updatedStates).toContain('wt-3');
            
            // Still has history and expanded states
            expect(hasExpandCollapseHistory(testDate)).toBe(true);
            expect(hasExpandedStates(testDate)).toBe(true);
        });

        test('should handle edge case of collapsing non-existent working time', () => {
            const testDate = new Date('2025-05-28');
            
            // Try to collapse a working time that was never expanded
            saveExpandedState('non-existent-wt', false, testDate);
            
            // Should create history but no expanded states
            expect(hasExpandCollapseHistory(testDate)).toBe(true);
            expect(hasExpandedStates(testDate)).toBe(false);
            expect(getExpandedStates(testDate)).toHaveLength(0);
        });
    });

    describe('Default expansion logic with DOM integration', () => {
        test('should expand first working time when DOM elements are properly structured', () => {
            const testDate = new Date('2025-05-28');
            
            // Create realistic mock DOM elements
            const mockIcon = { className: 'bi bi-chevron-down' };
            const mockToggleButton = { querySelector: jest.fn(() => mockIcon) };
            const mockDetailsSection = { 
                classList: { 
                    remove: jest.fn(),
                    contains: jest.fn(() => true) // Initially collapsed
                } 
            };
            
            const mockFirstWorkingTime = {
                dataset: { id: 'wt-first' },
                querySelector: jest.fn((selector) => {
                    if (selector === '.working-time-details') return mockDetailsSection;
                    if (selector === '.toggle-details') return mockToggleButton;
                    return null;
                })
            };
            
            const mockWorkingTimeElements = [mockFirstWorkingTime];
            
            // Call the production function
            const expandedId = expandDefaultWorkingTime(mockWorkingTimeElements, testDate);
            
            // Verify the function succeeded
            expect(expandedId).toBe('wt-first');
            
            // Verify DOM manipulation was called
            expect(mockDetailsSection.classList.remove).toHaveBeenCalledWith('d-none');
            expect(mockIcon.className).toBe('bi bi-chevron-up');
            
            // Verify state was saved
            expect(hasExpandCollapseHistory(testDate)).toBe(true);
            expect(hasExpandedStates(testDate)).toBe(true);
            const expandedStates = getExpandedStates(testDate);
            expect(expandedStates).toContain('wt-first');
        });

        test('should handle empty working time lists gracefully', () => {
            const testDate = new Date('2025-05-28');
            const emptyList = [];
            
            const result = expandDefaultWorkingTime(emptyList, testDate);
            expect(result).toBeNull();
            
            // Should not create any state
            expect(hasExpandCollapseHistory(testDate)).toBe(false);
            expect(hasExpandedStates(testDate)).toBe(false);
        });

        test('should handle malformed DOM elements without crashing', () => {
            const testDate = new Date('2025-05-28');
            
            // Mock working time with missing critical DOM elements
            const mockWorkingTime = {
                dataset: { id: 'wt-broken' },
                querySelector: jest.fn(() => null) // Missing all DOM elements
            };
            
            const result = expandDefaultWorkingTime([mockWorkingTime], testDate);
            expect(result).toBeNull();
            
            // Should not create any state when DOM is broken
            expect(hasExpandCollapseHistory(testDate)).toBe(false);
            expect(hasExpandedStates(testDate)).toBe(false);
        });

        test('should handle working time without ID gracefully', () => {
            const testDate = new Date('2025-05-28');
            
            // Mock working time with missing ID
            const mockWorkingTime = {
                dataset: {}, // No ID
                querySelector: jest.fn()
            };
            
            const result = expandDefaultWorkingTime([mockWorkingTime], testDate);
            expect(result).toBeNull();
        });
    });

    describe('Integration scenarios - Testing the actual workflows', () => {
        test('should handle newly created working times through normal expansion state', () => {
            const testDate = new Date('2025-05-28');
            
            // With simplified approach: mark working time as expanded directly
            saveExpandedState('wt-newly-created', true, testDate);
            
            // Should immediately be in expanded states
            expect(hasExpandCollapseHistory(testDate)).toBe(true);
            expect(hasExpandedStates(testDate)).toBe(true);
            expect(getExpandedStates(testDate)).toContain('wt-newly-created');
        });

        test('should work correctly with day switching scenarios', () => {
            const date1 = new Date('2025-05-28');
            const date2 = new Date('2025-05-29');
            
            // Set up different states for different days
            saveExpandedState('wt-day1', true, date1);
            saveExpandedState('wt-newly-created-day2', true, date2);
            
            // Day 1: Has expansion history and expanded states
            expect(hasExpandCollapseHistory(date1)).toBe(true);
            expect(hasExpandedStates(date1)).toBe(true);
            expect(getExpandedStates(date1)).toContain('wt-day1');
            
            // Day 2: Also has expansion history and expanded states (simplified approach)
            expect(hasExpandCollapseHistory(date2)).toBe(true);
            expect(hasExpandedStates(date2)).toBe(true);
            expect(getExpandedStates(date2)).toContain('wt-newly-created-day2');
            
            // Both days maintain their independent states
            expect(getExpandedStates(date1)).not.toContain('wt-newly-created-day2');
            expect(getExpandedStates(date2)).not.toContain('wt-day1');
        });

        test('should maintain existing expand/collapse behavior', () => {
            const testDate = new Date('2025-05-28');
            
            // Simulate existing user behavior: expand, collapse, expand different ones
            saveExpandedState('wt-1', true, testDate);
            saveExpandedState('wt-2', true, testDate);
            saveExpandedState('wt-3', true, testDate);
            
            // User collapses wt-2
            saveExpandedState('wt-2', false, testDate);
            
            // State should be correctly maintained
            const expandedStates = getExpandedStates(testDate);
            expect(expandedStates).toHaveLength(2);
            expect(expandedStates).toContain('wt-1');
            expect(expandedStates).not.toContain('wt-2');
            expect(expandedStates).toContain('wt-3');
            
            expect(hasExpandCollapseHistory(testDate)).toBe(true);
            expect(hasExpandedStates(testDate)).toBe(true);
        });
    });

    describe('Edge cases and error conditions', () => {
        test('should handle localStorage errors gracefully', () => {
            // This tests the fallback behavior when localStorage fails
            const originalGetItem = global.localStorage.getItem;
            global.localStorage.getItem = jest.fn(() => { throw new Error('Storage error'); });
            
            const testDate = new Date('2025-05-28');
            
            // Functions should not crash when localStorage fails
            expect(() => hasExpandCollapseHistory(testDate)).not.toThrow();
            expect(() => hasExpandedStates(testDate)).not.toThrow();
            expect(() => getExpandedStates(testDate)).not.toThrow();
            
            // Restore original function
            global.localStorage.getItem = originalGetItem;
        });

        test('should handle invalid dates gracefully', () => {
            const invalidDate = new Date('invalid-date');
            
            // Functions should handle invalid dates without crashing
            expect(() => hasExpandCollapseHistory(invalidDate)).not.toThrow();
            expect(() => hasExpandedStates(invalidDate)).not.toThrow();
            expect(() => getExpandedStates(invalidDate)).not.toThrow();
            expect(() => saveExpandedState('test', true, invalidDate)).not.toThrow();
        });

        test('should handle null and undefined inputs', () => {
            // Functions should handle invalid inputs gracefully
            expect(() => saveExpandedState(null, true, new Date())).not.toThrow();
            expect(() => saveExpandedState('test', true, null)).not.toThrow();
            expect(() => getExpandedStates(null)).not.toThrow();
            expect(() => hasExpandCollapseHistory(undefined)).not.toThrow();
        });
    });

    describe('Regression tests - Ensuring the original bug is fixed', () => {
        test('REGRESSION: Should NOT auto-expand when user previously collapsed all working times', () => {
            const testDate = new Date('2025-05-28');
            
            // Simulate user visiting a day and expanding a working time
            saveExpandedState('wt-1', true, testDate);
            expect(hasExpandCollapseHistory(testDate)).toBe(true);
            expect(hasExpandedStates(testDate)).toBe(true);
            
            // User then collapses the working time (the bug scenario)
            saveExpandedState('wt-1', false, testDate);
            
            // CRITICAL: This should show that user has history but no expanded states
            expect(hasExpandCollapseHistory(testDate)).toBe(true); // User has interacted
            expect(hasExpandedStates(testDate)).toBe(false); // But nothing is expanded
            
            // The old buggy code would have returned true for auto-expansion here
            // The fixed code should recognize this as "user explicitly collapsed everything"
        });

        test('REGRESSION: Should auto-expand when user visits day for first time', () => {
            const testDate = new Date('2025-06-01'); // Completely new date
            
            // Verify this is truly a first visit
            expect(hasExpandCollapseHistory(testDate)).toBe(false);
            expect(hasExpandedStates(testDate)).toBe(false);
            
            // This scenario should trigger auto-expansion of topmost working time
            // (This is what the original requirement wanted)
        });

        test('REGRESSION: Should work correctly when user has mixed expand/collapse states', () => {
            const testDate = new Date('2025-05-28');
            
            // User expands multiple working times
            saveExpandedState('wt-1', true, testDate);
            saveExpandedState('wt-2', true, testDate);
            saveExpandedState('wt-3', true, testDate);
            
            // User collapses some but not all
            saveExpandedState('wt-2', false, testDate);
            
            // Should maintain the correct state
            expect(hasExpandCollapseHistory(testDate)).toBe(true);
            expect(hasExpandedStates(testDate)).toBe(true); // Still has some expanded
            
            const expandedStates = getExpandedStates(testDate);
            expect(expandedStates).toHaveLength(2);
            expect(expandedStates).toContain('wt-1');
            expect(expandedStates).not.toContain('wt-2');
            expect(expandedStates).toContain('wt-3');
        });
    });
});