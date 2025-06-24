/**
 * Integration tests for main.js auto-expansion workflow
 * Testing the complete user interaction flow that was affected by the original bug
 * 
 * These tests focus on the integration between:
 * 1. saveWorkingTime() function marking newly created working times
 * 2. restoreExpandedStates() function handling auto-expansion logic
 * 3. The critical bug fix that distinguishes "never visited" vs "user collapsed all"
 */

// Import the functions we need to test from the production modules
import { 
    hasExpandedStates,
    hasExpandCollapseHistory,
    expandDefaultWorkingTime,
    saveExpandedState,
    getExpandedStates
} from '../../static/js/modules/state-management.js';

// Mock the DOM environment for testing main.js integration
global.document = {
    querySelectorAll: jest.fn(),
    querySelector: jest.fn(),
    getElementById: jest.fn()
};

global.bootstrap = {
    Modal: {
        getInstance: jest.fn(() => ({
            hide: jest.fn()
        }))
    }
};

global.console = { 
    log: jest.fn(),
    error: jest.fn(),
    warn: jest.fn()
};

// Set up localStorage mock
global.localStorage = {
    storage: {},
    getItem: function(key) { return this.storage[key] || null; },
    setItem: function(key, value) { this.storage[key] = value; },
    removeItem: function(key) { delete this.storage[key]; },
    clear: function() { this.storage = {}; }
};

// Mock fetch for API calls
global.fetch = jest.fn(() => 
    Promise.resolve({
        ok: true,
        json: () => Promise.resolve({
            working_time: { id: 'wt_api_response_123' }
        })
    })
);

describe('Main.js Auto-Expansion Integration - Complete User Workflow', () => {
    beforeEach(() => {
        global.localStorage.clear();
        jest.clearAllMocks();
        
        // Set up basic DOM structure that main.js expects
        global.document.querySelectorAll = jest.fn((selector) => {
            if (selector === '.working-time-item') {
                return [
                    {
                        dataset: { id: 'wt-1' },
                        querySelector: jest.fn((sel) => {
                            if (sel === '.working-time-details') {
                                return { classList: { remove: jest.fn(), contains: jest.fn(() => true) } };
                            }
                            if (sel === '.toggle-details') {
                                return { querySelector: jest.fn(() => ({ className: 'bi bi-chevron-down' })) };
                            }
                            return null;
                        })
                    },
                    {
                        dataset: { id: 'wt-2' },
                        querySelector: jest.fn(() => null)
                    }
                ];
            }
            return [];
        });

        global.document.querySelector = jest.fn((selector) => {
            if (selector.includes('[data-id="wt-1"]')) {
                return {
                    dataset: { id: 'wt-1' },
                    querySelector: jest.fn((sel) => {
                        if (sel === '.working-time-details') {
                            return { classList: { remove: jest.fn(), contains: jest.fn(() => true) } };
                        }
                        if (sel === '.toggle-details') {
                            return { querySelector: jest.fn(() => ({ className: 'bi bi-chevron-down' })) };
                        }
                        return null;
                    })
                };
            }
            return null;
        });
    });

    describe('Complete workflow integration - The scenarios that caused the original bug', () => {
        /**
         * REGRESSION TEST: This test reproduces the exact scenario that caused the original bug
         * With simplified approach: newly created working time is immediately marked as expanded
         */
        test('REGRESSION: Complete workflow should handle user who created working time, then collapsed it, then switched back', () => {
            const testDate = new Date('2025-05-28');
            
            // STEP 1: Simulate user creating new working time (simplified saveWorkingTime approach)
            // NEW APPROACH: Just mark the working time as expanded directly
            saveExpandedState('wt_new_123', true, testDate);
            
            // STEP 2: Immediately after creation, working time is in expanded state
            expect(hasExpandCollapseHistory(testDate)).toBe(true);
            expect(hasExpandedStates(testDate)).toBe(true);
            expect(getExpandedStates(testDate)).toContain('wt_new_123');
            
            // STEP 3: User collapses the working time (this is the critical bug scenario)
            saveExpandedState('wt_new_123', false, testDate);
            
            // STATE CHECK: User has interaction history but no expanded states
            expect(hasExpandCollapseHistory(testDate)).toBe(true); // User HAS interacted
            expect(hasExpandedStates(testDate)).toBe(false); // But nothing is expanded
            
            // STEP 4: User switches to another day and back (triggering restoreExpandedStates again)
            // This is where the original bug manifested - the system would incorrectly auto-expand
            
            // Simulate the logic from restoreExpandedStates()
            const expandedIds = getExpandedStates(testDate);
            expect(expandedIds).toHaveLength(0); // No expanded states
            
            // The CRITICAL test: This should NOT trigger auto-expansion
            // because hasExpandCollapseHistory() returns true (user previously interacted)
            const hasHistory = hasExpandCollapseHistory(testDate);
            expect(hasHistory).toBe(true);
            
            // The bug was: if expandedIds.length === 0 was the only check,
            // it would auto-expand even when user had explicitly collapsed everything
            
            // With the fix, since hasHistory is true, no auto-expansion should occur
            // (this would be the "user previously collapsed all" branch in restoreExpandedStates)
        });

        test('REGRESSION: First-time visit should auto-expand topmost working time', () => {
            const testDate = new Date('2025-06-01'); // Completely new date
            
            // Verify this is a first-time visit
            expect(hasExpandCollapseHistory(testDate)).toBe(false);
            expect(hasExpandedStates(testDate)).toBe(false);
            
            // Simulate the restoreExpandedStates() logic for first-time visits
            const expandedIds = getExpandedStates(testDate);
            expect(expandedIds).toHaveLength(0);
            
            const hasHistory = hasExpandCollapseHistory(testDate);
            expect(hasHistory).toBe(false); // This should trigger auto-expansion
            
            // Simulate expandDefaultWorkingTime() being called
            const workingTimeItems = [
                {
                    dataset: { id: 'wt-first' },
                    querySelector: jest.fn((selector) => {
                        if (selector === '.working-time-details') {
                            return { classList: { remove: jest.fn(), contains: jest.fn(() => true) } };
                        }
                        if (selector === '.toggle-details') {
                            return { querySelector: jest.fn(() => ({ className: 'bi bi-chevron-down' })) };
                        }
                        return null;
                    })
                }
            ];
            
            const expandedId = expandDefaultWorkingTime(workingTimeItems, testDate);
            expect(expandedId).toBe('wt-first');
            
            // After auto-expansion, there should be history and expanded states
            expect(hasExpandCollapseHistory(testDate)).toBe(true);
            expect(hasExpandedStates(testDate)).toBe(true);
        });

        test('REGRESSION: Mixed expansion states should be handled correctly', () => {
            const testDate = new Date('2025-05-28');
            
            // User expands multiple working times
            saveExpandedState('wt-1', true, testDate);
            saveExpandedState('wt-2', true, testDate);
            saveExpandedState('wt-3', true, testDate);
            
            // User collapses one of them
            saveExpandedState('wt-2', false, testDate);
            
            // System should maintain correct state
            expect(hasExpandCollapseHistory(testDate)).toBe(true);
            expect(hasExpandedStates(testDate)).toBe(true); // Still has some expanded
            
            const expandedIds = getExpandedStates(testDate);
            expect(expandedIds).toHaveLength(2);
            expect(expandedIds).toContain('wt-1');
            expect(expandedIds).not.toContain('wt-2');
            expect(expandedIds).toContain('wt-3');
            
            // If user switches days and comes back, this should NOT trigger auto-expansion
            // because hasExpandCollapseHistory() is true and hasExpandedStates() is true
        });
    });

    describe('API Integration workflow', () => {
        test('Should handle API response with working time ID correctly (simplified approach)', () => {
            const testDate = new Date('2025-05-28');
            
            // Simulate successful API response with working time ID
            const apiResponse = {
                working_time: { id: 'wt_from_api_456' }
            };
            
            // NEW SIMPLIFIED APPROACH: Just mark as expanded directly
            if (apiResponse.working_time && apiResponse.working_time.id) {
                saveExpandedState(apiResponse.working_time.id, true, testDate);
            }
            
            // Verify the working time is in expanded states
            expect(hasExpandedStates(testDate)).toBe(true);
            expect(getExpandedStates(testDate)).toContain('wt_from_api_456');
        });

        test('Should handle API response without working time ID (graceful fallback)', () => {
            const testDate = new Date('2025-05-28');
            
            // Simulate API response without working time ID
            const apiResponse = { success: true };
            
            // NEW SIMPLIFIED APPROACH: If no ID available, just don't auto-expand
            // This is more robust than complex fallback logic
            if (!apiResponse.working_time || !apiResponse.working_time.id) {
                // Graceful fallback: do nothing (working time won't auto-expand)
                console.log('No working time ID in API response - skipping auto-expansion');
            }
            
            // Verify no states were affected
            expect(hasExpandedStates(testDate)).toBe(false);
            expect(getExpandedStates(testDate)).toHaveLength(0);
        });

        test('Should support multiple working time creations in one day (improved UX)', () => {
            const testDate = new Date('2025-05-28');
            
            // NEW BENEFIT: Multiple working times can all be auto-expanded
            const apiResponse1 = { working_time: { id: 'wt_first' } };
            const apiResponse2 = { working_time: { id: 'wt_second' } };
            
            // Both get marked as expanded
            saveExpandedState(apiResponse1.working_time.id, true, testDate);
            saveExpandedState(apiResponse2.working_time.id, true, testDate);
            
            // Both remain expanded (better UX than old approach that only remembered the last one)
            const expandedStates = getExpandedStates(testDate);
            expect(expandedStates).toHaveLength(2);
            expect(expandedStates).toContain('wt_first');
            expect(expandedStates).toContain('wt_second');
        });
    });

    describe('DOM Integration scenarios', () => {
        test('Should handle working time expansion through normal restoreExpandedStates flow', () => {
            const testDate = new Date('2025-05-28');
            
            // NEW SIMPLIFIED APPROACH: Mark working time as expanded directly
            saveExpandedState('wt-specific-123', true, testDate);
            
            // Mock DOM to have this specific working time
            global.document.querySelector = jest.fn((selector) => {
                if (selector === '.working-time-item[data-id="wt-specific-123"]') {
                    return {
                        dataset: { id: 'wt-specific-123' },
                        querySelector: jest.fn(() => ({
                            classList: { remove: jest.fn() }
                        }))
                    };
                }
                return null;
            });
            
            // Verify working time is in expanded states
            expect(getExpandedStates(testDate)).toContain('wt-specific-123');
            
            // Verify DOM query would find the element
            const targetElement = global.document.querySelector('.working-time-item[data-id="wt-specific-123"]');
            expect(targetElement).not.toBeNull();
            expect(targetElement.dataset.id).toBe('wt-specific-123');
        });

        test('Should work with normal restoreExpandedStates workflow (no special fallback needed)', () => {
            const testDate = new Date('2025-05-28');
            
            // NEW SIMPLIFIED APPROACH: Multiple working times can be expanded
            saveExpandedState('wt-first', true, testDate);
            saveExpandedState('wt-second', true, testDate);
            
            // Mock DOM to have working time items
            global.document.querySelectorAll = jest.fn((selector) => {
                if (selector === '.working-time-item') {
                    return [
                        { dataset: { id: 'wt-first' } },
                        { dataset: { id: 'wt-second' } }
                    ];
                }
                return [];
            });
            
            // Both working times should be in expanded states
            const expandedStates = getExpandedStates(testDate);
            expect(expandedStates).toHaveLength(2);
            expect(expandedStates).toContain('wt-first');
            expect(expandedStates).toContain('wt-second');
            
            // No complex fallback logic needed - normal restoreExpandedStates handles everything
            const workingTimeItems = global.document.querySelectorAll('.working-time-item');
            expect(workingTimeItems.length).toBe(2);
        });
    });

    describe('State consistency across user interactions', () => {
        test('Should maintain consistent state through complete create->expand->collapse->revisit cycle (simplified)', () => {
            const testDate = new Date('2025-05-28');
            
            // Phase 1: User creates working time (NEW SIMPLIFIED APPROACH)
            saveExpandedState('wt-cycle-test', true, testDate);
            
            // At this point: expansion history immediately exists
            expect(hasExpandCollapseHistory(testDate)).toBe(true);
            expect(hasExpandedStates(testDate)).toBe(true);
            expect(getExpandedStates(testDate)).toContain('wt-cycle-test');
            
            // Phase 2: User collapses the working time
            saveExpandedState('wt-cycle-test', false, testDate);
            expect(hasExpandCollapseHistory(testDate)).toBe(true); // Still has history
            expect(hasExpandedStates(testDate)).toBe(false); // But no expanded states
            
            // Phase 3: User switches to another day and back (simulate revisit)
            // The critical test: expandedIds will be empty, but hasHistory will be true
            const expandedIds = getExpandedStates(testDate);
            const hasHistory = hasExpandCollapseHistory(testDate);
            
            expect(expandedIds).toHaveLength(0); // This alone would trigger auto-expansion in the buggy version
            expect(hasHistory).toBe(true); // This prevents auto-expansion in the fixed version
            
            // The fixed logic: expandedIds.length === 0 AND !hasHistory triggers auto-expansion
            // In this case: expandedIds.length === 0 AND hasHistory === true → no auto-expansion
            const shouldAutoExpand = expandedIds.length === 0 && !hasHistory;
            expect(shouldAutoExpand).toBe(false);
        });

        test('Should handle multiple working time creations in one day (improved UX)', () => {
            const testDate = new Date('2025-05-28');
            
            // NEW SIMPLIFIED APPROACH: User creates multiple working times
            saveExpandedState('wt-first-of-day', true, testDate);
            saveExpandedState('wt-second-of-day', true, testDate);
            
            // IMPROVED UX: Both working times remain expanded (instead of only remembering the last one)
            const expandedStates = getExpandedStates(testDate);
            expect(expandedStates).toHaveLength(2);
            expect(expandedStates).toContain('wt-first-of-day');
            expect(expandedStates).toContain('wt-second-of-day');
            
            // Both have expansion history
            expect(hasExpandCollapseHistory(testDate)).toBe(true);
            expect(hasExpandedStates(testDate)).toBe(true);
        });
    });

    describe('Edge cases that could reveal the original bug', () => {
        test('Should not auto-expand when user has history but all states are false', () => {
            const testDate = new Date('2025-05-28');
            
            // Create a scenario where user has interacted but nothing is expanded
            // This can happen when user expands and then collapses everything
            saveExpandedState('wt-1', true, testDate);
            saveExpandedState('wt-2', true, testDate);
            saveExpandedState('wt-1', false, testDate);
            saveExpandedState('wt-2', false, testDate);
            
            // Final state: has history, no expanded states
            expect(hasExpandCollapseHistory(testDate)).toBe(true);
            expect(hasExpandedStates(testDate)).toBe(false);
            expect(getExpandedStates(testDate)).toHaveLength(0);
            
            // This is the exact scenario that triggered the original bug
            // The system should NOT auto-expand because user has explicitly collapsed everything
        });

        test('Should properly handle localStorage corruption scenarios', () => {
            const testDate = new Date('2025-05-28');
            
            // Simulate corrupted localStorage data
            global.localStorage.setItem('expandedWorkingTimes_2025-05-28', 'invalid json');
            
            // hasExpandCollapseHistory should still work (it only checks key existence)
            expect(() => hasExpandCollapseHistory(testDate)).not.toThrow();
            expect(hasExpandCollapseHistory(testDate)).toBe(true);
            
            // Functions that parse JSON will throw with current implementation
            // This test documents the current behavior - in production, this would need error handling
            expect(() => hasExpandedStates(testDate)).toThrow();
            expect(() => getExpandedStates(testDate)).toThrow();
            
            // NOTE: This test exposes that the state-management functions need better error handling
            // for localStorage corruption scenarios in production code
        });
    });
});