/**
 * Unit tests for sorting utilities
 * Following the Ten Laws of Unit Testing
 */

import { 
    sortWorkingTimesByStartTime, 
    sortWorkingTimesLatestFirst, 
    sortWorkingTimesEarliestFirst,
    sortTasksByName,
    sortTasksAlphabetically,
    sortUIProjectTimesByTaskName,
    sortUIProjectTimesAlphabetically
} from '../../static/js/modules/sorting-utils.js';

describe('Sorting Utilities', () => {
    
    // Test data - realistic working time objects
    const workingTimesData = [
        {
            id: '1',
            start: '2025-06-02T08:00:00.000Z',
            end: '2025-06-02T12:00:00.000Z'
        },
        {
            id: '2', 
            start: '2025-06-02T13:00:00.000Z',
            end: '2025-06-02T17:00:00.000Z'
        },
        {
            id: '3',
            start: '2025-06-02T09:30:00.000Z', 
            end: '2025-06-02T11:30:00.000Z'
        }
    ];

    describe('sortWorkingTimesByStartTime', () => {
        
        test('sorts working times in descending order by default', () => {
            const result = sortWorkingTimesByStartTime(workingTimesData);
            
            expect(result[0].id).toBe('2'); // 13:00 - latest
            expect(result[1].id).toBe('3'); // 09:30 - middle  
            expect(result[2].id).toBe('1'); // 08:00 - earliest
        });

        test('sorts working times in ascending order when specified', () => {
            const result = sortWorkingTimesByStartTime(workingTimesData, 'asc');
            
            expect(result[0].id).toBe('1'); // 08:00 - earliest
            expect(result[1].id).toBe('3'); // 09:30 - middle
            expect(result[2].id).toBe('2'); // 13:00 - latest
        });

        test('sorts working times in descending order when explicitly specified', () => {
            const result = sortWorkingTimesByStartTime(workingTimesData, 'desc');
            
            expect(result[0].id).toBe('2'); // 13:00 - latest
            expect(result[1].id).toBe('3'); // 09:30 - middle
            expect(result[2].id).toBe('1'); // 08:00 - earliest
        });

        test('does not mutate the original array', () => {
            const originalData = [...workingTimesData];
            const result = sortWorkingTimesByStartTime(workingTimesData);
            
            expect(workingTimesData).toEqual(originalData);
            expect(result).not.toBe(workingTimesData); // Different reference
        });

        test('handles empty array', () => {
            const result = sortWorkingTimesByStartTime([]);
            
            expect(result).toEqual([]);
        });

        test('handles single item array', () => {
            const singleItem = [workingTimesData[0]];
            const result = sortWorkingTimesByStartTime(singleItem);
            
            expect(result).toEqual(singleItem);
            expect(result).not.toBe(singleItem); // Should still be a new array
        });

        test('handles working times with same start time', () => {
            const sameStartTimes = [
                { id: '1', start: '2025-06-02T09:00:00.000Z' },
                { id: '2', start: '2025-06-02T09:00:00.000Z' },
                { id: '3', start: '2025-06-02T10:00:00.000Z' }
            ];
            
            const result = sortWorkingTimesByStartTime(sameStartTimes);
            
            // Should maintain relative order for same times and sort the different one
            expect(result[0].id).toBe('3'); // 10:00 - latest
            expect([result[1].id, result[2].id]).toContain('1');
            expect([result[1].id, result[2].id]).toContain('2');
        });

        // Error condition tests
        test('throws error for non-array input', () => {
            expect(() => sortWorkingTimesByStartTime('not an array')).toThrow('workingTimes must be an array');
            expect(() => sortWorkingTimesByStartTime(null)).toThrow('workingTimes must be an array');
            expect(() => sortWorkingTimesByStartTime(undefined)).toThrow('workingTimes must be an array');
        });

        test('throws error for invalid order parameter', () => {
            expect(() => sortWorkingTimesByStartTime(workingTimesData, 'invalid')).toThrow('order must be either "asc" or "desc"');
            expect(() => sortWorkingTimesByStartTime(workingTimesData, 'ascending')).toThrow('order must be either "asc" or "desc"');
        });

        test('throws error for working times without start property', () => {
            const invalidData = [{ id: '1', end: '2025-06-02T12:00:00.000Z' }];
            
            expect(() => sortWorkingTimesByStartTime(invalidData)).toThrow('Working time objects must have a start property');
        });

        test('throws error for invalid date strings', () => {
            const invalidDateData = [{ id: '1', start: 'invalid-date' }];
            
            expect(() => sortWorkingTimesByStartTime(invalidDateData)).toThrow('Working time start values must be valid date strings');
        });

        test('handles various valid date formats', () => {
            const mixedFormats = [
                { id: '1', start: '2025-06-02T08:00:00.000Z' }, // ISO string
                { id: '2', start: '2025-06-02T13:00:00+02:00' }, // ISO with timezone
                { id: '3', start: '2025-06-02 09:30:00' }         // Space-separated
            ];
            
            const result = sortWorkingTimesByStartTime(mixedFormats);
            
            expect(result).toHaveLength(3);
            expect(result[0].id).toBe('2'); // Should handle different formats correctly
        });
    });

    describe('sortWorkingTimesLatestFirst', () => {
        
        test('sorts working times with latest first', () => {
            const result = sortWorkingTimesLatestFirst(workingTimesData);
            
            expect(result[0].id).toBe('2'); // 13:00 - latest
            expect(result[1].id).toBe('3'); // 09:30 - middle
            expect(result[2].id).toBe('1'); // 08:00 - earliest
        });

        test('does not mutate original array', () => {
            const originalData = [...workingTimesData];
            const result = sortWorkingTimesLatestFirst(workingTimesData);
            
            expect(workingTimesData).toEqual(originalData);
        });

        test('handles empty array', () => {
            const result = sortWorkingTimesLatestFirst([]);
            
            expect(result).toEqual([]);
        });
    });

    describe('sortWorkingTimesEarliestFirst', () => {
        
        test('sorts working times with earliest first', () => {
            const result = sortWorkingTimesEarliestFirst(workingTimesData);
            
            expect(result[0].id).toBe('1'); // 08:00 - earliest
            expect(result[1].id).toBe('3'); // 09:30 - middle
            expect(result[2].id).toBe('2'); // 13:00 - latest
        });

        test('does not mutate original array', () => {
            const originalData = [...workingTimesData];
            const result = sortWorkingTimesEarliestFirst(workingTimesData);
            
            expect(workingTimesData).toEqual(originalData);
        });

        test('handles empty array', () => {
            const result = sortWorkingTimesEarliestFirst([]);
            
            expect(result).toEqual([]);
        });
    });

    describe('Edge cases and boundary conditions', () => {
        
        test('handles working times spanning multiple days', () => {
            const multiDay = [
                { id: '1', start: '2025-06-01T23:00:00.000Z' },
                { id: '2', start: '2025-06-02T01:00:00.000Z' },
                { id: '3', start: '2025-06-02T00:30:00.000Z' }
            ];
            
            const result = sortWorkingTimesLatestFirst(multiDay);
            
            expect(result[0].id).toBe('2'); // Latest time
            expect(result[1].id).toBe('3'); // Middle time
            expect(result[2].id).toBe('1'); // Earliest time
        });

        test('handles very close timestamps', () => {
            const closeTimestamps = [
                { id: '1', start: '2025-06-02T09:00:00.000Z' },
                { id: '2', start: '2025-06-02T09:00:00.001Z' }, // 1ms later
                { id: '3', start: '2025-06-02T09:00:00.002Z' }  // 2ms later
            ];
            
            const result = sortWorkingTimesLatestFirst(closeTimestamps);
            
            expect(result[0].id).toBe('3'); // Latest by 2ms
            expect(result[1].id).toBe('2'); // Middle
            expect(result[2].id).toBe('1'); // Earliest
        });
    });

    describe('Task Sorting Functions', () => {
        
        // Test data - realistic task objects
        const tasksData = [
            { id: '1', name: 'Zebra Task', description: 'Last alphabetically' },
            { id: '2', name: 'Alpha Task', description: 'First alphabetically' },
            { id: '3', name: 'Beta Task', description: 'Middle alphabetically' },
            { id: '4', title: 'Charlie Task', description: 'Using title field' },
            { id: '5', name: '', title: 'Delta Task', description: 'Empty name, has title' },
            { id: '6', description: 'No name or title' }
        ];

        describe('sortTasksByName', () => {
            
            test('sorts tasks in ascending order by default', () => {
                const result = sortTasksByName(tasksData);
                
                expect(result[0].id).toBe('6'); // Empty name comes first
                expect(result[1].id).toBe('2'); // Alpha Task
                expect(result[2].id).toBe('3'); // Beta Task
                expect(result[3].id).toBe('4'); // Charlie Task (from title)
                expect(result[4].id).toBe('5'); // Delta Task (from title)
                expect(result[5].id).toBe('1'); // Zebra Task
            });

            test('sorts tasks in descending order when specified', () => {
                const result = sortTasksByName(tasksData, 'desc');
                
                expect(result[0].id).toBe('1'); // Zebra Task
                expect(result[1].id).toBe('5'); // Delta Task
                expect(result[2].id).toBe('4'); // Charlie Task
                expect(result[3].id).toBe('3'); // Beta Task
                expect(result[4].id).toBe('2'); // Alpha Task
                expect(result[5].id).toBe('6'); // Empty name comes last
            });

            test('does not mutate the original array', () => {
                const originalData = [...tasksData];
                const result = sortTasksByName(tasksData);
                
                expect(tasksData).toEqual(originalData);
                expect(result).not.toBe(tasksData);
            });

            test('handles empty array', () => {
                const result = sortTasksByName([]);
                expect(result).toEqual([]);
            });

            test('handles single item array', () => {
                const singleTask = [tasksData[0]];
                const result = sortTasksByName(singleTask);
                
                expect(result).toEqual(singleTask);
                expect(result).not.toBe(singleTask);
            });

            test('handles tasks with same names using ID fallback', () => {
                const sameName = [
                    { id: 'task-2', name: 'Same Task' },
                    { id: 'task-1', name: 'Same Task' },
                    { id: 'task-3', name: 'Different Task' }
                ];
                
                const result = sortTasksByName(sameName);
                
                expect(result[0].id).toBe('task-3'); // Different Task comes first
                expect(result[1].id).toBe('task-1'); // task-1 comes before task-2
                expect(result[2].id).toBe('task-2'); // task-2 comes last
            });

            test('throws error for non-array input', () => {
                expect(() => sortTasksByName('not an array')).toThrow('tasks must be an array');
                expect(() => sortTasksByName(null)).toThrow('tasks must be an array');
                expect(() => sortTasksByName(undefined)).toThrow('tasks must be an array');
            });

            test('throws error for invalid order parameter', () => {
                expect(() => sortTasksByName(tasksData, 'invalid')).toThrow('order must be either "asc" or "desc"');
                expect(() => sortTasksByName(tasksData, 'ascending')).toThrow('order must be either "asc" or "desc"');
            });

            test('handles special characters and numbers in task names', () => {
                const specialTasks = [
                    { id: '1', name: '2. Second Task' },
                    { id: '2', name: '1. First Task' },
                    { id: '3', name: 'Task with (parentheses)' },
                    { id: '4', name: 'Task-with-dashes' }
                ];
                
                const result = sortTasksByName(specialTasks);
                
                expect(result[0].name).toBe('1. First Task');
                expect(result[1].name).toBe('2. Second Task');
                // localeCompare should handle special characters appropriately
            });

            test('supports custom name and ID extractors via lambdas', () => {
                const customTasks = [
                    { taskId: 'task-2', taskName: 'Beta Task' },
                    { taskId: 'task-1', taskName: 'Alpha Task' },
                    { taskId: 'task-3', taskName: 'Alpha Task' } // Same name as task-1
                ];
                
                const result = sortTasksByName(
                    customTasks, 
                    'asc',
                    (task) => task.taskName || "",
                    (task) => task.taskId || ""
                );
                
                expect(result[0].taskName).toBe('Alpha Task');
                expect(result[0].taskId).toBe('task-1'); // Should come before task-3
                expect(result[1].taskName).toBe('Alpha Task');
                expect(result[1].taskId).toBe('task-3'); // Should come after task-1
                expect(result[2].taskName).toBe('Beta Task');
            });

            test('handles missing custom fields gracefully with lambdas', () => {
                const incompleteTasks = [
                    { taskId: 'task-1' }, // No taskName
                    { taskName: 'Beta Task' }, // No taskId
                    { taskId: 'task-2', taskName: 'Alpha Task' }
                ];
                
                const result = sortTasksByName(
                    incompleteTasks, 
                    'asc',
                    (task) => task.taskName || "",
                    (task) => task.taskId || ""
                );
                
                expect(result).toHaveLength(3);
                // Should handle gracefully without throwing
                // Empty names come first, then named tasks in alphabetical order
                expect(result[0].taskName || '').toBe(''); // Empty name first
                expect(result[1].taskName).toBe('Alpha Task'); // Alpha comes before Beta
                expect(result[2].taskName).toBe('Beta Task'); // Beta comes last
            });

            test('uses default field detection when no extractors are provided', () => {
                const mixedTasks = [
                    { id: '1', name: 'Name Task' },
                    { id: '2', title: 'Title Task' },
                    { id: '3', name: '', title: 'Fallback Title' }
                ];
                
                const result = sortTasksByName(mixedTasks);
                
                expect(result[0].title || result[0].name).toBe('Fallback Title');
                expect(result[1].name).toBe('Name Task');
                expect(result[2].title).toBe('Title Task');
            });

            test('supports complex extraction logic with lambdas', () => {
                const complexTasks = [
                    { metadata: { title: 'Complex Task B' }, uuid: 'uuid-2' },
                    { metadata: { title: 'Complex Task A' }, uuid: 'uuid-1' },
                    { metadata: { title: 'Complex Task A' }, uuid: 'uuid-3' } // Same name
                ];
                
                const result = sortTasksByName(
                    complexTasks, 
                    'asc',
                    (task) => task.metadata?.title || "",
                    (task) => task.uuid || ""
                );
                
                expect(result[0].metadata.title).toBe('Complex Task A');
                expect(result[0].uuid).toBe('uuid-1'); // Should come before uuid-3
                expect(result[1].metadata.title).toBe('Complex Task A');
                expect(result[1].uuid).toBe('uuid-3'); // Should come after uuid-1
                expect(result[2].metadata.title).toBe('Complex Task B');
            });
        });

        describe('sortTasksAlphabetically', () => {
            
            test('sorts tasks alphabetically (A-Z)', () => {
                const result = sortTasksAlphabetically(tasksData);
                
                expect(result[0].id).toBe('6'); // Empty name
                expect(result[1].id).toBe('2'); // Alpha Task
                expect(result[2].id).toBe('3'); // Beta Task
                expect(result[3].id).toBe('4'); // Charlie Task
                expect(result[4].id).toBe('5'); // Delta Task
                expect(result[5].id).toBe('1'); // Zebra Task
            });

            test('does not mutate original array', () => {
                const originalData = [...tasksData];
                const result = sortTasksAlphabetically(tasksData);
                
                expect(tasksData).toEqual(originalData);
            });
        });
    });

    describe('UI Project Time Sorting Functions', () => {
        
        // Test data - realistic UI project time objects
        const uiProjectTimesData = [
            { 
                task_id: 'task-3', 
                task_name: 'Zebra Project',
                duration_minutes: 60
            },
            { 
                task_id: 'task-1', 
                task_name: 'Alpha Project',
                duration_minutes: 30
            },
            { 
                task_id: 'task-2', 
                task_name: 'Beta Project',
                duration_minutes: 45
            },
            { 
                task_id: 'task-4', 
                task_name: 'Alpha Project', // Same name as task-1
                duration_minutes: 90
            },
            { 
                task_id: 'task-5', 
                task_name: '',
                duration_minutes: 15
            }
        ];

        describe('sortUIProjectTimesByTaskName', () => {
            
            test('sorts UI project times in ascending order by default', () => {
                const result = sortUIProjectTimesByTaskName(uiProjectTimesData);
                
                expect(result[0].task_id).toBe('task-5'); // Empty name first
                expect(result[1].task_name).toBe('Alpha Project');
                expect(result[2].task_name).toBe('Alpha Project');
                expect(result[3].task_name).toBe('Beta Project');
                expect(result[4].task_name).toBe('Zebra Project');
            });

            test('uses task_id as fallback when names are the same', () => {
                const result = sortUIProjectTimesByTaskName(uiProjectTimesData);
                
                // Find the two Alpha Project entries
                const alphaProjects = result.filter(item => item.task_name === 'Alpha Project');
                expect(alphaProjects).toHaveLength(2);
                expect(alphaProjects[0].task_id).toBe('task-1'); // Should come before task-4
                expect(alphaProjects[1].task_id).toBe('task-4');
            });

            test('sorts UI project times in descending order when specified', () => {
                const result = sortUIProjectTimesByTaskName(uiProjectTimesData, 'desc');
                
                expect(result[0].task_name).toBe('Zebra Project');
                expect(result[1].task_name).toBe('Beta Project');
                expect(result[2].task_name).toBe('Alpha Project');
                expect(result[3].task_name).toBe('Alpha Project');
                expect(result[4].task_id).toBe('task-5'); // Empty name last in desc
            });

            test('uses task_id fallback in descending order', () => {
                const result = sortUIProjectTimesByTaskName(uiProjectTimesData, 'desc');
                
                // Find the two Alpha Project entries in descending order
                const alphaProjects = result.filter(item => item.task_name === 'Alpha Project');
                expect(alphaProjects[0].task_id).toBe('task-4'); // Should come before task-1 in desc
                expect(alphaProjects[1].task_id).toBe('task-1');
            });

            test('does not mutate the original array', () => {
                const originalData = [...uiProjectTimesData];
                const result = sortUIProjectTimesByTaskName(uiProjectTimesData);
                
                expect(uiProjectTimesData).toEqual(originalData);
                expect(result).not.toBe(uiProjectTimesData);
            });

            test('handles empty array', () => {
                const result = sortUIProjectTimesByTaskName([]);
                expect(result).toEqual([]);
            });

            test('handles single item array', () => {
                const singleItem = [uiProjectTimesData[0]];
                const result = sortUIProjectTimesByTaskName(singleItem);
                
                expect(result).toEqual(singleItem);
                expect(result).not.toBe(singleItem);
            });

            test('throws error for non-array input', () => {
                expect(() => sortUIProjectTimesByTaskName('not an array')).toThrow('uiProjectTimes must be an array');
                expect(() => sortUIProjectTimesByTaskName(null)).toThrow('uiProjectTimes must be an array');
                expect(() => sortUIProjectTimesByTaskName(undefined)).toThrow('uiProjectTimes must be an array');
            });

            test('throws error for invalid order parameter', () => {
                expect(() => sortUIProjectTimesByTaskName(uiProjectTimesData, 'invalid')).toThrow('order must be either "asc" or "desc"');
                expect(() => sortUIProjectTimesByTaskName(uiProjectTimesData, 'ascending')).toThrow('order must be either "asc" or "desc"');
            });

            test('handles missing task_name and task_id properties gracefully', () => {
                const incompleteData = [
                    { duration_minutes: 30 }, // No task_name or task_id
                    { task_name: 'Beta', duration_minutes: 45 },
                    { task_id: 'task-1', duration_minutes: 60 } // No task_name
                ];
                
                const result = sortUIProjectTimesByTaskName(incompleteData);
                
                expect(result).toHaveLength(3);
                // Should handle gracefully without throwing errors
                expect(result[0].task_name || '').toBe(''); // Empty task_name first
                expect(result[1].task_name || '').toBe(''); // Empty task_name 
                expect(result[2].task_name).toBe('Beta'); // Named task last
            });
        });

        describe('sortUIProjectTimesAlphabetically', () => {
            
            test('sorts UI project times alphabetically by task name (A-Z)', () => {
                const result = sortUIProjectTimesAlphabetically(uiProjectTimesData);
                
                expect(result[0].task_id).toBe('task-5'); // Empty name
                expect(result[1].task_name).toBe('Alpha Project');
                expect(result[2].task_name).toBe('Alpha Project');
                expect(result[3].task_name).toBe('Beta Project');
                expect(result[4].task_name).toBe('Zebra Project');
            });

            test('does not mutate original array', () => {
                const originalData = [...uiProjectTimesData];
                const result = sortUIProjectTimesAlphabetically(uiProjectTimesData);
                
                expect(uiProjectTimesData).toEqual(originalData);
            });
        });

        describe('Integration with realistic data', () => {
            
            test('handles complex task names with special characters', () => {
                const complexTasks = [
                    { task_id: '1', task_name: 'Project: API Development (v2.1)' },
                    { task_id: '2', task_name: 'Project: Database Migration' },
                    { task_id: '3', task_name: 'Bug Fix: Login Issues #123' },
                    { task_id: '4', task_name: 'Feature: User Management' }
                ];
                
                const result = sortUIProjectTimesAlphabetically(complexTasks);
                
                expect(result[0].task_name).toBe('Bug Fix: Login Issues #123');
                expect(result[1].task_name).toBe('Feature: User Management');
                expect(result[2].task_name).toBe('Project: API Development (v2.1)');
                expect(result[3].task_name).toBe('Project: Database Migration');
            });

            test('handles multilingual task names', () => {
                const multilingualTasks = [
                    { task_id: '1', task_name: 'Ząbek Task' },
                    { task_id: '2', task_name: 'Änderung Task' },
                    { task_id: '3', task_name: 'Basic Task' }
                ];
                
                const result = sortUIProjectTimesAlphabetically(multilingualTasks);
                
                // localeCompare should handle special characters properly
                expect(result).toHaveLength(3);
                expect(result[0].task_name).toBe('Änderung Task');
                expect(result[1].task_name).toBe('Basic Task');
                expect(result[2].task_name).toBe('Ząbek Task');
            });
        });
    });
});