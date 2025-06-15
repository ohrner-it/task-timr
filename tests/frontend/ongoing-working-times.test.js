/**
 * Tests for ongoing working time frontend functionality
 * Tests the JavaScript changes for handling working times with null end times
 */

const { 
    renderWorkingTimeCard,
    calculateDurationInMinutes,
    formatTimeFromISOString
} = require('../../static/js/main.js');

// Mock global state object needed by renderWorkingTimeCard
global.state = {
    attendanceTypes: [
        { id: "attendance-type-id", name: "mobiles Arbeiten" }
    ]
};

describe('Ongoing Working Time Frontend Tests', () => {
    
    // Store original Date constructor
    const originalDate = global.Date;
    
    beforeEach(() => {
        // Mock Date to always return consistent times
        global.Date = jest.fn((dateString) => {
            if (dateString) {
                return new originalDate(dateString);
            }
            // Default "now" for fallback calculations (local timezone)
            return new originalDate("2025-06-15T10:00:00");
        });
        // Copy all static methods and prototype
        Object.setPrototypeOf(global.Date, originalDate);
        Object.assign(global.Date, originalDate);
        global.Date.prototype = originalDate.prototype;
    });
    
    afterEach(() => {
        // Restore original Date
        global.Date = originalDate;
    });
    
    describe('renderWorkingTimeCard', () => {
        
        test('should handle ongoing working time with null end', () => {
            const ongoingWorkingTime = {
                id: "ongoing-id",
                start: "2025-06-15T09:00:00", // Local timezone
                end: null,
                duration: {
                    type: "ongoing",
                    minutes: 120,
                    minutes_rounded: 120
                },
                break_time_total_minutes: 15,
                working_time_type: {
                    id: "attendance-type-id",
                    name: "mobiles Arbeiten"
                }
            };
            
            const result = renderWorkingTimeCard(ongoingWorkingTime);
            
            // Verify the HTML contains ongoing indicators
            expect(result).toContain("09:00 - ongoing");
            expect(result).toContain("(running)");
            expect(result).toContain("bg-success"); // Green badge for ongoing
            expect(result).toContain("1h 45m (running)"); // 120 - 15 break = 105m = 1h 45m
            expect(result).toContain("data-id=\"ongoing-id\"");
        });
        
        test('should handle completed working time with end time', () => {
            const completedWorkingTime = {
                id: "completed-id", 
                start: "2025-06-15T09:00:00", // Local timezone
                end: "2025-06-15T11:00:00", // Local timezone
                break_time_total_minutes: 15,
                working_time_type: {
                    id: "attendance-type-id",
                    name: "mobiles Arbeiten"
                }
            };
            
            const result = renderWorkingTimeCard(completedWorkingTime);
            
            // Verify the HTML contains proper end time and no ongoing indicators
            expect(result).toContain("09:00 - 11:00");
            expect(result).not.toContain("ongoing");
            expect(result).not.toContain("(running)");
            expect(result).toContain("bg-secondary"); // Secondary badge for completed
            expect(result).toContain("1h 45m"); // 120 - 15 break = 105m = 1h 45m
            expect(result).not.toContain("1h 45m (running)");
        });
        
        test('should handle ongoing working time without duration info', () => {
            const ongoingWithoutDuration = {
                id: "ongoing-no-duration",
                start: "2025-06-15T09:00:00", // Local timezone
                end: null,
                // No duration field - should fallback to time calculation
                break_time_total_minutes: 0,
                working_time_type: {
                    id: "attendance-type-id",
                    name: "mobiles Arbeiten"
                }
            };
            
            // Date is already mocked in beforeEach to return 10:00 for "now"
            
            const result = renderWorkingTimeCard(ongoingWithoutDuration);
            
            // Should calculate 60 minutes from start to mocked current time
            expect(result).toContain("09:00 - ongoing");
            expect(result).toContain("1h 0m (running)"); // 60 minutes = 1h 0m
            expect(result).toContain("bg-success");
        });
        
        test('should handle ongoing working time with zero duration', () => {
            const ongoingZeroDuration = {
                id: "ongoing-zero",
                start: "2025-06-15T09:00:00", // Local timezone
                end: null,
                duration: {
                    type: "ongoing",
                    minutes: 0,
                    minutes_rounded: 0
                },
                break_time_total_minutes: 0,
                working_time_type: {
                    id: "attendance-type-id",
                    name: "mobiles Arbeiten"
                }
            };
            
            const result = renderWorkingTimeCard(ongoingZeroDuration);
            
            expect(result).toContain("09:00 - ongoing");
            expect(result).toContain("0m (running)");
            expect(result).toContain("bg-success");
        });
        
        test('should handle ongoing working time with breaks exceeding duration', () => {
            const ongoingExcessiveBreaks = {
                id: "ongoing-excessive-breaks",
                start: "2025-06-15T09:00:00", // Local timezone
                end: null,
                duration: {
                    type: "ongoing", 
                    minutes: 60,
                    minutes_rounded: 60
                },
                break_time_total_minutes: 90, // More breaks than total time
                working_time_type: {
                    id: "attendance-type-id",
                    name: "mobiles Arbeiten"
                }
            };
            
            const result = renderWorkingTimeCard(ongoingExcessiveBreaks);
            
            expect(result).toContain("09:00 - ongoing");
            expect(result).toContain("bg-success");
            // Note: The actual implementation will show negative duration
            // Frontend should handle this gracefully by showing the calculated result
        });
        
        test('should disable edit/delete buttons for ongoing working times', () => {
            const ongoingWorkingTime = {
                id: "ongoing-id",
                start: "2025-06-15T09:00:00",
                end: null,
                duration: {
                    type: "ongoing",
                    minutes: 120,
                    minutes_rounded: 120
                },
                break_time_total_minutes: 15,
                working_time_type: {
                    id: "attendance-type-id",
                    name: "mobiles Arbeiten"
                }
            };
            
            const result = renderWorkingTimeCard(ongoingWorkingTime);
            
            // Should contain disabled lock button instead of edit/delete buttons
            expect(result).toContain("bi-lock");
            expect(result).toContain("Ongoing working times cannot be edited");
            expect(result).not.toContain("bi-pencil");
            expect(result).not.toContain("bi-trash");
        });
        
        test('should enable edit/delete buttons for completed working times', () => {
            const completedWorkingTime = {
                id: "completed-id", 
                start: "2025-06-15T09:00:00",
                end: "2025-06-15T11:00:00",
                break_time_total_minutes: 15,
                working_time_type: {
                    id: "attendance-type-id",
                    name: "mobiles Arbeiten"
                }
            };
            
            const result = renderWorkingTimeCard(completedWorkingTime);
            
            // Should contain edit and delete buttons
            expect(result).toContain("bi-pencil");
            expect(result).toContain("bi-trash");
            expect(result).toContain("edit-working-time");
            expect(result).toContain("delete-working-time");
            expect(result).not.toContain("bi-lock");
        });

        test('should handle non-editable working time types', () => {
            const nonEditableWorkingTime = {
                id: "non-editable-id",
                start: "2025-06-15T09:00:00",
                end: "2025-06-15T11:00:00",
                break_time_total_minutes: 15,
                working_time_type: {
                    id: "non-attendance-type-id",
                    name: "Other Work Type"
                }
            };
            
            const result = renderWorkingTimeCard(nonEditableWorkingTime);
            
            // Should show read-only indicators
            expect(result).toContain("Read-only");
            expect(result).toContain("bg-warning");
            expect(result).toContain("bi-lock");
            expect(result).toContain("Read-only - non-attendance time types cannot be edited");
        });
    });
    
    describe('Helper Functions', () => {
        
        test('calculateDurationInMinutes should calculate correctly', () => {
            const start = "2025-06-15T09:00:00";
            const end = "2025-06-15T11:00:00";
            
            const duration = calculateDurationInMinutes(start, end);
            
            expect(duration).toBe(120); // 2 hours = 120 minutes
        });
        
        test('formatTimeFromISOString should format time correctly', () => {
            const isoString = "2025-06-15T09:30:00";
            
            const formatted = formatTimeFromISOString(isoString);
            
            expect(formatted).toBe("09:30");
        });
        
        test('formatTimeFromISOString should pad single digits', () => {
            const isoString = "2025-06-15T05:05:00";
            
            const formatted = formatTimeFromISOString(isoString);
            
            expect(formatted).toBe("05:05");
        });
    });
    
    describe('Time Display Integration', () => {
        
        test('should format ongoing time display correctly in full HTML', () => {
            const ongoingWorkingTime = {
                id: "test-id",
                start: "2025-06-15T14:30:00", // Local timezone
                end: null,
                duration: { minutes: 75 },
                break_time_total_minutes: 0,
                working_time_type: {
                    id: "attendance-type-id",
                    name: "mobiles Arbeiten"
                }
            };
            
            const result = renderWorkingTimeCard(ongoingWorkingTime);
            
            expect(result).toContain("14:30 - ongoing");
            expect(result).toContain("1h 15m (running)"); // 75 minutes = 1h 15m
        });
        
        test('should format completed time display correctly in full HTML', () => {
            const completedWorkingTime = {
                id: "test-id",
                start: "2025-06-15T14:30:00", // Local timezone
                end: "2025-06-15T16:30:00", // Local timezone
                break_time_total_minutes: 0,
                working_time_type: {
                    id: "attendance-type-id",
                    name: "mobiles Arbeiten"
                }
            };
            
            const result = renderWorkingTimeCard(completedWorkingTime);
            
            expect(result).toContain("14:30 - 16:30");
            expect(result).toContain("2h"); // 120 minutes = 2 hours
            expect(result).not.toContain("(running)");
        });
    });
    
    describe('Badge Styling Integration', () => {
        
        test('should use success badge for ongoing working times in full HTML', () => {
            const ongoingWorkingTime = {
                id: "test-id",
                start: "2025-06-15T09:00:00",
                end: null,
                duration: { minutes: 60 },
                break_time_total_minutes: 0,
                working_time_type: {
                    id: "attendance-type-id",
                    name: "mobiles Arbeiten"
                }
            };
            
            const result = renderWorkingTimeCard(ongoingWorkingTime);
            
            expect(result).toContain("bg-success");
            expect(result).not.toContain("bg-secondary");
        });
        
        test('should use secondary badge for completed working times in full HTML', () => {
            const completedWorkingTime = {
                id: "test-id",
                start: "2025-06-15T09:00:00",
                end: "2025-06-15T11:00:00",
                break_time_total_minutes: 0,
                working_time_type: {
                    id: "attendance-type-id",
                    name: "mobiles Arbeiten"
                }
            };
            
            const result = renderWorkingTimeCard(completedWorkingTime);
            
            expect(result).toContain("bg-secondary");
            expect(result).not.toContain("bg-success");
        });
    });
});