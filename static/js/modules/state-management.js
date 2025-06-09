/**
 * State Management Module
 * Functions for managing localStorage state and UI state
 * Can be used in both browser and Node.js (Jest) environments
 */

import { getDateKey } from './time-utils.js';

/**
 * Save expanded state for a working time
 * @param {string} workingTimeId - ID of the working time
 * @param {boolean} isExpanded - Whether the working time is expanded
 * @param {Date} currentViewDate - Current view date
 */
export function saveExpandedState(workingTimeId, isExpanded, currentViewDate) {
    const dateKey = getDateKey(currentViewDate);
    const storageKey = `expandedWorkingTimes_${dateKey}`;

    // Mock localStorage for Node.js testing environment
    const storage = typeof localStorage !== 'undefined' ? localStorage : {
        getItem: () => null,
        setItem: () => {},
        removeItem: () => {},
        clear: () => {}
    };

    let expandedIds = JSON.parse(storage.getItem(storageKey) || "[]");

    if (isExpanded && !expandedIds.includes(workingTimeId)) {
        expandedIds.push(workingTimeId);
    } else if (!isExpanded) {
        expandedIds = expandedIds.filter((id) => id !== workingTimeId);
    }

    storage.setItem(storageKey, JSON.stringify(expandedIds));
    
    // Only log in browser environment
    if (typeof console !== 'undefined') {
        console.log(`Saved expansion state for ${workingTimeId}: ${isExpanded}`);
    }
}

/**
 * Get expanded states for current date
 * @param {Date} currentViewDate - Current view date
 * @returns {Array} - Array of expanded working time IDs
 */
export function getExpandedStates(currentViewDate) {
    const dateKey = getDateKey(currentViewDate);
    const storageKey = `expandedWorkingTimes_${dateKey}`;
    
    // Mock localStorage for Node.js testing environment
    const storage = typeof localStorage !== 'undefined' ? localStorage : {
        getItem: () => null,
        setItem: () => {},
        removeItem: () => {},
        clear: () => {}
    };
    
    return JSON.parse(storage.getItem(storageKey) || "[]");
}

/**
 * Find the most recently expanded working time
 * @param {NodeList} workingTimeItems - All working time DOM elements
 * @param {Date} currentViewDate - Current view date
 * @returns {string|null} - Working time ID or null if none expanded
 */
export function findMostRecentlyExpandedWorkingTime(workingTimeItems, currentViewDate) {
    const expandedWorkingTimes = Array.from(workingTimeItems)
        .filter((item) => {
            const detailsSection = item.querySelector(".working-time-details");
            return (
                detailsSection && !detailsSection.classList.contains("d-none")
            );
        })
        .map((item) => item.dataset.id);

    if (expandedWorkingTimes.length === 0) {
        return null;
    }

    // Find the most recently expanded one based on localStorage order
    const expandedIds = getExpandedStates(currentViewDate);
    for (let i = expandedIds.length - 1; i >= 0; i--) {
        if (expandedWorkingTimes.includes(expandedIds[i])) {
            return expandedIds[i];
        }
    }

    // If no match in order, use the first expanded one
    return expandedWorkingTimes[0];
}