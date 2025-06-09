/**
 * Mock implementation of functions required for frontend tests
 * This file provides implementations of the functions that are
 * referenced in the frontend tests but might not be directly
 * accessible in the test environment.
 */

// Mock implementations of functions referenced in tests
global.loadData = async function (dateString) {
    // Implementation for loading data for a specific date
    const response = await fetch(`/api/working-times?date=${dateString}`);

    if (!response.ok) {
        const data = await response.json();
        throw new Error(data.error || "Failed to load working times");
    }

    const data = await response.json();

    // Store the working times in state
    if (data && data.data) {
        global.state.workingTimes = data.data;
    } else if (Array.isArray(data)) {
        global.state.workingTimes = data;
    } else {
        console.error("Unexpected data format for working times:", data);
        global.state.workingTimes = [];
    }

    // Update date in state
    global.state.date = new Date(dateString);

    // Update UI elements
    const dateDisplay = document.getElementById("date-display");
    if (dateDisplay) {
        dateDisplay.textContent = new Date(dateString).toLocaleDateString();
    }

    const dateInput = document.getElementById("date-input");
    if (dateInput) {
        dateInput.value = dateString;
    }

    return global.state.workingTimes;
};

global.renderUIProjectTimes = function (projectTimesData, workingTime) {
    const workingTimeId = workingTime.id;
    const container = document.getElementById(`project-times-${workingTimeId}`);

    if (!container) {
        console.error(
            `Container for project times of working time ${workingTimeId} not found`,
        );
        return false;
    }

    if (!projectTimesData || !projectTimesData.ui_project_times) {
        console.error(
            "Invalid UI project times data structure",
            projectTimesData,
        );
        container.innerHTML =
            '<div class="text-muted">No time allocations available</div>';
        return false;
    }

    const uiProjectTimes = projectTimesData.ui_project_times;
    const totalDuration = projectTimesData.total_duration || 0;
    const remainingDuration = projectTimesData.remaining_duration || 0;
    const isFullyAllocated = projectTimesData.is_fully_allocated || false;

    // Create table HTML for the UI project times
    let html = '<table class="table table-sm project-times-table">';

    // Add table header
    html += `
        <thead>
            <tr>
                <th>Task</th>
                <th>Duration</th>
                <th>Actions</th>
            </tr>
        </thead>
    `;

    // Add table body
    html += "<tbody>";

    uiProjectTimes.forEach((uiPt) => {
        html += `
            <tr class="ui-project-time-item" 
                data-task-id="${uiPt.task_id}" 
                data-task-name="${uiPt.task_name}" 
                data-task-breadcrumbs="${uiPt.task_breadcrumbs || ""}" 
                data-duration="${uiPt.duration_minutes}">
                <td>
                    <div class="task-name">${uiPt.task_name}</div>
                    <div class="task-breadcrumbs small text-muted">${uiPt.task_breadcrumbs || ""}</div>
                </td>
                <td>${global.formatDuration(uiPt.duration_minutes)}</td>
                <td>
                    <div class="btn-group btn-group-sm">
                        <button class="btn btn-outline-primary edit-time-allocation">Edit</button>
                        <button class="btn btn-outline-danger delete-time-allocation">Delete</button>
                    </div>
                </td>
            </tr>
        `;
    });

    html += "</tbody></table>";

    // Update container with the table
    container.innerHTML = html;

    // Return true to indicate successful rendering
    return true;
};

global.saveTimeAllocation = async function () {
    const form = document.getElementById("time-allocation-form");
    if (!form) return;

    const taskId = form.dataset.taskId; // For editing existing UI time allocation
    const workingTimeId = form.dataset.workingTimeId;
    const taskIdInput = document.getElementById("selected-task-id");
    const durationInput = document.getElementById("time-allocation-duration");

    // Validate form elements exist
    if (!taskIdInput || !durationInput) {
        global.showAlert(
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
        global.showAlert("Please select a task before saving", "warning", true);
        const taskSearch = document.getElementById("task-search");
        if (taskSearch) taskSearch.focus();
        return;
    }

    // Validate duration input
    if (isNaN(duration) || duration <= 0) {
        global.showAlert(
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

    // Show loading indicator
    const submitBtn = form.querySelector('button[type="submit"]');
    if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.innerHTML =
            '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Saving...';
    }

    try {
        let response;

        if (taskId) {
            // For editing an existing UI time allocation, use PATCH
            const data = {
                duration_minutes: duration,
                task_name: taskName,
            };

            response = await fetch(
                `/api/working-times/${workingTimeId}/ui-project-times/${taskId}`,
                {
                    method: "PATCH",
                    headers: {
                        "Content-Type": "application/json",
                    },
                    body: JSON.stringify(data),
                },
            );
        } else {
            // For new UI time allocations, use POST
            const data = {
                task_id: selectedTaskId,
                task_name: taskName,
                duration_minutes: duration,
            };

            response = await fetch(
                `/api/working-times/${workingTimeId}/ui-project-times`,
                {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                    },
                    body: JSON.stringify(data),
                },
            );
        }

        // Check response
        if (!response.ok) {
            const data = await response.json();
            throw new Error(data.error || "Failed to save time allocation");
        }

        // Parse response data
        const data = await response.json();

        // Close modal
        const modal = global.bootstrap.Modal.getInstance(
            document.getElementById("time-allocation-modal"),
        );
        if (modal) {
            modal.hide();
        }

        // Show success message
        global.showAlert("Time allocation saved successfully", "success");

        // Update the UI
        global.handleUIProjectTimeResponse(data, workingTimeId);

        return data;
    } catch (error) {
        console.error("Error:", error);
        global.showAlert(`Error: ${error.message}`, "danger", true);
    } finally {
        // Reset button
        if (submitBtn) {
            submitBtn.disabled = false;
            submitBtn.innerHTML = "Save";
        }
    }
};

global.deleteTimeAllocation = async function (taskId, workingTimeId) {
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
        // Send delete request
        const response = await fetch(
            `/api/working-times/${workingTimeId}/ui-project-times/${taskId}`,
            {
                method: "DELETE",
            },
        );

        // Check response
        if (!response.ok) {
            const data = await response.json();
            throw new Error(data.error || "Failed to delete time allocation");
        }

        // Parse response data
        const data = await response.json();

        // Show success message
        global.showAlert("Time allocation deleted successfully", "success");

        // Update the UI
        global.handleUIProjectTimeResponse(data, workingTimeId);

        return data;
    } catch (error) {
        console.error("Error:", error);
        global.showAlert(`Error: ${error.message}`, "danger");

        // Reset opacity
        if (timeAllocationItem) {
            timeAllocationItem.style.opacity = "1";
        }
    }
};

global.openAddRemainingTimeModal = function (workingTimeId, remainingMinutes) {
    // Call openTimeAllocationForm
    global.openTimeAllocationForm(workingTimeId);

    // Update modal title
    const modalTitle = document.getElementById("time-allocation-modal-label");
    if (modalTitle) {
        modalTitle.textContent = "Distribute Remaining Time";
    }

    // Add a message about remaining time
    const modalAlerts = document.querySelector(
        "#time-allocation-modal .modal-alerts",
    );
    if (modalAlerts) {
        modalAlerts.innerHTML = `
            <div class="alert alert-info">
                <i class="bi bi-info-circle me-2"></i>
                There are <strong>${global.formatDuration(remainingMinutes)}</strong> of unallocated time. 
                Please select a task to allocate this time to.
            </div>
        `;
    }

    // Set duration input to remaining minutes
    const durationInput = document.getElementById("time-allocation-duration");
    if (durationInput) {
        durationInput.value = remainingMinutes;
    }
};

global.openTimeAllocationForm = function (workingTimeId) {
    // Get form and reset it
    const form = document.getElementById("time-allocation-form");
    if (!form) return;

    form.reset();
    delete form.dataset.taskId; // Remove task ID for new entries
    form.dataset.workingTimeId = workingTimeId;

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
        durationInput.value = 60; // Default to 1 hour
    }

    // Update modal title
    const modalTitle = document.getElementById("time-allocation-modal-label");
    if (modalTitle) {
        modalTitle.textContent = "Add Time Allocation";
    }
};

global.handleUIProjectTimeResponse = function (data, workingTimeId) {
    // Update UI with response data
    if (data && data.ui_project_times) {
        // Update UI project times display
        const container = document.getElementById(
            `project-times-${workingTimeId}`,
        );
        if (container) {
            global.renderUIProjectTimes(data, { id: workingTimeId });
            return true;
        }
    }
    return false;
};

global.fetchUIProjectTimes = async function (workingTimeId) {
    try {
        const response = await fetch(
            `/api/working-times/${workingTimeId}/ui-project-times`,
        );

        if (!response.ok) {
            const data = await response.json();
            throw new Error(data.error || "Failed to load UI project times");
        }

        return await response.json();
    } catch (error) {
        console.error("Error:", error);
        global.showAlert(`Error: ${error.message}`, "danger");
        return null;
    }
};

// Initialize global state
global.state = {
    date: new Date(),
    workingTimes: [],
    tasks: [],
    recentTasks: [],
};

// Utility functions
global.formatDuration = function (minutes) {
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    if (hours > 0) {
        return `${hours}h ${mins}m`;
    } else {
        return `${mins}m`;
    }
};

global.escapeHtml = function (text) {
    if (!text) return "";
    return String(text)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
};

global.showAlert = jest.fn();
global.logMessage = jest.fn();
