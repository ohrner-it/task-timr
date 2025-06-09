/**
 * Sorting utilities for working times and other data structures
 * 
 * This module provides pure functions for sorting operations that can be
 * easily tested and reused across the application.
 */

/**
 * Sort working times by start time
 * @param {Array} workingTimes - Array of working time objects
 * @param {string} order - Sort order: 'asc' for earliest first, 'desc' for latest first
 * @returns {Array} - New sorted array (does not mutate original)
 */
export function sortWorkingTimesByStartTime(workingTimes, order = 'desc') {
    if (!Array.isArray(workingTimes)) {
        throw new Error('workingTimes must be an array');
    }
    
    if (!['asc', 'desc'].includes(order)) {
        throw new Error('order must be either "asc" or "desc"');
    }
    
    // Validate data before sorting
    for (let i = 0; i < workingTimes.length; i++) {
        const workingTime = workingTimes[i];
        if (!workingTime.hasOwnProperty('start')) {
            throw new Error('Working time objects must have a start property');
        }
        
        const testDate = new Date(workingTime.start);
        if (isNaN(testDate.getTime())) {
            throw new Error('Working time start values must be valid date strings');
        }
    }
    
    // Create a copy to avoid mutating the original array
    return [...workingTimes].sort((a, b) => {
        const dateA = new Date(a.start);
        const dateB = new Date(b.start);
        
        if (order === 'desc') {
            return dateB - dateA; // Latest first
        } else {
            return dateA - dateB; // Earliest first
        }
    });
}

/**
 * Sort working times in descending order (latest first) - convenience function
 * @param {Array} workingTimes - Array of working time objects
 * @returns {Array} - New sorted array with latest working times first
 */
export function sortWorkingTimesLatestFirst(workingTimes) {
    return sortWorkingTimesByStartTime(workingTimes, 'desc');
}

/**
 * Sort working times in ascending order (earliest first) - convenience function
 * @param {Array} workingTimes - Array of working time objects
 * @returns {Array} - New sorted array with earliest working times first
 */
export function sortWorkingTimesEarliestFirst(workingTimes) {
    return sortWorkingTimesByStartTime(workingTimes, 'asc');
}

/**
 * Sort tasks by name (alphabetical order) with ID fallback
 * @param {Array} tasks - Array of task objects
 * @param {string} order - Sort order: 'asc' for A-Z, 'desc' for Z-A
 * @param {Function} nameExtractor - Function to extract name from task object (default: auto-detect 'name' or 'title')
 * @param {Function} idExtractor - Function to extract ID from task object (default: extracts 'id' field)
 * @returns {Array} - New sorted array (does not mutate original)
 */
export function sortTasksByName(tasks, order = 'asc', nameExtractor = null, idExtractor = null) {
    if (!Array.isArray(tasks)) {
        throw new Error('tasks must be an array');
    }
    
    if (!['asc', 'desc'].includes(order)) {
        throw new Error('order must be either "asc" or "desc"');
    }
    
    // Default extractors
    const defaultNameExtractor = (task) => task.name || task.title || "";
    const defaultIdExtractor = (task) => task.id || "";
    
    const getName = nameExtractor || defaultNameExtractor;
    const getId = idExtractor || defaultIdExtractor;
    
    // Create a copy to avoid mutating the original array
    return [...tasks].sort((a, b) => {
        const nameA = getName(a) || "";
        const nameB = getName(b) || "";
        
        const nameComparison = nameA.localeCompare(nameB);
        
        // If names are the same, sort by ID as fallback
        if (nameComparison === 0) {
            const idA = getId(a) || "";
            const idB = getId(b) || "";
            const idComparison = idA.localeCompare(idB);
            return order === 'desc' ? -idComparison : idComparison;
        }
        
        return order === 'desc' ? -nameComparison : nameComparison;
    });
}

/**
 * Sort UI project times by task name with ID fallback
 * @param {Array} uiProjectTimes - Array of UI project time objects
 * @param {string} order - Sort order: 'asc' for A-Z, 'desc' for Z-A
 * @returns {Array} - New sorted array (does not mutate original)
 */
export function sortUIProjectTimesByTaskName(uiProjectTimes, order = 'asc') {
    if (!Array.isArray(uiProjectTimes)) {
        throw new Error('uiProjectTimes must be an array');
    }
    
    if (!['asc', 'desc'].includes(order)) {
        throw new Error('order must be either "asc" or "desc"');
    }
    
    // Reuse sortTasksByName with lambda extractors for UI project times
    return sortTasksByName(
        uiProjectTimes, 
        order,
        (uiProjectTime) => uiProjectTime.task_name || "",
        (uiProjectTime) => uiProjectTime.task_id || ""
    );
}

/**
 * Sort tasks alphabetically (A-Z) - convenience function
 * @param {Array} tasks - Array of task objects
 * @returns {Array} - New sorted array with tasks in alphabetical order
 */
export function sortTasksAlphabetically(tasks) {
    return sortTasksByName(tasks, 'asc');
}

/**
 * Sort UI project times by task name (A-Z) - convenience function
 * @param {Array} uiProjectTimes - Array of UI project time objects
 * @returns {Array} - New sorted array with project times sorted by task name
 */
export function sortUIProjectTimesAlphabetically(uiProjectTimes) {
    return sortUIProjectTimesByTaskName(uiProjectTimes, 'asc');
}