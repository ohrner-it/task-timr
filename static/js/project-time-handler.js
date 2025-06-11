/**
 * Handling of API responses for UI Project Times
 *
 * This module provides helper functions to interact with the UIProjectTime
 * API endpoints and render the results.
 */

// Import utility modules
import { parseJiraDuration, isReasonableDuration, JIRA_PARSE_DELAY_MS } from './modules/duration-parser.js';
import { formatDuration } from './modules/time-utils.js';
import { escapeHtml } from './modules/dom-utils.js';
import { logMessage, showAlert } from './modules/ui-utils.js';
import { fetchWithErrorHandling, handleFormSubmission, resetUIElements, handleUIError } from './modules/error-handler.js';
import { sortUIProjectTimesAlphabetically } from './modules/sorting-utils.js';

// Global state to store current allocations per working time
const workingTimeAllocations = new Map();

/**
 * Update stored allocations for a working time
 *
 * @param {string} workingTimeId - ID of the working time
 * @param {Object} data - UI project times data
 */
function updateStoredAllocations(workingTimeId, data) {
    if (data && data.ui_project_times) {
        workingTimeAllocations.set(workingTimeId, {
            allocations: data.ui_project_times,
            remainingDuration: data.remaining_duration || 0,
            isFullyAllocated: data.is_fully_allocated || false,
            isOverAllocated: data.is_over_allocated || false,
            lastUpdated: Date.now(),
        });
    }
}

/**
 * Get stored allocations for a working time
 *
 * @param {string} workingTimeId - ID of the working time
 * @returns {Object|null} - Stored allocation data or null if not available
 */
function getStoredAllocations(workingTimeId) {
    return workingTimeAllocations.get(workingTimeId) || null;
}

// parseJiraDuration and isReasonableDuration are now imported from modules/duration-parser.js

/**
 * Update save button state based on task selection and duration validity
 */
function updateSaveButtonState() {
    const form = document.getElementById("time-allocation-form");
    if (!form) return;

    const saveButton = form.querySelector('button[type="submit"]');
    const saveAndAddNewButton = document.getElementById("save-and-add-new-btn");
    if (!saveButton) return;

    const taskIdInput = document.getElementById("selected-task-id");
    const durationInput = document.getElementById("time-allocation-duration");

    const hasTaskSelected = taskIdInput && taskIdInput.value.trim() !== "";
    const hasDuration =
        durationInput &&
        !isNaN(parseInt(durationInput.value)) &&
        parseInt(durationInput.value) > 0;

    const isFormValid = hasTaskSelected && hasDuration;
    
    saveButton.disabled = !isFormValid;
    if (saveAndAddNewButton) {
        saveAndAddNewButton.disabled = !isFormValid;
    }
}

/**
 * Update the preview message when a task is selected
 */
function updateTimeAllocationPreview() {
    const form = document.getElementById("time-allocation-form");
    const modalAlerts = document.querySelector(
        "#time-allocation-modal .modal-alerts",
    );

    if (!form || !modalAlerts) return;

    const taskIdInput = document.getElementById("selected-task-id");
    const durationInput = document.getElementById("time-allocation-duration");
    const isEditing = !!form.dataset.taskId;

    // Don't show preview when editing existing allocation
    if (isEditing) return;

    const selectedTaskId = taskIdInput?.value?.trim();
    const newDuration = parseInt(durationInput?.value || 0);

    if (!selectedTaskId || !newDuration || newDuration <= 0) {
        // Clear any existing preview
        const existingPreview = modalAlerts.querySelector(
            ".allocation-preview",
        );
        if (existingPreview) {
            existingPreview.remove();
        }
        return;
    }

    // Get current allocations from form data or stored allocations
    let currentAllocations = [];
    try {
        if (form.dataset.currentAllocations) {
            currentAllocations = JSON.parse(form.dataset.currentAllocations);
        } else {
            // Fallback to stored allocations if form data not available
            const workingTimeId = form.dataset.workingTimeId;
            const storedData = getStoredAllocations(workingTimeId);
            currentAllocations = storedData ? storedData.allocations : [];
        }
    } catch (e) {
        console.warn("Could not parse current allocations", e);
        return;
    }

    // Find existing allocation for this task
    const existingAllocation = currentAllocations.find(
        (allocation) => allocation.task_id === selectedTaskId,
    );

    // Remove any existing preview
    const existingPreview = modalAlerts.querySelector(".allocation-preview");
    if (existingPreview) {
        existingPreview.remove();
    }

    if (existingAllocation) {
        // Show preview for adding to existing allocation
        const existingDuration = existingAllocation.duration_minutes;
        const totalDuration = existingDuration + newDuration;
        const taskName = existingAllocation.task_name;

        const previewAlert = document.createElement("div");
        previewAlert.className = "alert alert-info allocation-preview";
        previewAlert.innerHTML = `
            <i class="bi bi-info-circle me-2"></i>
            Task '<strong>${escapeHtml(taskName)}</strong>' already has <strong>${formatDuration(existingDuration)}</strong> allocated. 
            Adding <strong>${formatDuration(newDuration)}</strong> more will result in a total of <strong>${formatDuration(totalDuration)}</strong>.
        `;

        modalAlerts.appendChild(previewAlert);
    }
}

/**
 * Setup event listeners for the time allocation form
 */
function setupTimeAllocationFormListeners() {
    // Update save button state when task selection changes
    const taskIdInput = document.getElementById("selected-task-id");
    if (taskIdInput) {
        const observer = new MutationObserver(() => {
            updateSaveButtonState();
            updateTimeAllocationPreview();
        });
        observer.observe(taskIdInput, {
            attributes: true,
            attributeFilter: ["value"],
        });
    }

    // Handle Jira-style duration input with improved parsing
    const durationInput = document.getElementById("time-allocation-duration");
    if (durationInput) {
        let parseTimeout;

        // Watch for ANY value changes to the duration input (typing, programmatic, etc.)
        let lastValue = durationInput.value;
        
        function checkForValueChange() {
            if (durationInput.value !== lastValue) {
                lastValue = durationInput.value;
                updateSaveButtonState();
                updateTimeAllocationPreview();
                document.dispatchEvent(new CustomEvent('updateDurationButtons'));
            }
        }
        
        // Use multiple approaches to catch all possible value changes
        durationInput.addEventListener('input', checkForValueChange);
        durationInput.addEventListener('change', checkForValueChange);
        durationInput.addEventListener('propertychange', checkForValueChange); // For older browsers
        
        // Also use MutationObserver for attribute changes
        const durationObserver = new MutationObserver(checkForValueChange);
        durationObserver.observe(durationInput, {
            attributes: true,
            attributeFilter: ['value']
        });
        
        // Periodically check for changes (as a last resort)
        setInterval(checkForValueChange, 100);

        // The comprehensive value change detection above handles all updates
        // This listener now only handles input-specific logic (clearing timeouts)
        durationInput.addEventListener("input", function (e) {
            // Clear previous timeout for parsing
            if (parseTimeout) {
                clearTimeout(parseTimeout);
            }
        });

        // Also handle blur event for immediate parsing when user leaves the field
        durationInput.addEventListener("blur", function (e) {
            const currentValue = e.target.value.trim();

            // Clear any pending timeout
            if (parseTimeout) {
                clearTimeout(parseTimeout);
                parseTimeout = null;
            }

            // Parse if it contains letters
            if (/[a-zA-Z]/.test(currentValue)) {
                const minutes = parseJiraDuration(currentValue);
                if (!isNaN(minutes)) {
                    e.target.value = minutes;
                    // Clear any previous error styling
                    e.target.classList.remove("is-invalid");
                    updateSaveButtonState();
                    updateTimeAllocationPreview();
                    // Also trigger duration button update after parsing
                    document.dispatchEvent(new CustomEvent('updateDurationButtons'));
                } else {
                    // Show error for invalid format
                    e.target.classList.add("is-invalid");
                    const modalAlerts = document.querySelector("#time-allocation-modal .modal-alerts");
                    if (modalAlerts) {
                        modalAlerts.innerHTML = `
                            <div class="alert alert-warning">
                                <i class="bi bi-exclamation-triangle me-2"></i>
                                Invalid time format: "${currentValue}". Please use formats like "2h 30m", "90m", or "1.5h".
                            </div>
                        `;
                    }
                }
            } else {
                // Clear error styling for pure numeric input
                e.target.classList.remove("is-invalid");
            }
        });
    }

    // Handle "Save and Add New" button
    const saveAndAddNewBtn = document.getElementById("save-and-add-new-btn");
    if (saveAndAddNewBtn) {
        saveAndAddNewBtn.addEventListener("click", function () {
            // Trigger form submission but mark it as "save and add new"
            const form = document.getElementById("time-allocation-form");
            if (form) {
                form.dataset.saveAndAddNew = "true";
                form.dispatchEvent(new Event("submit"));
            }
        });
    }

    // Set up event listeners for cross-file communication
    document.addEventListener('updateSaveButton', updateSaveButtonState);
    document.addEventListener('updatePreview', updateTimeAllocationPreview);
    
    // Initial button state and preview update
    updateSaveButtonState();
    updateTimeAllocationPreview();
}

/**
 * Fetch UI project times for a working time
 *
 * @param {string} workingTimeId - ID of the working time
 * @returns {Promise<Object>} - UI project times data
 */
async function fetchUIProjectTimes(workingTimeId) {
    try {
        logMessage(
            `Fetching UI project times for working time ID: ${workingTimeId}`,
            "info",
        );
        const response = await fetch(
            `/api/working-times/${workingTimeId}/ui-project-times`,
        );

        if (!response.ok) {
            const data = await response.json();
            const errorMsg = data.error || "Failed to load UI project times";
            logMessage(`API Error (${response.status}): ${errorMsg}`, "error", {
                workingTimeId,
                response,
            });
            throw new Error(errorMsg);
        }

        const responseData = await response.json();
        logMessage("UI project times fetched successfully", "info", {
            count: responseData?.ui_project_times?.length || 0,
        });
        return responseData;
    } catch (error) {
        logMessage(
            `Failed to load time allocations: ${error.message}`,
            "error",
            { error, workingTimeId },
        );
        showAlert(
            `Failed to load time allocations: ${error.message}`,
            "danger",
        );
        return null;
    }
}

/**
 * Handle response from UI project time API and update UI
 *
 * @param {Object} data - Response data
 * @param {string} workingTimeId - ID of the working time
 * @returns {boolean} - Whether the update was successful
 */
function handleUIProjectTimeResponse(data, workingTimeId) {
    // Update stored allocations first
    updateStoredAllocations(workingTimeId, data);

    // Update UI with response data
    if (data && data.ui_project_times) {
        // Update UI project times display
        renderUIProjectTimes(data, { id: workingTimeId });

        // Update time allocation progress if available
        if (
            data.total_duration !== undefined &&
            data.remaining_duration !== undefined
        ) {
            renderTimeAllocationProgress(data, workingTimeId);
        }

        return true;
    }
    return false;
}

/**
 * Save a time allocation
 *
 * @returns {Promise<Object>} - Response data
 */
async function saveTimeAllocation(event) {
    // Prevent default form submission to keep modal open
    if (event) {
        event.preventDefault();
        event.stopPropagation();
    }
    
    const form = document.getElementById("time-allocation-form");
    if (!form) return;

    // Store current date in localStorage before making any changes
    const dateInput = document.getElementById("date-input");
    if (dateInput && dateInput.value) {
        localStorage.setItem("currentViewDate", dateInput.value);
        console.log(`Stored current date in localStorage: ${dateInput.value}`);
    }

    const taskId = form.dataset.taskId; // For editing existing UI time allocation
    const workingTimeId = form.dataset.workingTimeId;
    const taskIdInput = document.getElementById("selected-task-id");
    const durationInput = document.getElementById("time-allocation-duration");

    // Validate form elements exist
    if (!taskIdInput || !durationInput) {
        showAlert(
            "Form fields not found. Please reload the page and try again.",
            "danger",
            true,
        );
        return;
    }

    const selectedTaskId = taskIdInput.value.trim();
    const duration = parseInt(durationInput.value);

    // Validate task selection
    if (!selectedTaskId) {
        showAlert("Please select a task before saving", "warning", true);
        document.getElementById("task-search")?.focus();
        return;
    }

    // Validate duration input
    if (isNaN(duration) || duration <= 0) {
        showAlert(
            "Please enter a valid duration (greater than 0 minutes)",
            "warning",
            true,
        );
        return;
    }

    // Get task name from the display element
    const taskNameElement = document.querySelector("#selected-task-name");
    const taskName = taskNameElement
        ? taskNameElement.textContent
        : "Unknown Task";

    // Get task breadcrumbs if available
    const breadcrumbsElement = document.querySelector(".task-breadcrumbs");
    const taskBreadcrumbs = breadcrumbsElement
        ? breadcrumbsElement.textContent
        : "";

    // Show loading indicator for both save buttons
    let submitBtn = document.querySelector(
        `button[type="submit"][form="${form.id}"]`,
    );
    if (!submitBtn) {
        submitBtn = form.querySelector('button[type="submit"]');
    }
    
    const saveAndAddNewBtn = document.getElementById("save-and-add-new-btn");
    const isSaveAndAddNew = form.dataset.saveAndAddNew === "true";

    // Disable both buttons
    if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.classList.add("btn-processing");
    }
    if (saveAndAddNewBtn) {
        saveAndAddNewBtn.disabled = true;
        saveAndAddNewBtn.classList.add("btn-processing");
    }

    // Show spinner on the clicked button
    if (isSaveAndAddNew && saveAndAddNewBtn) {
        saveAndAddNewBtn.innerHTML =
            '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Saving...';
    } else if (submitBtn) {
        submitBtn.innerHTML =
            '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Saving...';
    }

    const submitOperation = async () => {
        let requestData;
        let requestUrl;
        let requestMethod;

        if (taskId) {
            // For editing an existing UI time allocation, use PATCH
            requestData = {
                duration_minutes: duration,
                task_name: taskName,
            };
            requestUrl = `/api/working-times/${workingTimeId}/ui-project-times/${taskId}`;
            requestMethod = "PATCH";
        } else {
            // For new UI time allocations, use POST
            requestData = {
                task_id: selectedTaskId,
                task_name: taskName,
                task_breadcrumbs: taskBreadcrumbs,
                duration_minutes: duration,
            };
            requestUrl = `/api/working-times/${workingTimeId}/ui-project-times`;
            requestMethod = "POST";
        }

        // Log request details for debugging Firefox issues
        console.log(`Making ${requestMethod} request to: ${requestUrl}`);
        console.log('Request data:', JSON.stringify(requestData));
        console.log('Working time ID:', workingTimeId);
        
        const response = await fetch(requestUrl, {
            method: requestMethod,
            headers: {
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            body: JSON.stringify(requestData),
        });

        if (!response.ok) {
            const errorText = await response.text();
            let errorData;
            try {
                errorData = JSON.parse(errorText);
            } catch (e) {
                errorData = { error: `Server error (${response.status})` };
            }
            throw new Error(errorData.error || `HTTP ${response.status}: Failed to save time allocation`);
        }

        const data = await response.json();

        return data;
    };

    try {
        const data = await submitOperation();

        // Success - execute success logic
        // Check if this is a "Save and Add New" operation
        const saveAndAddNew = form.dataset.saveAndAddNew === "true";
        
        // Close modal only if not "Save and Add New"
        const modal = bootstrap.Modal.getInstance(
            document.getElementById("time-allocation-modal"),
        );
        if (modal && !saveAndAddNew) {
            modal.hide();
        }

        // Show success message with details if adding to existing allocation
        let successMessage = "Time allocation saved successfully";

        // Check if we were adding to an existing allocation (only for new allocations, not edits)
        if (!taskId) {
            try {
                const currentAllocations = JSON.parse(
                    form.dataset.currentAllocations || "[]",
                );
                const existingAllocation = currentAllocations.find(
                    (allocation) => allocation.task_id === selectedTaskId,
                );

                if (existingAllocation) {
                    const existingDuration =
                        existingAllocation.duration_minutes;
                    const totalDuration = existingDuration + duration;
                    successMessage = `Added ${formatDuration(duration)} to '${taskName}'. Total time allocated: ${formatDuration(totalDuration)}.`;
                }
            } catch (e) {
                // Fall back to generic message if we can't parse allocations
                console.warn("Could not parse allocations for success message");
            }
        }

        showAlert(successMessage, "success");

        // Update the UI without losing context
        handleUIProjectTimeResponse(data, workingTimeId);

        // Make sure the working time details section remains open
        const workingTimeItem = document.querySelector(
            `.working-time-item[data-id="${workingTimeId}"]`,
        );
        if (workingTimeItem) {
            const detailsSection = workingTimeItem.querySelector(
                ".working-time-details",
            );
            if (detailsSection) {
                detailsSection.classList.remove("d-none");
            }
        }

        // If this is "Save and Add New", reset the form for another entry
        if (saveAndAddNew) {
            // Clear the saveAndAddNew flag
            delete form.dataset.saveAndAddNew;
            
            // Reset form for a new entry, but keep the working time ID
            form.reset();
            delete form.dataset.taskId;
            
            // Reset task selection UI
            const taskIdInput = document.getElementById("selected-task-id");
            const taskNameDisplay = document.getElementById("selected-task-name");
            const selectedTaskContainer = document.getElementById("selected-task-container");
            
            if (taskIdInput) taskIdInput.value = "";
            if (taskNameDisplay) taskNameDisplay.textContent = "";
            if (selectedTaskContainer) selectedTaskContainer.classList.add("d-none");
            
            // Set default duration (considering updated remaining time)
            const durationInput = document.getElementById("time-allocation-duration");
            if (durationInput) {
                // Use the updated remaining time from the response if available
                const remainingMinutes = data.remaining_duration || 60;
                const defaultDuration = Math.min(60, remainingMinutes);
                durationInput.value = defaultDuration > 0 ? defaultDuration : 60;
            }
            
            // Update stored allocations with the new data
            workingTimeAllocations.set(workingTimeId, {
                allocations: data.ui_project_times || [],
                remainingDuration: data.remaining_duration || 0,
                isFullyAllocated: data.is_fully_allocated || false,
                workingDuration: data.working_duration || 0
            });
            
            // Update the form's current allocations dataset for the preview system
            form.dataset.currentAllocations = JSON.stringify(data.ui_project_times || []);
            
            // Update the form's remaining duration for the duration button highlighting
            form.dataset.remainingDuration = data.remaining_duration || 0;
            
            // Clear any existing alerts and show a helpful message
            const modalAlerts = document.querySelector("#time-allocation-modal .modal-alerts");
            if (modalAlerts) {
                const remainingMinutes = data.remaining_duration || 0;
                if (remainingMinutes > 0) {
                    modalAlerts.innerHTML = `
                        <div class="alert alert-success">
                            <i class="bi bi-check-circle me-2"></i>
                            Time allocation saved! You have <strong>${formatDuration(remainingMinutes)}</strong> remaining to allocate.
                        </div>
                    `;
                } else {
                    modalAlerts.innerHTML = `
                        <div class="alert alert-warning">
                            <i class="bi bi-exclamation-triangle me-2"></i>
                            Time allocation saved! This working time is now fully allocated.
                        </div>
                    `;
                }
            }
            
            // Update button states and preview
            updateSaveButtonState();
            updateTimeAllocationPreview();
            
            // Trigger custom event to update duration button highlighting
            setTimeout(() => {
                document.dispatchEvent(new CustomEvent('updateDurationButtons'));
            }, 50);
            
            // Focus on task search for quick entry
            const taskSearchInput = document.getElementById("task-search");
            if (taskSearchInput) {
                setTimeout(() => taskSearchInput.focus(), 100);
            }
        }

        return data;
    } catch (error) {
        // Show error in modal and keep it open
        const modalAlerts = document.querySelector("#time-allocation-modal .modal-alerts");
        if (modalAlerts) {
            modalAlerts.innerHTML = `
                <div class="alert alert-danger">
                    <i class="bi bi-exclamation-triangle me-2"></i>
                    ${error.message}
                </div>
            `;
        }
        
        // Log detailed error information
        console.error(`API Error: save time allocation | Message: ${error.message} | Request: POST /api/working-times/${workingTimeId}/ui-project-times | Request data: ${JSON.stringify({task_id: selectedTaskId, task_name: taskName, duration_minutes: duration})} | Browser: ${navigator.userAgent.split(' ')[0]} | Timestamp: ${new Date().toISOString()}`);
        
        return null;
    } finally {
        // Reset UI elements regardless of success or failure
        resetUIElements({
            submitBtn: submitBtn,
            saveAndAddNewBtn: document.getElementById("save-and-add-new-btn")
        }, {
            submitBtn: {
                disabled: false,
                innerHTML: "Save",
                classList: { remove: ["btn-processing"] }
            },
            saveAndAddNewBtn: {
                disabled: false,
                innerHTML: "Save and Add New",
                classList: { remove: ["btn-processing"] }
            }
        });

        // Clear the saveAndAddNew flag if it exists
        if (form && form.dataset.saveAndAddNew) {
            delete form.dataset.saveAndAddNew;
        }
    }
}

/**
 * Delete a time allocation
 *
 * @param {string} taskId - ID of the task
 * @param {string} workingTimeId - ID of the working time
 * @returns {Promise<Object>} - Response data
 */
async function deleteTimeAllocation(taskId, workingTimeId) {
    if (!confirm("Are you sure you want to delete this time allocation?")) {
        return;
    }

    // Show loading indicator
    const timeAllocationItem = document.querySelector(
        `.ui-project-time-item[data-task-id="${taskId}"]`,
    );
    if (timeAllocationItem) {
        timeAllocationItem.style.opacity = "0.5";
    }

    try {
        const requestUrl = `/api/working-times/${workingTimeId}/ui-project-times/${taskId}`;
        
        // Use the enhanced fetch wrapper with automatic error handling
        const data = await fetchWithErrorHandling(requestUrl, {
            method: "DELETE",
        }, {
            operation: "delete time allocation",
            workingTimeId: workingTimeId,
            taskId: taskId
        });

        // Show success message
        showAlert("Time allocation deleted successfully", "success");

        // Update the UI
        handleUIProjectTimeResponse(data, workingTimeId);

        return data;
    } catch (error) {
        // Use the centralized error handler
        handleUIError(error, {
            operation: "delete time allocation",
            modalContext: false,
            fallbackAction: () => {
                // Reset opacity on error
                if (timeAllocationItem) {
                    timeAllocationItem.style.opacity = "1";
                }
            }
        });
    }
}

/**
 * Render UI project times for a working time
 *
 * @param {Object} data - UI project times data
 * @param {Object} workingTime - Working time object
 * @returns {boolean} - Whether the rendering was successful
 */
function renderUIProjectTimes(data, workingTime) {
    const workingTimeId = workingTime.id;
    const container = document.getElementById(`project-times-${workingTimeId}`);

    if (!container) {
        console.error(
            `Container for project times of working time ${workingTimeId} not found`,
        );
        return false;
    }

    // Store the data for later use
    updateStoredAllocations(workingTimeId, data);

    // Ensure we have the right data structure
    if (!data || !Array.isArray(data.ui_project_times)) {
        console.error("Invalid UI project times data structure", data);
        container.innerHTML =
            '<div class="text-muted">No time allocations available</div>';
        return false;
    }

    const uiProjectTimes = data.ui_project_times;

    // If no project times, show empty state
    if (uiProjectTimes.length === 0) {
        // Check if this working time is fully allocated (e.g., 0-duration placeholder entries)
        const isFullyAllocated = data.is_fully_allocated || false;

        container.innerHTML = `
            <div class="alert alert-light text-center">
                <p>No time allocations yet. <i class="bi bi-clock-history"></i></p>
                ${createTimeActionButton(isFullyAllocated, "sm btn-primary", "add-time-allocation", "Add Time", "bi-plus-circle me-1")}
            </div>
        `;

        // Add event listener to the add button (only if not fully allocated)
        if (!isFullyAllocated) {
            container
                .querySelector(".add-time-allocation")
                ?.addEventListener("click", function () {
                    openTimeAllocationModal(workingTimeId);
                });
        }

        return true;
    }

    // Create a table to display UI project times
    let tableHtml = `
        <table class="table table-hover table-sm project-times-table">
            <thead>
                <tr>
                    <th>Task</th>
                    <th style="width: 120px;">Duration</th>
                    <th style="width: 150px;">Actions</th>
                </tr>
            </thead>
            <tbody>
    `;

    // Sort UI project times by task name
    const sortedTimes = sortUIProjectTimesAlphabetically(uiProjectTimes);

    // Add rows for each UI project time
    sortedTimes.forEach((uiPt) => {
        const durationFormatted = formatDuration(uiPt.duration_minutes);

        tableHtml += `
            <tr class="ui-project-time-item" 
                data-task-id="${uiPt.task_id}" 
                data-task-name="${escapeHtml(uiPt.task_name || "")}" 
                data-task-breadcrumbs="${escapeHtml(uiPt.task_breadcrumbs || "")}" 
                data-duration="${uiPt.duration_minutes}">
                <td>
                    <div class="fw-semibold task-name">${escapeHtml(uiPt.task_name || "Unknown Task")}</div>
                    <div class="task-breadcrumbs small text-muted">${escapeHtml(uiPt.task_breadcrumbs || "")}</div>
                </td>
                <td class="text-center align-middle">
                    <span class="badge bg-secondary">${durationFormatted}</span>
                </td>
                <td>
                    <div class="btn-group btn-group-sm" role="group">
                        <button type="button" class="btn btn-outline-primary edit-time-allocation" 
                            title="Edit time allocation" aria-label="Edit time allocation">
                            <i class="bi bi-pencil"></i>
                        </button>
                        <button type="button" class="btn btn-outline-danger delete-time-allocation" 
                            title="Delete time allocation" aria-label="Delete time allocation">
                            <i class="bi bi-trash"></i>
                        </button>
                    </div>
                </td>
            </tr>
        `;
    });

    tableHtml += `
            </tbody>
        </table>
    `;

    container.innerHTML = tableHtml;

    // Add event listeners to edit and delete buttons
    container.querySelectorAll(".edit-time-allocation").forEach((btn) => {
        btn.addEventListener("click", function () {
            const item = this.closest(".ui-project-time-item");
            editTimeAllocation(item.dataset.taskId, workingTimeId, item);
        });
    });

    container.querySelectorAll(".delete-time-allocation").forEach((btn) => {
        btn.addEventListener("click", function () {
            const item = this.closest(".ui-project-time-item");
            deleteTimeAllocation(item.dataset.taskId, workingTimeId);
        });
    });

    return true;
}

/**
 * Creates a button with tooltip if needed based on allocation status
 *
 * @param {boolean} isFullyAllocated - Whether the working time is fully allocated
 * @param {string} buttonClasses - CSS classes for the button (e.g., 'primary', 'sm btn-primary')
 * @param {string} buttonClass - Functional class name for the button (add-time-allocation, distribute-time)
 * @param {string} buttonLabel - Label for the button
 * @param {string} iconClass - Bootstrap icon class
 * @return {string} - HTML for the button
 */
function createTimeActionButton(
    isFullyAllocated,
    buttonClasses,
    buttonClass,
    buttonLabel,
    iconClass,
) {
    if (isFullyAllocated) {
        return `<button type="button" class="btn btn-${buttonClasses} ${buttonClass}" disabled data-bs-toggle="tooltip" data-bs-placement="top" title="This working time is already fully allocated">
                <i class="bi ${iconClass}"></i> ${buttonLabel}
            </button>`;
    } else {
        return `<button type="button" class="btn btn-${buttonClasses} ${buttonClass}">
            <i class="bi ${iconClass}"></i> ${buttonLabel}
         </button>`;
    }
}

/**
 * Attach event handlers to time allocation buttons
 *
 * @param {string} workingTimeId - ID of the working time
 * @param {HTMLElement} container - Container element with the buttons
 * @param {boolean} isFullyAllocated - Whether the working time is fully allocated
 */
function attachTimeActionHandlers(workingTimeId, container, isFullyAllocated) {
    if (isFullyAllocated) return; // Skip if fully allocated

    // Add event listeners to buttons within this specific container
    const addTimeBtn = container.querySelector(".add-time-allocation");
    if (addTimeBtn) {
        addTimeBtn.addEventListener("click", function () {
            openTimeAllocationModal(workingTimeId);
        });
    }

    const distributeTimeBtn = container.querySelector(".distribute-time");
    if (distributeTimeBtn) {
        distributeTimeBtn.addEventListener("click", function () {
            openDistributeTimeModal(workingTimeId);
        });
    }
}

/**
 * Render the time allocation progress bar
 *
 * @param {Object} data - UI project times data
 * @param {string} workingTimeId - ID of the working time
 */
function renderTimeAllocationProgress(data, workingTimeId) {
    const container = document.getElementById(
        `time-allocation-${workingTimeId}`,
    );
    if (!container) return;

    const totalDuration = data.total_duration || 0;
    const netDuration = data.net_duration || 0;
    const remainingDuration = data.remaining_duration || 0;
    const isFullyAllocated = data.is_fully_allocated || false;
    const isOverAllocated = data.is_over_allocated || false;

    // Format durations for display
    const totalFormatted = formatDuration(totalDuration);
    const remainingFormatted = formatDuration(Math.abs(remainingDuration));

    // Calculate percentage for progress bar (can exceed 100% for over-allocation)
    const percentAllocated =
        netDuration > 0 ? (totalDuration / netDuration) * 100 : 0;

    // Determine status class and badge text based on allocation status
    let statusClass, statusBadgeClass, statusText;
    
    if (isOverAllocated) {
        statusClass = "bg-danger";
        statusBadgeClass = "bg-danger";
        statusText = "Over-allocated";
    } else if (isFullyAllocated) {
        statusClass = "bg-success";
        statusBadgeClass = "bg-success";
        statusText = "Fully allocated";
    } else {
        statusClass = "bg-warning";
        statusBadgeClass = "bg-warning";
        statusText = `${remainingFormatted} remaining`;
    }

    // Create "Add Remaining Time" button for the progress bar (only if not over-allocated)
    const distributeTimeButton = (isFullyAllocated || isOverAllocated)
        ? ""
        : `<div class="text-center mt-2">
            ${createTimeActionButton(false, "warning", "distribute-time", `Allocate Remaining ${remainingFormatted}`, "bi-lightning-fill me-1")}
         </div>`;

    let html = `
        <div class="card border-light mb-3">
            <div class="card-body py-2">
                <div class="d-flex justify-content-between align-items-center mb-1">
                    <div class="fw-bold">Time Allocation</div>
                    <div>
                        <span class="badge bg-secondary">${totalFormatted} allocated</span>
                        ${
                            isOverAllocated
                                ? `<span class="badge ${statusBadgeClass} ms-1">${remainingFormatted} over</span>`
                                : `<span class="badge ${statusBadgeClass} ms-1">${statusText}</span>`
                        }
                    </div>
                </div>
                <div class="progress" style="height: 20px;">
                    ${isOverAllocated ? `
                        <div class="progress-bar bg-danger timr-progress-text" 
                            role="progressbar" 
                            style="width: 100%"
                            aria-valuenow="${totalDuration}" 
                            aria-valuemin="0" 
                            aria-valuemax="${netDuration}">
                            ${Math.round(percentAllocated)}%
                        </div>
                    ` : `
                        <div class="progress-bar ${statusClass} timr-progress-text" 
                            role="progressbar" 
                            style="width: ${percentAllocated}%"
                            aria-valuenow="${totalDuration}" 
                            aria-valuemin="0" 
                            aria-valuemax="${netDuration}">
                            ${percentAllocated > 30 ? `${Math.round(percentAllocated)}%` : ""}
                        </div>
                    `}
                </div>
                ${distributeTimeButton}
            </div>
        </div>
    `;

    container.innerHTML = html;

    // Attach event handlers to the progress bar distribute button
    attachTimeActionHandlers(workingTimeId, container, isFullyAllocated || isOverAllocated);

    // Find and update the action buttons section in the card header
    const workingTimeItem = document.querySelector(
        `.working-time-item[data-id="${workingTimeId}"]`,
    );
    if (workingTimeItem) {
        const actionsContainer = workingTimeItem.querySelector(
            '.btn-group[aria-label="Time allocation actions"]',
        );

        if (actionsContainer) {
            // Replace the buttons with our new HTML that includes tooltip wrappers if needed
            const isTimeAllocationDisabled = isFullyAllocated || isOverAllocated;
            actionsContainer.innerHTML = `
                ${createTimeActionButton(isTimeAllocationDisabled, "primary", "add-time-allocation", "Add Time", "bi-plus-circle me-1")}
                ${createTimeActionButton(isTimeAllocationDisabled, "outline-warning", "distribute-time", "Add Remaining Time", "bi-lightning-fill me-1")}
            `;

            // Attach event handlers to the action buttons
            attachTimeActionHandlers(
                workingTimeId,
                actionsContainer,
                isTimeAllocationDisabled,
            );
        }
    }

    // Initialize tooltips
    const tooltips = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    tooltips.forEach((tooltipEl) => {
        new bootstrap.Tooltip(tooltipEl);
    });
}

/**
 * Open time allocation modal for adding a new time allocation
 * This function handles both regular "Add Time" and "Add Remaining Time" operations
 *
 * @param {string} workingTimeId - ID of the working time
 * @param {boolean} useRemainingTime - Whether to use remaining time as the default duration
 */
function openTimeAllocationModal(workingTimeId, useRemainingTime = false) {
    // Try to get current data from stored allocations first (fastest)
    const storedData = getStoredAllocations(workingTimeId);

    if (storedData) {
        // We have the data already stored, use it directly
        const remainingMinutes = storedData.remainingDuration;
        const isFullyAllocated = storedData.isFullyAllocated;
        const isOverAllocated = storedData.isOverAllocated;

        if (isOverAllocated) {
            showAlert(
                "This working time is over-allocated. Cannot add new time allocations.",
                "warning",
            );
            return;
        }

        if (isFullyAllocated) {
            showAlert(
                "This working time is already fully allocated. Cannot add new time allocations.",
                "info",
            );
            return;
        }

        // Open the form with stored data
        if (useRemainingTime) {
            openTimeAllocationForm(workingTimeId, null, remainingMinutes, true);
        } else {
            const defaultDuration = Math.min(60, remainingMinutes);
            openTimeAllocationForm(workingTimeId, null, defaultDuration, false);
        }
        return;
    }

    // Fallback: fetch data if not available in memory (e.g., page just loaded)
    fetchUIProjectTimes(workingTimeId)
        .then((data) => {
            const remainingMinutes = data?.remaining_duration || 0;
            const isFullyAllocated = data?.is_fully_allocated || false;
            const isOverAllocated = data?.is_over_allocated || false;

            if (isOverAllocated) {
                showAlert(
                    "This working time is over-allocated. Cannot add new time allocations.",
                    "warning",
                );
                return;
            }

            if (isFullyAllocated) {
                showAlert(
                    "This working time is already fully allocated. Cannot add new time allocations.",
                    "info",
                );
                return;
            }

            // Data will be stored by fetchUIProjectTimes -> handleUIProjectTimeResponse
            // Open the form
            if (useRemainingTime) {
                openTimeAllocationForm(
                    workingTimeId,
                    null,
                    remainingMinutes,
                    true,
                );
            } else {
                const defaultDuration = Math.min(60, remainingMinutes);
                openTimeAllocationForm(
                    workingTimeId,
                    null,
                    defaultDuration,
                    false,
                );
            }
        })
        .catch((error) => {
            showAlert(
                `Error checking remaining time: ${error.message}`,
                "danger",
            );
        });
}

/**
 * Open time allocation form for editing or creating
 *
 * @param {string} workingTimeId - ID of the working time
 * @param {string} taskId - ID of the task (for editing)
 * @param {number} defaultDuration - Default duration in minutes
 * @param {boolean} isDistributeRemaining - Whether this is for distributing remaining time
 */
function openTimeAllocationForm(
    workingTimeId,
    taskId = null,
    defaultDuration = 60,
    isDistributeRemaining = false,
) {
    // Get form and reset it
    const form = document.getElementById("time-allocation-form");
    if (!form) return;

    form.reset();
    form.dataset.workingTimeId = workingTimeId;

    // If taskId is provided, this is an edit operation
    if (taskId) {
        form.dataset.taskId = taskId;
    } else {
        delete form.dataset.taskId;
    }

    // Reset task selection
    const taskIdInput = document.getElementById("selected-task-id");
    const taskNameDisplay = document.getElementById("selected-task-name");
    const selectedTaskContainer = document.getElementById(
        "selected-task-container",
    );

    if (taskIdInput) taskIdInput.value = "";
    if (taskNameDisplay) taskNameDisplay.textContent = "";
    if (selectedTaskContainer) selectedTaskContainer.classList.add("d-none");

    // Set default duration
    const durationInput = document.getElementById("time-allocation-duration");
    if (durationInput) {
        durationInput.value = defaultDuration;
    }

    // Get current allocations from stored data
    const storedData = getStoredAllocations(workingTimeId);
    const currentAllocations = storedData ? storedData.allocations : [];
    const remainingDuration = storedData ? storedData.remainingDuration : 0;

    // Store current allocations and remaining time in the form for later reference
    form.dataset.currentAllocations = JSON.stringify(currentAllocations);
    form.dataset.remainingDuration = remainingDuration;

    // If editing, populate the form with existing data
    if (taskId) {
        const item = document.querySelector(
            `.ui-project-time-item[data-task-id="${taskId}"]`,
        );
        if (item) {
            if (taskIdInput) taskIdInput.value = taskId;
            if (taskNameDisplay)
                taskNameDisplay.textContent = item.dataset.taskName || "";
            if (selectedTaskContainer)
                selectedTaskContainer.classList.remove("d-none");

            // Add breadcrumbs if available
            const breadcrumbs = item.dataset.taskBreadcrumbs;
            if (breadcrumbs && selectedTaskContainer) {
                // Check if breadcrumbs element already exists
                let breadcrumbsEl =
                    selectedTaskContainer.querySelector(".task-breadcrumbs");
                if (!breadcrumbsEl) {
                    breadcrumbsEl = document.createElement("div");
                    breadcrumbsEl.className =
                        "task-breadcrumbs small text-muted mt-1";
                    selectedTaskContainer.appendChild(breadcrumbsEl);
                }
                breadcrumbsEl.textContent = breadcrumbs;
            }

            // Set duration
            if (durationInput && item.dataset.duration) {
                durationInput.value = item.dataset.duration;
            }

            // Update alert style
            const alertElement = selectedTaskContainer.querySelector(".alert");
            if (alertElement) {
                alertElement.classList.remove("alert-info");
                alertElement.classList.add("alert-success");
            }
        }
    }

    // Update modal title and add info for remaining time if needed
    const modalTitle = document.getElementById("time-allocation-modal-label");
    const modalAlerts = document.querySelector(
        "#time-allocation-modal .modal-alerts",
    );

    if (modalTitle) {
        modalTitle.textContent = taskId
            ? "Edit Time Allocation"
            : isDistributeRemaining
              ? "Distribute Remaining Time"
              : "Add Time Allocation";
    }

    // Clear any existing alerts
    if (modalAlerts) {
        modalAlerts.innerHTML = "";

        // Add a message about remaining time if distributing
        if (isDistributeRemaining && defaultDuration > 0) {
            modalAlerts.innerHTML = `
                <div class="alert alert-info">
                    <i class="bi bi-info-circle me-2"></i>
                    There are <strong>${formatDuration(defaultDuration)}</strong> of unallocated time. 
                    Please select a task to allocate this time to.
                </div>
            `;
        }


    }

    // Show modal
    const modal = new bootstrap.Modal(
        document.getElementById("time-allocation-modal"),
    );
    if (modal) {
        modal.show();

        // Setup event listeners for the form elements
        setupTimeAllocationFormListeners();
        
        // Update duration button states to highlight the correct initial button
        // Use a small delay to ensure the modal is fully rendered
        setTimeout(() => {
            document.dispatchEvent(new CustomEvent('updateDurationButtons'));
        }, 200);
    }
}

/**
 * Edit time allocation
 *
 * @param {string} taskId - ID of the task
 * @param {string} workingTimeId - ID of the working time
 * @param {Element} element - UI element containing task data
 */
function editTimeAllocation(taskId, workingTimeId, element) {
    const duration = element ? parseInt(element.dataset.duration) : 0;
    openTimeAllocationForm(workingTimeId, taskId, duration);
}

/**
 * Open distribute remaining time modal - this now uses the unified openTimeAllocationModal function
 *
 * @param {string} workingTimeId - ID of the working time
 */
function openDistributeTimeModal(workingTimeId) {
    // Just call the main function with useRemainingTime=true
    openTimeAllocationModal(workingTimeId, true);
}

// Export functions for ES6 modules
export { 
    openTimeAllocationModal, 
    openDistributeTimeModal, 
    editTimeAllocation,
    saveTimeAllocation,
    deleteTimeAllocation,
    fetchUIProjectTimes,
    renderUIProjectTimes,
    renderTimeAllocationProgress
};

// Keep minimal global exports for HTML onclick handlers that still need them
window.saveTimeAllocation = saveTimeAllocation;
window.deleteTimeAllocation = deleteTimeAllocation;
window.editTimeAllocation = editTimeAllocation;



// Export functions for testing (works in both Node.js and browser environments)
if (typeof module !== 'undefined' && module.exports) {
    // Node.js environment (for testing)
    module.exports = {
        parseJiraDuration,
        isReasonableDuration,
        MAX_REASONABLE_DURATION_MINUTES
    };
}
