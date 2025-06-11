/**
 * Timr.com Alternative Frontend - Main JavaScript
 *
 * This script provides the core functionality for the Timr.com alternative frontend,
 * focusing on a task-oriented approach to time tracking instead of time slots.
 * It integrates with project-time-handler.js for project time specific operations.
 */

// Import utility modules
import { 
    parseTimeToMinutes, 
    getCurrentTimeMinutes, 
    calculateTimeDistance, 
    formatDateTimeForAPI, 
    formatDuration, 
    getDateKey 
} from './modules/time-utils.js';
import { escapeHtml, extractTimeRangeFromWorkingTime } from './modules/dom-utils.js';
import { saveExpandedState, getExpandedStates, findMostRecentlyExpandedWorkingTime } from './modules/state-management.js';
import { logMessage, showAlert, debounce, logApiError } from './modules/ui-utils.js';
import { sortWorkingTimesLatestFirst, sortTasksAlphabetically } from './modules/sorting-utils.js';
import { openTimeAllocationModal, openDistributeTimeModal, fetchUIProjectTimes, renderUIProjectTimes, renderTimeAllocationProgress } from './project-time-handler.js';



// Global variables for direct access
let currentViewDate = null;
let isEditingWorkingTime = false;

// Helper functions for expansion state storage - now using imported modules
function getDateKeyWrapper() {
    return getDateKey(currentViewDate);
}

function saveExpandedStateWrapper(workingTimeId, isExpanded) {
    saveExpandedState(workingTimeId, isExpanded, currentViewDate);
}

function getExpandedStatesWrapper() {
    return getExpandedStates(currentViewDate);
}

function restoreExpandedStates() {
    // Get expanded working time IDs from storage
    const expandedIds = getExpandedStatesWrapper();

    if (expandedIds.length === 0) {
        return; // No expanded states to restore
    }

    console.log(
        `Restoring expanded states for ${expandedIds.length} working times`,
    );

    // For each saved ID, expand the corresponding working time details
    expandedIds.forEach((workingTimeId) => {
        const workingTimeItem = document.querySelector(
            `.working-time-item[data-id="${workingTimeId}"]`,
        );
        if (!workingTimeItem) return;

        const detailsSection = workingTimeItem.querySelector(
            ".working-time-details",
        );
        const toggleButton = workingTimeItem.querySelector(".toggle-details");
        const icon = toggleButton?.querySelector("i");

        if (detailsSection && toggleButton && icon) {
            // Show details section
            detailsSection.classList.remove("d-none");

            // Update icon
            icon.className = "bi bi-chevron-up";

            // Let the user see the expanded state first, then try to load project times
            setTimeout(() => {
                try {
                    // Try to load project times for this working time
                    const container = document.getElementById(
                        `project-times-${workingTimeId}`,
                    );
                    if (container) {
                        // The UI is already expanded, let's try to load the data
                        fetchUIProjectTimes(workingTimeId)
                            .then((data) => {
                                renderUIProjectTimes(data, {
                                    id: workingTimeId,
                                });
                                renderTimeAllocationProgress(
                                    data,
                                    workingTimeId,
                                );
                            })
                            .catch((err) => {
                                console.error(
                                    `Could not load details for ${workingTimeId}: ${err.message}`,
                                );
                                // Show user-friendly error notification
                                showAlert(
                                    `Failed to load time allocations: ${err.message}`,
                                    "warning",
                                );
                                
                                // Show inline error in the working time card
                                container.innerHTML = `
                                    <div class="alert alert-warning alert-sm mb-2">
                                        <i class="bi bi-exclamation-triangle me-2"></i>
                                        Failed to load time allocations
                                    </div>
                                `;
                            });
                    }
                } catch (err) {
                    console.error(
                        `Error loading details for expanded working time: ${err.message}`,
                    );
                    // Show user-friendly error notification
                    showAlert(
                        `Error restoring expanded working time: ${err.message}`,
                        "danger",
                    );
                }
            }, 100);
        }
    });
}

/**
 * Smart algorithm to find the best working time for adding time allocations
 * Prioritizes expanded working times, then falls back to time-based heuristics
 *
 * @returns {string|null} - Working time ID to target, or null if none found
 */
function findBestWorkingTimeForTimeAllocation() {
    const workingTimeItems = document.querySelectorAll(".working-time-item");
    if (workingTimeItems.length === 0) {
        return null;
    }

    // Strategy 1: Prefer expanded working times
    const expandedWorkingTime =
        findMostRecentlyExpandedWorkingTimeWrapper(workingTimeItems);
    if (expandedWorkingTime) {
        console.log(
            `Selected working time ${expandedWorkingTime} (most recently expanded)`,
        );
        return expandedWorkingTime;
    }

    // Strategy 2: Time-based heuristic
    const timeBasedWorkingTime = findWorkingTimeByCurrentTime(workingTimeItems);
    if (timeBasedWorkingTime) {
        console.log(
            `Selected working time ${timeBasedWorkingTime.id} (time-based heuristic, score: ${timeBasedWorkingTime.score})`,
        );
        return timeBasedWorkingTime.id;
    }

    // Strategy 3: Fallback to first working time
    const firstWorkingTime = workingTimeItems[0].dataset.id;
    console.log(
        `Selected working time ${firstWorkingTime} (fallback to first)`,
    );
    return firstWorkingTime;
}

/**
 * Find the most recently expanded working time - wrapper for imported function
 *
 * @param {NodeList} workingTimeItems - All working time DOM elements
 * @returns {string|null} - Working time ID or null if none expanded
 */
function findMostRecentlyExpandedWorkingTimeWrapper(workingTimeItems) {
    return findMostRecentlyExpandedWorkingTime(workingTimeItems, currentViewDate);
}

/**
 * Find working time closest to current time of day
 *
 * @param {NodeList} workingTimeItems - All working time DOM elements
 * @returns {Object|null} - Object with id and score, or null if none found
 */
function findWorkingTimeByCurrentTime(workingTimeItems) {
    const currentTimeMinutes = getCurrentTimeMinutes();
    let bestMatch = null;
    let bestScore = Infinity;

    Array.from(workingTimeItems).forEach((item) => {
        try {
            const timeRange = extractTimeRangeFromWorkingTime(item);
            if (!timeRange) return;

            const score = calculateTimeDistance(
                currentTimeMinutes,
                timeRange.start,
                timeRange.end,
            );
            if (score < bestScore) {
                bestScore = score;
                bestMatch = item.dataset.id;
            }
        } catch (error) {
            console.log(
                `Error processing working time for selection: ${error.message}`,
            );
        }
    });

    return bestMatch ? { id: bestMatch, score: bestScore } : null;
}

// getCurrentTimeMinutes is now imported from modules/time-utils.js

// extractTimeRangeFromWorkingTime is now imported from modules/dom-utils.js

// calculateTimeDistance is now imported from modules/time-utils.js

// parseTimeToMinutes is now imported from modules/time-utils.js

// formatDateTimeForAPI is now imported from modules/time-utils.js

// showAlert is now imported from modules/ui-utils.js - but we need to expose it globally for templates
window.showAlert = showAlert;

// formatDuration is now imported from modules/time-utils.js

// escapeHtml is now imported from modules/dom-utils.js

// logMessage is now imported from modules/ui-utils.js

document.addEventListener("DOMContentLoaded", function () {
    // Initialize state object
    const state = {
        date: new Date(),
        workingTimes: [],
        tasks: [],
        recentTasks: [],
        workingTimeTypes: [],
        // Track which working times are expanded
        expandedWorkingTimes: new Set(),
    };

    // Initialize UI event handlers
    setupEventHandlers();

    // Only load data if user is authenticated (check if user info exists)
    const userInfo = document.getElementById('user-info');
    if (userInfo) {
        // Load initial data only when user is logged in
        loadCurrentDateData();
        loadRecentTasks();
    }

    /**
     * Set up all event handlers for the UI
     */
    function setupEventHandlers() {
        // Date navigation
        document
            .getElementById("prev-date")
            ?.addEventListener("click", navigatePreviousDay);
        document
            .getElementById("today")
            ?.addEventListener("click", navigateToday);
        document
            .getElementById("next-date")
            ?.addEventListener("click", navigateNextDay);

        // Add keyboard shortcuts for navigation
        document.addEventListener("keydown", handleKeyboardShortcuts);

        // Working time form
        document
            .getElementById("new-working-time-btn")
            ?.addEventListener("click", openNewWorkingTimeModal);
        document
            .getElementById("working-time-form")
            ?.addEventListener("submit", saveWorkingTime);

        // Task selection and time allocation
        document
            .getElementById("task-search")
            ?.addEventListener("input", debounce(handleTaskSearch, 300));
        document
            .getElementById("time-allocation-form")
            ?.addEventListener("submit", saveTimeAllocation);

        // Task selection clearing
        document
            .getElementById("clear-selected-task")
            ?.addEventListener("click", clearSelectedTask);

        // Duration quick buttons
        document.querySelectorAll("[data-duration]").forEach((btn) => {
            btn.addEventListener("click", function () {
                const duration = parseInt(this.getAttribute("data-duration"));
                document.getElementById("time-allocation-duration").value =
                    duration;
                updateDurationButtonStates();
            });
        });

        // Duration max button
        document
            .getElementById("duration-max")
            ?.addEventListener("click", function () {
                const form = document.getElementById("time-allocation-form");
                const remainingDuration = form?.dataset.remainingDuration;
                
                if (remainingDuration && parseInt(remainingDuration) > 0) {
                    const input = document.getElementById("time-allocation-duration");
                    input.value = remainingDuration;
                    updateDurationButtonStates();
                }
            });

        // Duration input field changes
        document
            .getElementById("time-allocation-duration")
            ?.addEventListener("input", function () {
                updateDurationButtonStates();
            });

        // Duration +/- buttons
        document
            .getElementById("duration-increase")
            ?.addEventListener("click", function () {
                const input = document.getElementById(
                    "time-allocation-duration",
                );
                input.value = Math.max(0, parseInt(input.value || 0) + 15);
                updateDurationButtonStates();
            });

        document
            .getElementById("duration-decrease")
            ?.addEventListener("click", function () {
                const input = document.getElementById(
                    "time-allocation-duration",
                );
                input.value = Math.max(15, parseInt(input.value || 0) - 15);
                updateDurationButtonStates();
            });

        // Clear modals on close
        document.querySelectorAll(".modal").forEach((modal) => {
            modal.addEventListener("hidden.bs.modal", resetModalForms);
        });
    }

    /**
     * Handle keyboard shortcuts
     */
    function handleKeyboardShortcuts(event) {
        // Handle Ctrl+S and Ctrl+Shift+S in modals (these work even in input fields)
        if (event.ctrlKey && event.key.toLowerCase() === "s") {
            // Check if we're in the working time modal
            const workingTimeModal = document.getElementById("working-time-modal");
            const timeAllocationModal = document.getElementById("time-allocation-modal");
            
            if (workingTimeModal && workingTimeModal.classList.contains("show")) {
                // Working Time modal is open
                event.preventDefault();
                const form = document.getElementById("working-time-form");
                if (form) {
                    form.dispatchEvent(new Event('submit'));
                }
                return;
            }
            
            if (timeAllocationModal && timeAllocationModal.classList.contains("show")) {
                // Time Allocation modal is open
                event.preventDefault();
                
                if (event.shiftKey) {
                    // Ctrl+Shift+S = Save and Add New
                    const saveAndAddNewBtn = document.getElementById("save-and-add-new-btn");
                    if (saveAndAddNewBtn) {
                        saveAndAddNewBtn.click();
                    }
                } else {
                    // Ctrl+S = Save
                    const form = document.getElementById("time-allocation-form");
                    if (form) {
                        form.dispatchEvent(new Event('submit'));
                    }
                }
                return;
            }
        }

        // Handle Ctrl+0-9 for recent task selection in time allocation modal
        if (event.ctrlKey && /^[0-9]$/.test(event.key)) {
            const timeAllocationModal = document.getElementById("time-allocation-modal");
            if (timeAllocationModal && timeAllocationModal.classList.contains("show")) {
                event.preventDefault();
                const taskNumber = parseInt(event.key);
                const recentTaskElements = document.querySelectorAll('.recent-task-allocation-item[data-shortcut]');
                
                // Find the task with the matching shortcut number
                const targetTask = Array.from(recentTaskElements).find(
                    element => element.dataset.shortcut === taskNumber.toString()
                );
                
                if (targetTask) {
                    selectRecentTask(targetTask);
                }
                return;
            }
        }

        // Only if not in an input field
        if (
            event.target.tagName !== "INPUT" &&
            event.target.tagName !== "TEXTAREA" &&
            event.target.tagName !== "SELECT"
        ) {
            if (event.altKey) {
                // Alt+Left = Previous day
                if (event.key === "ArrowLeft") {
                    navigatePreviousDay();
                    event.preventDefault();
                }
                // Alt+Right = Next day
                else if (event.key === "ArrowRight") {
                    navigateNextDay();
                    event.preventDefault();
                }
                // Alt+T = Today
                else if (event.key.toLowerCase() === "t") {
                    navigateToday();
                    event.preventDefault();
                }
                // Alt+N = New working time
                else if (event.key.toLowerCase() === "n") {
                    openNewWorkingTimeModal();
                    event.preventDefault();
                }
                // Alt+A = Add time allocation to best working time
                else if (event.key.toLowerCase() === "a") {
                    try {
                        const bestWorkingTimeId =
                            findBestWorkingTimeForTimeAllocation();
                        if (bestWorkingTimeId) {
                            openTimeAllocationModal(bestWorkingTimeId);
                            event.preventDefault();
                        } else {
                            showAlert("No working time available for time allocation", "info");
                        }
                    } catch (error) {
                        console.error("Error with Alt+A shortcut:", error);
                        showAlert(`Failed to open time allocation: ${error.message}`, "danger");
                    }
                }
                // Alt+R = Distribute remaining time for best working time
                else if (event.key.toLowerCase() === "r") {
                    try {
                        const bestWorkingTimeId =
                            findBestWorkingTimeForTimeAllocation();
                        if (bestWorkingTimeId) {
                            openDistributeTimeModal(bestWorkingTimeId);
                            event.preventDefault();
                        } else {
                            showAlert("No working time available for time distribution", "info");
                        }
                    } catch (error) {
                        console.error("Error with Alt+R shortcut:", error);
                        showAlert(`Failed to open time distribution: ${error.message}`, "danger");
                    }
                }
            }
            // Escape key closes modals
            else if (event.key === "Escape") {
                closeAllModals();
            }
        }

        // Enhanced keyboard navigation for task search
        if (
            event.target.id === "task-search" ||
            event.target.id === "modal-task-search"
        ) {
            if (event.key === "ArrowDown") {
                // Move focus to first task item
                const firstResult = document.querySelector(".task-item");
                if (firstResult) {
                    firstResult.focus();
                    event.preventDefault();
                }
            } else if (event.key === "Enter") {
                // Select first task item
                const firstResult = document.querySelector(".task-item");
                if (firstResult) {
                    firstResult.click();
                    event.preventDefault();
                }
            }
        } else if (event.target.classList.contains("task-item")) {
            // Navigation within task results
            if (event.key === "ArrowDown") {
                // Move to next task item
                const nextItem = event.target.nextElementSibling;
                if (nextItem) {
                    nextItem.focus();
                    event.preventDefault();
                }
            } else if (event.key === "ArrowUp") {
                // Move to previous task item or back to search input
                const prevItem = event.target.previousElementSibling;
                if (prevItem) {
                    prevItem.focus();
                    event.preventDefault();
                } else {
                    // Move back to search input
                    const searchInput =
                        document.getElementById("task-search") ||
                        document.getElementById("modal-task-search");
                    if (searchInput) {
                        searchInput.focus();
                        event.preventDefault();
                    }
                }
            } else if (event.key === "Enter" || event.key === " ") {
                // Select this task item
                event.target.click();
                event.preventDefault();
            }
        }
    }

    /**
     * Close all open modals
     */
    function closeAllModals() {
        document.querySelectorAll(".modal.show").forEach((modalEl) => {
            const modalInstance = bootstrap.Modal.getInstance(modalEl);
            if (modalInstance) {
                modalInstance.hide();
            }
        });
    }

    /**
     * Reset modal forms when closed
     */
    function resetModalForms(event) {
        const modal = event.target;
        const form = modal.querySelector("form");
        if (form) {
            form.reset();
        }

        // Clear alerts
        const alerts = modal.querySelector(".modal-alerts");
        if (alerts) {
            alerts.innerHTML = "";
        }

        // Clear task selection
        if (modal.id === "time-allocation-modal") {
            const selectedContainer = document.getElementById(
                "selected-task-container",
            );
            if (selectedContainer) {
                selectedContainer.classList.add("d-none");
            }
            document.getElementById("selected-task-id").value = "";
            document.getElementById("selected-task-name").textContent = "";
        }
    }

    /**
     * Navigate to the previous day
     */
    function navigatePreviousDay() {
        const date = new Date(state.date);
        date.setDate(date.getDate() - 1);
        loadData(formatDate(date));
    }

    /**
     * Navigate to today
     */
    function navigateToday() {
        loadData(formatDate(new Date()));
    }

    /**
     * Navigate to the next day
     */
    function navigateNextDay() {
        const date = new Date(state.date);
        date.setDate(date.getDate() + 1);
        loadData(formatDate(date));
    }

    /**
     * Load data for the current date
     */
    function loadCurrentDateData() {
        const today = new Date();
        loadData(formatDate(today));
    }

    /**
     * Load working time types and store in state
     */
    function ensureWorkingTimeTypesLoaded() {
        if (!state.allWorkingTimeTypes || state.allWorkingTimeTypes.length === 0) {
            return loadWorkingTimeTypes();
        }
        return Promise.resolve(state.allWorkingTimeTypes);
    }

    /**
     * Load data for a specific date
     */
    function loadData(dateString) {
        // Check if we're coming from an edit - use the stored date from localStorage if available
        const storedDate = localStorage.getItem("currentViewDate");
        if (storedDate) {
            logMessage(
                `Using stored date from localStorage: ${storedDate}`,
                "info",
            );
            dateString = storedDate;
            // Clear it after use
            localStorage.removeItem("currentViewDate");
        }

        if (!dateString) {
            dateString = formatDate(new Date());
        }

        // Update state date
        state.date = new Date(dateString);

        // Store current view date globally
        currentViewDate = dateString;

        // Update UI date display
        updateDateDisplay(state.date);

        // Show loading indicator
        const container = document.getElementById("working-times-container");
        if (container) {
            container.innerHTML = `
                <div class="text-center my-5">
                    <div class="spinner-border text-primary" role="status">
                        <span class="visually-hidden">Loading...</span>
                    </div>
                    <p class="mt-2">Loading working times...</p>
                </div>
            `;
        }

        // Ensure working time types are loaded first, then fetch working times
        ensureWorkingTimeTypesLoaded()
            .then(() => {
                // Fetch working times from API
                return fetch(`/api/working-times?date=${dateString}`)
                    .then(response => handleApiResponse(response, {
                        operation: "fetch working times",
                        requestUrl: `/api/working-times?date=${dateString}`,
                        requestMethod: "GET",
                        date: dateString
                    }));
            })
            .then((data) => {
                state.workingTimes = data.data || [];
                renderWorkingTimes();
            })
            .catch((error) => {
                const errorMessage = `Error loading working times: ${error.message}`;
                logMessage(errorMessage, "error", { date: dateString, error });
                
                // Check if this is an authentication error
                if (error.message.includes("log in") || error.message.includes("Authentication")) {
                    renderAuthenticationRequired();
                    showAlert(error.message, "warning");
                } else {
                    showAlert(errorMessage, "danger");
                    renderEmptyWorkingTimes();
                }
            });
    }

    /**
     * Update the date display in the UI
     */
    function updateDateDisplay(date) {
        const dateDisplay = document.getElementById("date-display");
        if (dateDisplay) {
            dateDisplay.textContent = date.toLocaleDateString(undefined, {
                weekday: "long",
                year: "numeric",
                month: "long",
                day: "numeric",
            });
        }

        const dateInput = document.getElementById("date-input");
        if (dateInput) {
            dateInput.value = formatDate(date);
        }
    }

    /**
     * Render working times list
     */
    function renderWorkingTimes() {
        const container = document.getElementById("working-times-container");
        if (!container) return;

        // If no working times, show empty state
        if (state.workingTimes.length === 0) {
            renderEmptyWorkingTimes();
            return;
        }

        // Sort working times by start time (latest first)
        state.workingTimes = sortWorkingTimesLatestFirst(state.workingTimes);

        // Render each working time
        let html = "";
        state.workingTimes.forEach((workingTime) => {
            html += renderWorkingTimeCard(workingTime);
        });

        container.innerHTML = html;

        // Initialize feather icons if available
        if (typeof feather !== "undefined") {
            feather.replace();
        }

        // Add event listeners to the working time cards
        setupWorkingTimeCardEvents();

        // Apply expanded states from localStorage
        restoreExpandedStates();
    }

    /**
     * Render authentication required message
     */
    function renderAuthenticationRequired() {
        const container = document.getElementById("working-times-container");
        if (!container) return;

        container.innerHTML = `
            <div class="card border-warning">
                <div class="card-body text-center py-5">
                    <div class="mb-4">
                        <i class="bi bi-shield-lock" style="font-size: 3rem; color: var(--bs-warning);"></i>
                    </div>
                    <h4>Login Required</h4>
                    <p class="text-muted mb-4">Please log in to your Timr account to view and manage working times.</p>
                    <div class="d-flex justify-content-center gap-2">
                        <button class="btn btn-warning" onclick="document.querySelector('#username').focus()">
                            <i class="bi bi-box-arrow-in-right me-1"></i> Go to Login
                        </button>
                        <button class="btn btn-outline-secondary" onclick="location.reload()">
                            <i class="bi bi-arrow-clockwise me-1"></i> Refresh
                        </button>
                    </div>
                </div>
            </div>
        `;
    }

    /**
     * Render empty state for working times
     */
    function renderEmptyWorkingTimes() {
        const container = document.getElementById("working-times-container");
        if (!container) return;

        container.innerHTML = `
            <div class="card">
                <div class="card-body text-center py-5">
                    <div class="mb-4">
                        <i class="bi bi-calendar-x" style="font-size: 3rem; color: var(--bs-secondary);"></i>
                    </div>
                    <h4>No working times for this day</h4>
                    <p class="text-muted">Add a working time to start tracking your work.</p>
                    <button id="add-first-working-time" class="btn btn-primary">
                        <i class="bi bi-plus-circle me-1"></i> Add Working Time
                    </button>
                </div>
            </div>
        `;

        // Add event listener to the add button
        document
            .getElementById("add-first-working-time")
            ?.addEventListener("click", openNewWorkingTimeModal);
    }

    /**
     * Render a working time card
     */
    function renderWorkingTimeCard(workingTime) {
        const startTime = new Date(workingTime.start);
        const endTime = new Date(workingTime.end);
        const workingTimeId = workingTime.id;

        // Calculate duration
        const durationMinutes = calculateDurationInMinutes(
            workingTime.start,
            workingTime.end,
        );
        let breakMinutes = workingTime.break_time_total_minutes || 0;

        // Calculate net duration (working time minus break)
        const netDurationMinutes = durationMinutes - breakMinutes;

        // Check if this working time type is editable (attendance_time category)
        const workingTimeType = workingTime.working_time_type || {};
        const workingTimeTypeName = workingTimeType.name || 'Unknown Type';
        
        // Check if the working time type is in the attendance types list (editable types)
        const isEditable = state.attendanceTypes && state.attendanceTypes.some(type => 
            type.id === workingTimeType.id
        );

        return `
            <div class="card mb-3 working-time-item" data-id="${workingTimeId}" data-editable="${isEditable}">
                <div class="card-header d-flex justify-content-between align-items-center">
                    <div>
                        <span class="me-3 fw-bold">${formatTimeFromISOString(workingTime.start)} - ${formatTimeFromISOString(workingTime.end)}</span>
                        ${isEditable ? 
                            `<span class="badge bg-secondary">${formatDuration(netDurationMinutes)}</span>
                            ${breakMinutes > 0 ? `<span class="badge bg-info ms-1">Break: ${formatDuration(breakMinutes)}</span>` : ""}` :
                            `<span class="badge bg-warning">Read-only</span>`
                        }
                        <span class="badge bg-light text-dark ms-1" title="Working Time Type">${workingTimeTypeName}</span>
                    </div>
                    <div class="btn-group btn-group-sm" role="group" aria-label="Working time actions">
                        ${isEditable ? 
                            `<button type="button" class="btn btn-outline-secondary toggle-details" title="Toggle details" aria-label="Toggle details">
                                <i class="bi bi-chevron-down"></i>
                            </button>
                            <button type="button" class="btn btn-outline-primary edit-working-time" title="Edit working time" aria-label="Edit working time">
                                <i class="bi bi-pencil"></i>
                            </button>
                            <button type="button" class="btn btn-outline-danger delete-working-time" title="Delete working time" aria-label="Delete working time">
                                <i class="bi bi-trash"></i>
                            </button>` :
                            `<button type="button" class="btn btn-outline-secondary" disabled title="Read-only - non-attendance time types cannot be edited">
                                <i class="bi bi-lock"></i>
                            </button>`
                        }
                    </div>
                </div>
                <div class="working-time-details d-none">
                    <div class="card-body">
                        <div id="time-allocation-${workingTimeId}" class="time-allocation mb-3">
                            <!-- Time allocation progress will be populated here -->
                            <div class="text-center">
                                <div class="spinner-border spinner-border-sm text-secondary" role="status">
                                    <span class="visually-hidden">Loading...</span>
                                </div>
                                <span class="ms-2">Loading time allocations...</span>
                            </div>
                        </div>

                        <div class="d-flex justify-content-between mb-3">
                            <h5>Time Allocations</h5>
                            <div class="btn-group btn-group-sm" role="group" aria-label="Time allocation actions">
                                <button type="button" class="btn btn-primary add-time-allocation" title="Add time allocation (Alt+A)">
                                    <i data-feather="plus"></i> Add Time
                                </button>
                                <button type="button" class="btn btn-outline-secondary distribute-time" title="Distribute remaining time (Alt+R)">
                                    <i data-feather="share-2"></i> Add Remaining Time
                                </button>
                            </div>
                        </div>

                        <div id="project-times-${workingTimeId}" class="project-times mb-3">
                            <!-- UI Project times will be loaded here -->
                            <div class="text-center my-3">
                                <div class="spinner-border spinner-border-sm text-secondary" role="status">
                                    <span class="visually-hidden">Loading project times...</span>
                                </div>
                                <span class="ms-2">Loading time allocations...</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    /**
     * Setup event handlers for working time cards
     */
    function setupWorkingTimeCardEvents() {
        // Toggle details
        document.querySelectorAll(".toggle-details").forEach((btn) => {
            btn.addEventListener("click", function () {
                const workingTimeItem = this.closest(".working-time-item");
                const workingTimeId = workingTimeItem.dataset.id;
                const detailsSection = workingTimeItem.querySelector(
                    ".working-time-details",
                );

                // Toggle details section
                detailsSection.classList.toggle("d-none");

                // Update icon
                const icon = this.querySelector("i");
                if (detailsSection.classList.contains("d-none")) {
                    icon.className = "bi bi-chevron-down";
                    // Save collapsed state
                    saveExpandedStateWrapper(workingTimeId, false);
                } else {
                    icon.className = "bi bi-chevron-up";
                    // Save expanded state
                    saveExpandedStateWrapper(workingTimeId, true);

                    // Load project times when expanding
                    loadProjectTimesForWorkingTime(workingTimeId);
                }
            });
        });

        // Edit working time
        document.querySelectorAll(".edit-working-time").forEach((btn) => {
            btn.addEventListener("click", function () {
                const workingTimeId =
                    this.closest(".working-time-item").dataset.id;
                editWorkingTime(workingTimeId);
            });
        });

        // Delete working time
        document.querySelectorAll(".delete-working-time").forEach((btn) => {
            btn.addEventListener("click", function () {
                const workingTimeId =
                    this.closest(".working-time-item").dataset.id;
                if (
                    confirm(
                        "Are you sure you want to delete this working time?",
                    )
                ) {
                    deleteWorkingTime(workingTimeId);
                }
            });
        });

        // Add time allocation
        document.querySelectorAll(".add-time-allocation").forEach((btn) => {
            btn.addEventListener("click", function () {
                const workingTimeId =
                    this.closest(".working-time-item").dataset.id;
                openTimeAllocationModal(workingTimeId);
            });
        });

        // Distribute remaining time
        document.querySelectorAll(".distribute-time").forEach((btn) => {
            btn.addEventListener("click", function () {
                const workingTimeId =
                    this.closest(".working-time-item").dataset.id;
                openDistributeTimeModal(workingTimeId);
            });
        });
    }

    /**
     * Load project times for a specific working time
     * Uses project-time-handler.js
     */
    function loadProjectTimesForWorkingTime(workingTimeId) {
        const container = document.getElementById(
            `project-times-${workingTimeId}`,
        );
        const timeAllocationContainer = document.getElementById(
            `time-allocation-${workingTimeId}`,
        );

        if (!container || !timeAllocationContainer) return;

        // Use the fetchUIProjectTimes function from project-time-handler.js
        fetchUIProjectTimes(workingTimeId)
            .then((data) => {
                renderUIProjectTimes(data, { id: workingTimeId });
                renderTimeAllocationProgress(data, workingTimeId);
            })
            .catch((error) => {
                showAlert(
                    `Error loading time allocations: ${error.message}`,
                    "danger",
                );
                container.innerHTML = `
                    <div class="alert alert-danger">
                        <i class="bi bi-exclamation-triangle-fill me-2"></i>
                        Failed to load time allocations: ${error.message}
                    </div>
                `;
                timeAllocationContainer.innerHTML = "";
            });
    }

    /**
     * Open the new working time modal
     */
    function openNewWorkingTimeModal() {
        // Reset form
        const form = document.getElementById("working-time-form");
        if (form) {
            form.reset();
            delete form.dataset.workingTimeId;

            // Set default values
            const dateInput = form.querySelector("#working-time-date");
            if (dateInput) {
                dateInput.value = formatDate(state.date);
            }

            const startTimeInput = form.querySelector("#working-time-start");
            if (startTimeInput) {
                startTimeInput.value = "09:00";
            }

            const endTimeInput = form.querySelector("#working-time-end");
            if (endTimeInput) {
                endTimeInput.value = "17:00";
            }

            const pauseDurationInput = form.querySelector(
                "#working-time-pause",
            );
            if (pauseDurationInput) {
                pauseDurationInput.value = "30";
            }
        }

        // Update modal title
        const modalTitle = document.getElementById("working-time-modal-label");
        if (modalTitle) {
            modalTitle.textContent = "New Working Time";
        }

        // Load working time types and populate dropdown
        ensureWorkingTimeTypesLoaded().then(() => {
            const workingTimeTypeSelect = document.getElementById('working-time-type');
            if (workingTimeTypeSelect) {
                populateWorkingTimeTypes(workingTimeTypeSelect);
            }
        });

        // Show modal
        const modal = new bootstrap.Modal(
            document.getElementById("working-time-modal"),
        );
        if (modal) {
            modal.show();
        }
    }

    /**
     * Edit a working time
     */
    function editWorkingTime(workingTimeId) {
        // Set flag to indicate we're editing (this will be used to maintain context)
        isEditingWorkingTime = true;

        // Store current view date before editing
        currentViewDate = formatDate(state.date);
        logMessage(
            `Saved current view date before editing: ${currentViewDate}`,
            "info",
        );

        // Find working time in state
        const workingTime = state.workingTimes.find(
            (wt) => wt.id === workingTimeId,
        );
        if (!workingTime) {
            showAlert("Working time not found", "danger");
            return;
        }

        // Get form
        const form = document.getElementById("working-time-form");
        if (!form) return;

        // Set form values and store working time ID
        form.dataset.workingTimeId = workingTimeId;

        const dateInput = form.querySelector("#working-time-date");
        if (dateInput) {
            dateInput.value = formatDateFromISOString(workingTime.start);
        }

        const startTimeInput = form.querySelector("#working-time-start");
        if (startTimeInput) {
            startTimeInput.value = formatTimeFromISOString(workingTime.start);
        }

        const endTimeInput = form.querySelector("#working-time-end");
        if (endTimeInput) {
            endTimeInput.value = formatTimeFromISOString(workingTime.end);
        }

        const pauseDurationInput = form.querySelector("#working-time-pause");
        if (pauseDurationInput) {
            pauseDurationInput.value =
                workingTime.break_time_total_minutes || 0;
        }

        // Load working time types and populate dropdown, then set the value
        ensureWorkingTimeTypesLoaded().then(() => {
            const workingTimeTypeInput = form.querySelector("#working-time-type");
            if (workingTimeTypeInput) {
                populateWorkingTimeTypes(workingTimeTypeInput);
                if (workingTime.working_time_type) {
                    workingTimeTypeInput.value = workingTime.working_time_type.id || '';
                }
            }
        });

        // Update modal title
        const modalTitle = document.getElementById("working-time-modal-label");
        if (modalTitle) {
            modalTitle.textContent = "Edit Working Time";
        }

        // Show modal
        const modal = new bootstrap.Modal(
            document.getElementById("working-time-modal"),
        );
        if (modal) {
            modal.show();
        }
    }

    /**
     * Save working time (create or update)
     */
    function saveWorkingTime(event) {
        event.preventDefault();

        const form = document.getElementById("working-time-form");
        if (!form) return;

        const workingTimeId = form.dataset.workingTimeId;
        const dateInput = form.querySelector("#working-time-date");
        const startTimeInput = form.querySelector("#working-time-start");
        const endTimeInput = form.querySelector("#working-time-end");
        const pauseDurationInput = form.querySelector("#working-time-pause");
        const workingTimeTypeInput = form.querySelector("#working-time-type");

        if (
            !dateInput ||
            !startTimeInput ||
            !endTimeInput ||
            !pauseDurationInput ||
            !workingTimeTypeInput
        ) {
            showAlert("Form fields not found", "danger", true);
            return;
        }

        const date = dateInput.value;
        const startTime = startTimeInput.value;
        const endTime = endTimeInput.value;
        const pauseDuration = parseInt(pauseDurationInput.value) || 0;
        const workingTimeTypeId = workingTimeTypeInput.value;

        if (!date || !startTime || !endTime || !workingTimeTypeId) {
            showAlert("Please fill in all required fields including working time type", "warning", true);
            return;
        }

        // Create datetime objects in local timezone (no conversion to UTC)
        const startDateTime = new Date(`${date}T${startTime}:00`);
        const endDateTime = new Date(`${date}T${endTime}:00`);

        // Validate start time before end time
        if (startDateTime >= endDateTime) {
            showAlert("Start time must be before end time", "warning", true);
            return;
        }

        // Prepare data for API using local timezone formatting
        const data = {
            start: formatDateTimeForAPI(startDateTime),
            end: formatDateTimeForAPI(endDateTime),
            pause_duration: pauseDuration,
            working_time_type_id: workingTimeTypeId,
        };

        // Show loading state
        const submitBtn = form.querySelector('button[type="submit"]');
        if (submitBtn) {
            submitBtn.disabled = true;
            submitBtn.innerHTML =
                '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Saving...';
        }

        // Determine if this is a create or update operation
        const url = workingTimeId
            ? `/api/working-times/${workingTimeId}`
            : "/api/working-times";

        const method = workingTimeId ? "PATCH" : "POST";

        // Submit to API
        fetch(url, {
            method: method,
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(data),
        })
            .then(handleApiResponse)
            .then((response) => {
                // Close modal
                const modalElement =
                    document.getElementById("working-time-modal");
                const modal = bootstrap.Modal.getInstance(modalElement);
                if (modal) {
                    modal.hide();
                }

                // Show success message
                showAlert(
                    `Working time ${workingTimeId ? "updated" : "created"} successfully`,
                    "success",
                );

                // IMPORTANT: Get the date from the form, not from state
                // This ensures we stay on the date the user was working with
                const selectedDate = dateInput.value;
                console.log(`Loading date from form: ${selectedDate}`);

                // Load data for the date that was in the form
                loadData(selectedDate);
            })
            .catch((error) => {
                showAlert(`Error: ${error.message}`, "danger", true);
            })
            .finally(() => {
                // Reset button state
                if (submitBtn) {
                    submitBtn.disabled = false;
                    submitBtn.innerHTML = "Save";
                }
            });
    }

    /**
     * Delete a working time
     */
    function deleteWorkingTime(workingTimeId) {
        // Show loading indicator
        const workingTimeItem = document.querySelector(
            `.working-time-item[data-id="${workingTimeId}"]`,
        );
        if (workingTimeItem) {
            workingTimeItem.style.opacity = "0.5";
        }

        // Send delete request
        fetch(`/api/working-times/${workingTimeId}`, {
            method: "DELETE",
        })
            .then(handleApiResponse)
            .then((data) => {
                // Show success message
                showAlert("Working time deleted successfully", "success");

                // Remove from state and update UI
                state.workingTimes = state.workingTimes.filter(
                    (wt) => wt.id !== workingTimeId,
                );
                renderWorkingTimes();
            })
            .catch((error) => {
                showAlert(`Error: ${error.message}`, "danger");

                // Reset opacity
                if (workingTimeItem) {
                    workingTimeItem.style.opacity = "1";
                }
            });
    }

    /**
     * Open the time allocation modal - this function is handled by project-time-handler.js
     * The imported openTimeAllocationModal function will be used directly
     */

    /**
     * Open distribute remaining time modal - this function is handled by project-time-handler.js
     * The imported openDistributeTimeModal function will be used directly
     */

    /**
     * Handle task search input
     */
    function handleTaskSearch(event) {
        const searchTerm = event.target.value.trim();
        const resultsContainer = document.getElementById("task-search-results");

        // Clear results if search term is too short
        if (searchTerm.length < 3) {
            if (resultsContainer) {
                resultsContainer.innerHTML = "";
            }
            return;
        }

        // Show loading indicator
        if (resultsContainer) {
            resultsContainer.innerHTML = `
                <div class="p-2 text-center">
                    <div class="spinner-border spinner-border-sm text-secondary" role="status">
                        <span class="visually-hidden">Searching...</span>
                    </div>
                    <span class="ms-2">Searching...</span>
                </div>
            `;
        }

        // Search tasks
        fetch(`/api/tasks/search?q=${encodeURIComponent(searchTerm)}`)
            .then(handleApiResponse)
            .then((data) => {
                // Check if the response contains an error
                if (data.error) {
                    if (resultsContainer) {
                        resultsContainer.innerHTML = `
                            <div class="alert alert-warning m-2 p-2">
                                <small><i class="fas fa-exclamation-triangle me-1"></i>${data.error}</small>
                            </div>
                        `;
                    }
                    return;
                }
                
                const tasks = data.tasks || [];
                renderTaskSearchResults(tasks, resultsContainer);
            })
            .catch((error) => {
                if (resultsContainer) {
                    resultsContainer.innerHTML = `
                        <div class="alert alert-danger m-2 p-2">
                            <small>Search error: ${error.message}</small>
                        </div>
                    `;
                }
            });
    }

    /**
     * Render task search results
     */
    function renderTaskSearchResults(tasks, container) {
        if (!container) return;

        if (tasks.length === 0) {
            container.innerHTML = `
                <div class="p-2 text-center text-muted">
                    No tasks found matching your search.
                </div>
            `;
            return;
        }

        let html = '<div class="list-group">';

        tasks.forEach((task) => {
            const taskName = task.name || task.title || "Unknown Task";
            const taskBreadcrumbs = task.breadcrumbs || "";

            html += `
                <button type="button" class="list-group-item list-group-item-action task-item py-2" 
                    data-id="${task.id}" 
                    data-task-name="${escapeHtml(taskName)}"
                    data-task-breadcrumbs="${escapeHtml(taskBreadcrumbs)}"
                    tabindex="0">
                    <div class="fw-bold">${escapeHtml(taskName)}</div>
                    ${taskBreadcrumbs ? `<small class="text-muted">${escapeHtml(taskBreadcrumbs)}</small>` : ""}
                </button>
            `;
        });

        html += "</div>";
        container.innerHTML = html;

        // Add event listeners to task items
        container.querySelectorAll(".task-item").forEach((item) => {
            item.addEventListener("click", function () {
                selectTask(
                    this.dataset.id,
                    this.dataset.taskName,
                    this.dataset.taskBreadcrumbs,
                );
            });
        });
    }

    /**
     * Load recent tasks
     */
    function loadRecentTasks() {
        fetch("/api/recent-tasks")
            .then(handleApiResponse)
            .then((data) => {
                state.recentTasks = data.tasks || [];
                renderRecentTasks();
                renderRecentTasksAllocation();
            })
            .catch((error) => {
                console.error("Error loading recent tasks:", error);
            });
    }

    /**
     * Render recent tasks
     */
    function renderRecentTasks() {
        const container = document.getElementById("recent-tasks");
        if (!container) return;

        if (state.recentTasks.length === 0) {
            container.innerHTML =
                '<div class="text-muted">No recent tasks</div>';
            return;
        }

        let html = '<div class="list-group">';

        // Sort tasks alphabetically by name
        const sortedTasks = sortTasksAlphabetically(state.recentTasks);

        sortedTasks.forEach((task) => {
            const taskName = task.name || task.title || "Unknown Task";
            const taskBreadcrumbs = task.breadcrumbs || "";

            html += `
                <button type="button" class="list-group-item list-group-item-action recent-task-item py-2" 
                    data-id="${task.id}" 
                    data-task-name="${escapeHtml(taskName)}"
                    data-task-breadcrumbs="${escapeHtml(taskBreadcrumbs)}"
                    tabindex="0">
                    <div class="fw-bold">${escapeHtml(taskName)}</div>
                    ${taskBreadcrumbs ? `<small class="text-muted">${escapeHtml(taskBreadcrumbs)}</small>` : ""}
                </button>
            `;
        });

        html += "</div>";
        container.innerHTML = html;

        // Note: renderRecentTasks() is for the old task search modal which has been removed
        // Recent tasks are now handled by renderRecentTasksAllocation()
    }

    /**
     * Render recent tasks for allocation modal
     */
    function renderRecentTasksAllocation() {
        const container = document.getElementById("recent-tasks-allocation");
        if (!container) return;

        if (state.recentTasks.length === 0) {
            container.innerHTML =
                '<div class="text-muted small">No recent tasks</div>';
            return;
        }

        let html = '<div class="list-group list-group-flush">';

        // Sort tasks alphabetically by name
        const sortedTasks = sortTasksAlphabetically(state.recentTasks);

        sortedTasks.forEach((task, index) => {
            const taskName = task.name || task.title || "Unknown Task";
            const taskBreadcrumbs = task.breadcrumbs || "";
            const shortcutNumber = index < 10 ? index : null;

            // Truncate long task names for compact display in wider sidebar
            const displayName = taskName.length > 35 ? taskName.substring(0, 32) + "..." : taskName;
            const displayBreadcrumbs = taskBreadcrumbs.length > 40 ? taskBreadcrumbs.substring(0, 37) + "..." : taskBreadcrumbs;

            html += `
                <button type="button" class="list-group-item list-group-item-action recent-task-allocation-item py-1 px-2 border-0" 
                    data-id="${task.id}" 
                    data-task-name="${escapeHtml(taskName)}"
                    data-task-breadcrumbs="${escapeHtml(taskBreadcrumbs)}"
                    data-shortcut="${shortcutNumber}"
                    title="${escapeHtml(taskName)}${taskBreadcrumbs ? ' - ' + escapeHtml(taskBreadcrumbs) : ''}"
                    tabindex="0">
                    <div class="d-flex align-items-center">
                        ${shortcutNumber !== null ? `<span class="badge bg-primary me-1" style="min-width: 16px; font-size: 0.7em;">${shortcutNumber}</span>` : ''}
                        <div class="flex-grow-1 text-start">
                            <div class="fw-bold small">${escapeHtml(displayName)}</div>
                            ${taskBreadcrumbs ? `<div class="text-muted" style="font-size: 0.7em; line-height: 1.1;">${escapeHtml(displayBreadcrumbs)}</div>` : ""}
                        </div>
                    </div>
                </button>
            `;
        });

        html += "</div>";
        container.innerHTML = html;

        // Add event listeners to recent task items for allocation modal
        container.querySelectorAll(".recent-task-allocation-item").forEach((item) => {
            item.addEventListener("click", function () {
                selectRecentTask(this);
            });
        });
    }

    /**
     * Select a recent task from the allocation modal
     */
    function selectRecentTask(taskElement) {
        const taskId = taskElement.dataset.id;
        const taskName = taskElement.dataset.taskName;
        const taskBreadcrumbs = taskElement.dataset.taskBreadcrumbs;
        
        // Use the existing selectTask function to properly select the task
        selectTask(taskId, taskName, taskBreadcrumbs);
    }

    /**
     * Select a task
     */
    function selectTask(taskId, taskName, taskBreadcrumbs) {
        const taskIdInput = document.getElementById("selected-task-id");
        const taskNameDisplay = document.getElementById("selected-task-name");
        const selectedTaskContainer = document.getElementById(
            "selected-task-container",
        );

        if (taskIdInput && taskNameDisplay && selectedTaskContainer) {
            taskIdInput.value = taskId;
            taskNameDisplay.textContent = taskName;

            // Make sure the selected task container is visible
            selectedTaskContainer.classList.remove("d-none");

            // Update the alert to show the selected task is different from default
            const alertElement = taskNameDisplay.closest(".alert");
            if (alertElement) {
                alertElement.classList.remove("alert-info");
                alertElement.classList.add("alert-success");

                // Add breadcrumbs if available
                if (taskBreadcrumbs) {
                    // Check if breadcrumbs element already exists
                    let breadcrumbsEl =
                        alertElement.querySelector(".task-breadcrumbs");
                    if (!breadcrumbsEl) {
                        breadcrumbsEl = document.createElement("div");
                        breadcrumbsEl.className =
                            "task-breadcrumbs small text-muted mt-1";
                        alertElement.appendChild(breadcrumbsEl);
                    }
                    breadcrumbsEl.textContent = taskBreadcrumbs;
                }
            }

            // Clear search and hide results
            const taskSearch = document.getElementById("task-search");
            const searchResults = document.getElementById(
                "task-search-results",
            );
            if (taskSearch) {
                taskSearch.value = "";
            }
            if (searchResults) {
                searchResults.innerHTML = "";
            }

            // Trigger custom events to update UI components
            document.dispatchEvent(new CustomEvent('updateSaveButton'));
            document.dispatchEvent(new CustomEvent('updatePreview'));
            
            // Focus the duration input
            setTimeout(() => {
                const durationInput = document.getElementById(
                    "time-allocation-duration",
                );
                if (durationInput) {
                    durationInput.focus();
                    durationInput.select();
                }
            }, 50);
        }
    }

    /**
     * Update duration button states to highlight the active one
     */
    function updateDurationButtonStates() {
        const durationInput = document.getElementById("time-allocation-duration");
        const form = document.getElementById("time-allocation-form");
        
        if (!durationInput || !form) return;
        
        const currentDuration = parseInt(durationInput.value || 0);
        const remainingDuration = parseInt(form.dataset.remainingDuration || 0);
        
        // Reset all button states to default (gray outline) - only target buttons in the modal
        document.querySelectorAll("#time-allocation-modal button[data-duration]").forEach(btn => {
            btn.classList.remove("active", "btn-primary", "btn-secondary");
            btn.classList.add("btn-outline-secondary");
        });
        
        const maxButton = document.getElementById("duration-max");
        if (maxButton) {
            maxButton.classList.remove("active", "btn-primary", "btn-secondary");
            maxButton.classList.add("btn-outline-secondary");
        }
        
        // Highlight matching preset duration button(s) - only target buttons in the duration group
        const matchingButton = document.querySelector(`#time-allocation-modal button[data-duration="${currentDuration}"]`);
        if (matchingButton) {
            matchingButton.classList.remove("btn-outline-secondary");
            matchingButton.classList.add("active", "btn-primary");
        }
        
        // Highlight max button if current duration equals remaining time
        if (currentDuration === remainingDuration && remainingDuration > 0) {
            if (maxButton) {
                maxButton.classList.remove("btn-outline-secondary");
                maxButton.classList.add("active", "btn-primary");
            }
        }
    }

    /**
     * Clear selected task
     */
    function clearSelectedTask() {
        const taskIdInput = document.getElementById("selected-task-id");
        const taskNameDisplay = document.getElementById("selected-task-name");
        const selectedTaskContainer = document.getElementById(
            "selected-task-container",
        );
        const taskSearch = document.getElementById("task-search");

        if (taskIdInput) taskIdInput.value = "";
        if (taskNameDisplay) taskNameDisplay.textContent = "None";
        if (selectedTaskContainer)
            selectedTaskContainer.classList.add("d-none");
        if (taskSearch) {
            taskSearch.value = "";
            taskSearch.focus();
        }

        // Clear any breadcrumbs
        const breadcrumbs = document.querySelector(".task-breadcrumbs");
        if (breadcrumbs) {
            breadcrumbs.remove();
        }

        // Reset alert style
        const alertElement = document.querySelector(
            "#selected-task-container .alert",
        );
        if (alertElement) {
            alertElement.classList.remove("alert-success");
            alertElement.classList.add("alert-info");
        }
    }

    // Set up event listeners for cross-file communication
    document.addEventListener('updateDurationButtons', updateDurationButtonStates);

    /* Utility Functions */

    /**
     * Format a date as YYYY-MM-DD
     */
    function formatDate(date) {
        const year = date.getFullYear();
        const month = String(date.getMonth() + 1).padStart(2, "0");
        const day = String(date.getDate()).padStart(2, "0");
        return `${year}-${month}-${day}`;
    }

    /**
     * Format an ISO date string as YYYY-MM-DD
     */
    function formatDateFromISOString(isoString) {
        const date = new Date(isoString);
        return formatDate(date);
    }

    /**
     * Format an ISO date string as HH:MM
     */
    function formatTimeFromISOString(isoString) {
        const date = new Date(isoString);
        return `${String(date.getHours()).padStart(2, "0")}:${String(date.getMinutes()).padStart(2, "0")}`;
    }

    /**
     * Calculate duration in minutes between two ISO date strings
     */
    function calculateDurationInMinutes(startIsoString, endIsoString) {
        const start = new Date(startIsoString);
        const end = new Date(endIsoString);
        return Math.floor((end - start) / 60000);
    }

    // showAlert is now defined as a global function at the top of this file

    /**
     * Handle API response with enhanced error checking and logging
     */
    async function handleApiResponse(response, requestContext = {}) {
        if (!response.ok) {
            let responseData;
            let responseText;
            
            try {
                responseText = await response.text();
                responseData = JSON.parse(responseText);
            } catch (parseError) {
                responseData = { error: `Server returned ${response.status}: ${responseText || 'Unknown error'}` };
            }

            // Collect response headers for debugging
            const responseHeaders = {};
            response.headers.forEach((value, key) => {
                responseHeaders[key] = value;
            });

            // Prepare enhanced error context
            const errorContext = {
                ...requestContext,
                responseStatus: response.status,
                responseData: responseData,
                responseHeaders: responseHeaders,
                browserInfo: {
                    userAgent: navigator.userAgent,
                    language: navigator.language,
                    cookieEnabled: navigator.cookieEnabled
                }
            };

            const errorMessage = response.status === 401 
                ? "Please log in to your Timr account to view and manage working times"
                : (responseData.error || `Server error (${response.status})`);
            
            const apiError = new Error(errorMessage);
            
            // Log the error with detailed context
            logApiError(requestContext.operation || "API request", apiError, errorContext);
            
            throw apiError;
        }
        return response.json();
    }

    // debounce is now imported from modules/ui-utils.js

    // escapeHtml is now imported from modules/dom-utils.js

    /**
     * Load working time types from API
     */
    function loadWorkingTimeTypes() {
        return fetch("/api/working-time-types")
            .then(handleApiResponse)
            .then((data) => {
                state.attendanceTypes = data.attendance_types || [];
                state.otherTypes = data.other_types || [];
                state.allWorkingTimeTypes = [...state.attendanceTypes, ...state.otherTypes];
                return state.allWorkingTimeTypes;
            })
            .catch((error) => {
                console.error("Error loading working time types:", error);
                return [];
            });
    }

    /**
     * Populate working time types dropdown
     */
    function populateWorkingTimeTypes(selectElement) {
        if (!selectElement) return;

        // Clear existing options
        selectElement.innerHTML = '<option value="">Select working time type...</option>';

        if (state.attendanceTypes && state.attendanceTypes.length > 0) {
            // Add only attendance time types (already filtered by backend)
            state.attendanceTypes.forEach((type) => {
                const option = document.createElement('option');
                option.value = type.id;
                option.textContent = type.name || 'Unknown Type';
                selectElement.appendChild(option);
            });
        } else {
            selectElement.innerHTML = '<option value="">No attendance time types available</option>';
        }
    }

    /**
     * Setup keyboard navigation for working time modal
     */
    function setupWorkingTimeModalKeyboardNavigation() {
        const modal = document.getElementById('working-time-modal');
        if (!modal) return;

        modal.addEventListener('keydown', function(e) {
            // Tab navigation within modal
            if (e.key === 'Tab') {
                const focusableElements = modal.querySelectorAll(
                    'input:not([disabled]), select:not([disabled]), button:not([disabled]), [tabindex]:not([tabindex="-1"])'
                );
                const firstElement = focusableElements[0];
                const lastElement = focusableElements[focusableElements.length - 1];

                if (e.shiftKey) {
                    if (document.activeElement === firstElement) {
                        lastElement.focus();
                        e.preventDefault();
                    }
                } else {
                    if (document.activeElement === lastElement) {
                        firstElement.focus();
                        e.preventDefault();
                    }
                }
            }

            // Escape to close modal
            if (e.key === 'Escape') {
                const bsModal = bootstrap.Modal.getInstance(modal);
                if (bsModal) {
                    bsModal.hide();
                }
            }

            // Enter to submit form (if focus is on input, not button)
            if (e.key === 'Enter' && !e.target.matches('button')) {
                const form = modal.querySelector('#working-time-form');
                if (form) {
                    e.preventDefault();
                    form.dispatchEvent(new Event('submit'));
                }
            }
        });

        // Focus first input when modal opens
        modal.addEventListener('shown.bs.modal', function() {
            const firstInput = modal.querySelector('input:not([disabled])');
            if (firstInput) {
                firstInput.focus();
            }
        });
    }

    // Initialize keyboard navigation only (working time types will be loaded when needed)
    document.addEventListener('DOMContentLoaded', function() {
        setupWorkingTimeModalKeyboardNavigation();
    });
});

// Export functions for testing (only in Node.js environment)
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        getDateKey,
        saveExpandedState,
        getExpandedStates,
        formatDuration,
        parseTimeToMinutes
    };
}
