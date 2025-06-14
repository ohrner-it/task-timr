"""
Task Timr - Utility classes for time tracking and project management
Contains ProjectTimeConsolidator and UIProjectTime classes

Copyright (c) 2025 Ohrner IT GmbH
Licensed under the MIT License
"""

import json
import logging
from datetime import datetime, timedelta
from utils import parse_iso_datetime
from typing import List, Dict, Any, Optional, Set, Tuple, Union

from timr_api import TimrApi, TimrApiError

logger = logging.getLogger(__name__)


class UIProjectTime:
    """
    UI representation of a project time entry for a specific task.

    This class represents the time worked on a specific task during a work time.
    It focuses on the task and duration rather than the specific time slots.
    """

    def __init__(self,
                 task_id: str,
                 task_name: str,
                 duration_minutes: int = 0,
                 task_breadcrumbs: str = ""):
        """
        Initialize a UIProjectTime object.

        Args:
            task_id (str): The ID of the task this project time belongs to
            task_name (str): The name of the task
            duration_minutes (int): Duration in minutes
            task_breadcrumbs (str): Breadcrumb path for the task, for hierarchical display
        """
        self.task_id = task_id
        self.task_name = task_name
        self.task_breadcrumbs = task_breadcrumbs
        self.duration_minutes = duration_minutes
        self.deleted = False  # Flag to mark for deletion instead of actual deletion
        self.project_time_ids = []  # IDs of all aggregated Timr project times
        self.source_project_times = []  # Original Timr project time objects

    def mark_for_deletion(self):
        """
        Mark this UIProjectTime for deletion rather than actually deleting it.
        This allows the UI to still display it but flag it as to be removed on save.
        """
        self.deleted = True

    def add_project_time(self, project_time: Dict[str, Any]):
        """
        Add a Timr project time to this UIProjectTime's aggregated times.

        Args:
            project_time (dict): A Timr project time entry
        """
        if project_time and "id" in project_time:
            self.project_time_ids.append(project_time["id"])
            self.source_project_times.append(project_time)

    def toJSON(self):
        """
        Convert the UIProjectTime to a JSON string.

        Returns:
            str: JSON string representation of this UIProjectTime
        """
        return json.dumps(self.to_dict())

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the UIProjectTime to a dictionary for serialization.

        Returns:
            dict: Dictionary representation of this UIProjectTime
        """
        return {
            "task_id": self.task_id,
            "task_name": self.task_name,
            "task_breadcrumbs": self.task_breadcrumbs,
            "duration_minutes": self.duration_minutes,
            "deleted": self.deleted,
            "project_time_ids": self.project_time_ids
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UIProjectTime':
        """
        Create a UIProjectTime instance from a dictionary.

        Args:
            data (dict): Dictionary with UIProjectTime attributes

        Returns:
            UIProjectTime: A new UIProjectTime instance
        """
        ui_project_time = cls(task_id=data.get("task_id", ""),
                              task_name=data.get("task_name", ""),
                              duration_minutes=data.get("duration_minutes", 0),
                              task_breadcrumbs=data.get(
                                  "task_breadcrumbs", ""))
        ui_project_time.deleted = data.get("deleted", False)
        ui_project_time.project_time_ids = data.get("project_time_ids", [])
        return ui_project_time


class ProjectTimeConsolidator:
    """
    Utility class for consolidating project times related to working times.

    This class bridges the gap between Timr's time slot-based model and a more
    user-friendly task-based model where users only care about how much time
    they spent on each task, not when exactly they worked on what.

    PERFORMANCE OPTIMIZATION:
    Uses differential updates to minimize API calls when modifying tasks:

    - Compares current state (from Timr) vs desired state (from UI changes)  
    - Only creates/updates/deletes project times that actually changed
    - Handles cascading time shifts automatically when tasks are added/modified

    Example efficiency gains:
    - Adding 1 task to 5 existing: 1 create + 2-3 updates = 3-4 calls (vs 11 calls)
    - Updating 1 task duration: 1 update + 1-2 cascading updates = 2-3 calls (vs 11 calls)
    - Deleting 1 task: 1 delete + 1-2 cascading updates = 2-3 calls (vs 10 calls)

    OVERLAP PREVENTION:
    Tasks are assigned sequential, non-overlapping time slots:
    1. Consistent ordering by task_id ensures predictable time allocation
    2. Sequential time allocation (task N end = task N+1 start) prevents gaps/overlaps
    3. Differential updates maintain proper timing relationships automatically
    """

    def __init__(self, timr_api: TimrApi):
        """
        Initialize the ProjectTimeConsolidator.

        Args:
            timr_api (TimrApi): An instance of the TimrApi client
        """
        self.timr_api = timr_api

    def get_ui_project_times(
            self, working_time: Dict[str, Any]) -> List[UIProjectTime]:
        """
        Get UIProjectTime objects for a working time.

        Args:
            working_time (dict): The working time entry

        Returns:
            list: List of UIProjectTime objects
        """
        # Get consolidated project times
        consolidated_data = self.consolidate_project_times(working_time)

        # Return the UI project times
        return consolidated_data.get("ui_project_times", [])

    def add_ui_project_time(self,
                            working_time: Dict[str, Any],
                            task_id: str,
                            task_name: str,
                            duration_minutes: int,
                            task_breadcrumbs: str = "") -> Dict[str, Any]:
        """
        Add a new UIProjectTime to a working time using incremental updates.

        Args:
            working_time (dict): The working time entry
            task_id (str): Task ID
            task_name (str): Task name
            duration_minutes (int): Duration in minutes
            task_breadcrumbs (str, optional): Task breadcrumbs for hierarchical display

        Returns:
            dict: Updated consolidated data
        """
        logger.info(
            f"ADD_UI_PROJECT_TIME: Starting add operation for task {task_id} with {duration_minutes} minutes"
        )

        # Get existing UI project times
        ui_project_times = self.get_ui_project_times(working_time)
        logger.info(
            f"ADD_UI_PROJECT_TIME: Found {len(ui_project_times)} existing UI project times"
        )

        # Log existing tasks and their durations
        for i, pt in enumerate(ui_project_times):
            logger.info(
                f"ADD_UI_PROJECT_TIME: Existing task {i}: {pt.task_id} = {pt.duration_minutes} minutes"
            )

        # Check if this task already exists
        existing_task = next(
            (pt for pt in ui_project_times if pt.task_id == task_id), None)

        # If task exists, ADD to it instead of replacing
        if existing_task:
            old_duration = existing_task.duration_minutes
            existing_task.duration_minutes += duration_minutes  # ADD instead of replace
            existing_task.task_name = task_name
            if task_breadcrumbs:
                existing_task.task_breadcrumbs = task_breadcrumbs

            # Use targeted update for existing task
            logger.info(
                f"ADD_UI_PROJECT_TIME: Incrementally updating existing task {task_id}: {old_duration}m -> {existing_task.duration_minutes}m (added {duration_minutes}m)"
            )
            self.apply_differential_updates(working_time, ui_project_times)
        else:
            # Create new UI project time
            new_ui_pt = UIProjectTime(task_id=task_id,
                                      task_name=task_name,
                                      duration_minutes=duration_minutes,
                                      task_breadcrumbs=task_breadcrumbs)
            ui_project_times.append(new_ui_pt)

            # Use targeted creation for new task
            logger.info(
                f"ADD_UI_PROJECT_TIME: Incrementally adding new task {task_id}: {duration_minutes}m"
            )
            self.apply_differential_updates(working_time, ui_project_times)

        # Return updated consolidated data
        result = self.consolidate_project_times(working_time)
        logger.info(
            f"ADD_UI_PROJECT_TIME: Final result has {len(result.get('ui_project_times', []))} UI project times"
        )
        for i, pt in enumerate(result.get('ui_project_times', [])):
            logger.info(
                f"ADD_UI_PROJECT_TIME: Final task {i}: {pt.task_id} = {pt.duration_minutes} minutes"
            )

        return result

    def update_ui_project_time(self,
                               working_time: Dict[str, Any],
                               task_id: str,
                               duration_minutes: int,
                               task_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Update a UIProjectTime for a working time using incremental updates.

        Args:
            working_time (dict): The working time entry
            task_id (str): Task ID to update
            duration_minutes (int): New duration in minutes
            task_name (str, optional): New task name

        Returns:
            dict: Updated consolidated data
        """
        logger.info(
            f"UPDATE_UI_PROJECT_TIME: Starting update operation for task {task_id} to {duration_minutes} minutes"
        )

        # Get existing UI project times
        ui_project_times = self.get_ui_project_times(working_time)
        logger.info(
            f"UPDATE_UI_PROJECT_TIME: Found {len(ui_project_times)} existing UI project times"
        )

        # Log existing tasks and their durations
        for i, pt in enumerate(ui_project_times):
            logger.info(
                f"UPDATE_UI_PROJECT_TIME: Existing task {i}: {pt.task_id} = {pt.duration_minutes} minutes"
            )

        # Find the task to update
        task_to_update = next(
            (pt for pt in ui_project_times if pt.task_id == task_id), None)

        if not task_to_update:
            logger.error(
                f"UPDATE_UI_PROJECT_TIME: Task with ID {task_id} not found in working time"
            )
            raise ValueError(
                f"Task with ID {task_id} not found in working time")

        old_duration = task_to_update.duration_minutes

        # Update task (REPLACE for updates, not add)
        task_to_update.duration_minutes = duration_minutes
        if task_name:
            task_to_update.task_name = task_name

        # Use targeted update for this specific task
        logger.info(
            f"UPDATE_UI_PROJECT_TIME: Incrementally updating task {task_id}: {old_duration}m -> {duration_minutes}m (replaced)"
        )
        self.apply_differential_updates(working_time, ui_project_times)

        # Return updated consolidated data
        result = self.consolidate_project_times(working_time)
        logger.info(
            f"UPDATE_UI_PROJECT_TIME: Final result has {len(result.get('ui_project_times', []))} UI project times"
        )
        for i, pt in enumerate(result.get('ui_project_times', [])):
            logger.info(
                f"UPDATE_UI_PROJECT_TIME: Final task {i}: {pt.task_id} = {pt.duration_minutes} minutes"
            )

        return result

    def delete_ui_project_time(self, working_time: Dict[str, Any],
                               task_id: str) -> Dict[str, Any]:
        """
        Delete a UIProjectTime from a working time using incremental updates.

        Args:
            working_time (dict): The working time entry
            task_id (str): Task ID to delete

        Returns:
            dict: Updated consolidated data
        """
        # Get existing UI project times
        ui_project_times = self.get_ui_project_times(working_time)

        # Find the task to delete
        task_to_delete = next(
            (pt for pt in ui_project_times if pt.task_id == task_id), None)

        if task_to_delete:
            # Remove the task from the list
            remaining_tasks = [
                pt for pt in ui_project_times if pt.task_id != task_id
            ]

            # Use targeted deletion for this specific task
            logger.info(
                f"Incrementally deleting task {task_id}: {task_to_delete.duration_minutes}m"
            )
            self.apply_differential_updates(working_time, remaining_tasks)

        # Return updated consolidated data
        return self.consolidate_project_times(working_time)

    def replace_ui_project_times(
            self, working_time: Dict[str, Any],
            ui_project_times: List[UIProjectTime]) -> Dict[str, Any]:
        """
        Replace all UIProjectTimes for a working time.

        Args:
            working_time (dict): The working time entry
            ui_project_times (list): List of UIProjectTime objects

        Returns:
            dict: Updated consolidated data
        """
        # Use distribute_time to replace all project times
        self.distribute_time(work_time_entry=working_time,
                             ui_project_times=ui_project_times,
                             replace_all=True)

        # Return updated consolidated data
        return self.consolidate_project_times(working_time)



    def apply_differential_updates(self, working_time: Dict[str, Any],
                                   desired_tasks: List[UIProjectTime],
                                   source_working_time: Optional[Dict[str, Any]] = None):
        """
        Apply differential updates by comparing current vs desired state.
        Only makes the API calls necessary to achieve the desired state.

        Args:
            working_time (dict): The working time entry (target boundaries)
            desired_tasks (list): List of desired UIProjectTime objects
            source_working_time (dict, optional): Working time to get current project times from.
                                                 If None, uses working_time. Used when working time boundaries change.
        """
        # Get current project times from source working time (for boundary changes) or target working time (normal updates)
        source_time = source_working_time if source_working_time else working_time
        if source_working_time:
            logger.info(f"BOUNDARY_CHANGE_UPDATE: Getting current project times from OLD boundaries: {source_time.get('start')} to {source_time.get('end')}")
            logger.info(f"BOUNDARY_CHANGE_UPDATE: Applying to NEW boundaries: {working_time.get('start')} to {working_time.get('end')}")
        else:
            logger.info(f"DIFFERENTIAL_UPDATE: Working time boundaries: {working_time.get('start')} to {working_time.get('end')}")
        
        current_project_times = self.timr_api._get_project_times_in_work_time(source_time)
        logger.info(
            f"Current project times in Timr: {len(current_project_times)}")
        for pt in current_project_times:
            task_id = pt.get('task', {}).get('id', 'unknown')
            start = pt.get('start', 'unknown')
            end = pt.get('end', 'unknown')
            logger.info(f"  Current: Task {task_id} from {start} to {end}")

        # Merge multiple project times for the same task to avoid accidental
        # duplication when updating. We keep the first occurrence as the primary
        # project time and mark the rest for deletion.
        unique_project_times = []
        duplicate_project_times = []
        seen_tasks: Set[str] = set()
        for pt in current_project_times:
            task_id = pt.get('task', {}).get('id')
            if not task_id:
                continue
            if task_id in seen_tasks:
                duplicate_project_times.append(pt)
            else:
                seen_tasks.add(task_id)
                unique_project_times.append(pt)

        current_project_times = unique_project_times

        # Calculate desired time slots using existing logic
        desired_time_slots = self._calculate_time_slots(working_time, desired_tasks)
            
        logger.info(f"Desired time slots: {len(desired_time_slots)}")
        for slot in desired_time_slots:
            logger.info(
                f"  Desired: Task {slot['task_id']} from {slot['start']} to {slot['end']} ({slot['duration_minutes']}min)"
            )

        # Remove duplicate project times that were previously collected
        deleted = 0
        for dup in duplicate_project_times:
            logger.info(
                f"Deleting duplicate project time for task {dup.get('task', {}).get('id')} (ID: {dup.get('id')})")
            self.timr_api.delete_project_time(dup['id'])
            deleted += 1

        # Create lookup maps using the de-duplicated list
        current_by_task = {}
        for pt in current_project_times:
            task_id = pt.get('task', {}).get('id')
            if task_id:
                current_by_task[task_id] = pt

        desired_by_task = {}
        for slot in desired_time_slots:
            desired_by_task[slot['task_id']] = slot

        logger.info(f"Current tasks: {list(current_by_task.keys())}")
        logger.info(f"Desired tasks: {list(desired_by_task.keys())}")

        # Track changes for logging. `deleted` already contains the number of
        # duplicate project times removed above.
        created = 0
        updated = 0

        # 1. Delete tasks that exist currently but not in desired state
        tasks_to_delete = set(current_by_task.keys()) - set(
            desired_by_task.keys())
        logger.info(f"Tasks to delete: {tasks_to_delete}")
        for task_id in tasks_to_delete:
            logger.info(
                f"Deleting project time for task {task_id} (ID: {current_by_task[task_id]['id']})"
            )
            self.timr_api.delete_project_time(current_by_task[task_id]['id'])
            deleted += 1

        # 2. Create or update tasks that should exist in desired state
        for task_id, desired_slot in desired_by_task.items():
            if task_id in current_by_task:
                # Task exists - check if it needs updating
                current_pt = current_by_task[task_id]
                needs_update = self._project_time_needs_update(
                    current_pt, desired_slot)
                logger.info(
                    f"Task {task_id} exists, needs update: {needs_update}")
                if needs_update:
                    logger.info(
                        f"Updating project time for task {task_id} (ID: {current_pt['id']})"
                    )
                    logger.info(
                        f"  From: {current_pt.get('start')} to {current_pt.get('end')}"
                    )
                    logger.info(
                        f"  To: {desired_slot['start']} to {desired_slot['end']}"
                    )
                    self.timr_api.update_project_time(
                        project_time_id=current_pt['id'],
                        start=desired_slot['start'],
                        end=desired_slot['end'])
                    updated += 1
                else:
                    logger.info(
                        f"Task {task_id} already has correct times, no update needed"
                    )
            else:
                # Task doesn't exist - create it
                logger.info(f"Creating new project time for task {task_id}")
                logger.info(
                    f"  Times: {desired_slot['start']} to {desired_slot['end']}"
                )
                self.timr_api.create_project_time(task_id=task_id,
                                                  start=desired_slot['start'],
                                                  end=desired_slot['end'])
                created += 1

        logger.info(
            f"Differential update completed: {created} created, {updated} updated, {deleted} deleted"
        )

    def _calculate_time_slots(
            self, working_time: Dict[str, Any],
            tasks: List[UIProjectTime]) -> List[Dict[str, Any]]:
        """
        Calculate sequential time slots for all tasks within a working time.

        The consolidator sorts tasks by name (descending) and then assigns each
        task a slot starting at the end of the previous one. Durations are
        preserved exactly. If the working time is shorter than the summed
        durations the last slots may extend beyond the working time end which
        intentionally results in overlapping project times. These overlaps are
        surfaced to the user so they can decide whether to extend the working
        time or shorten some task durations.

        Args:
            working_time (dict): The working time entry
            tasks (list): List of UIProjectTime objects

        Returns:
            list: List of time slot dictionaries with start, end, task_id, and duration
        """
        # Parse working time boundaries
        start_str = working_time.get("start", "")
        end_str = working_time.get("end", "")
        if start_str.endswith('Z'):
            start_str = start_str.replace('Z', '+00:00')
        if end_str.endswith('Z'):
            end_str = end_str.replace('Z', '+00:00')

        work_start = datetime.fromisoformat(start_str)
        work_end = datetime.fromisoformat(end_str)
        
        current_time = work_start
        time_slots = []

        # Sort tasks by task name descending, then by task_id descending as fallback
        sorted_tasks = sorted(
            [t for t in tasks if not t.deleted and t.duration_minutes > 0],
            key=lambda x: (x.task_name or "", x.task_id), reverse=True)

        # Create sequential time slots with working time boundary enforcement
        for task in sorted_tasks:
            # Enforce that task starts no later than working time end minus one minute
            # (project times starting exactly at end time don't belong to working time)
            max_start_time = work_end - timedelta(minutes=1)
            task_start = min(current_time, max_start_time)
            
            # Task duration is preserved (as per requirements), even if it causes overlap
            task_end = task_start + timedelta(minutes=task.duration_minutes)

            time_slots.append({
                'task_id': task.task_id,
                'start': task_start,
                'end': task_end,
                'duration_minutes': task.duration_minutes
            })

            # Move to next position based on the calculated task end time
            current_time = task_end
            
            # Log warning if task extends beyond working time (this will create overlaps)
            if task_end > work_end:
                logger.warning(
                    f"Task {task.task_id} extends beyond working time end. "
                    f"Task ends at {task_end}, working time ends at {work_end}. "
                    f"This will create overlapping project times."
                )

        return time_slots

    def _project_time_needs_update(self, current_project_time: Dict[str, Any],
                                   desired_slot: Dict[str, Any]) -> bool:
        """
        Check if a project time needs to be updated by comparing current vs desired times.

        Args:
            current_project_time (dict): Current project time from Timr
            desired_slot (dict): Desired time slot

        Returns:
            bool: True if update is needed
        """
        try:
            # Parse current times
            current_start_str = current_project_time.get('start', '')
            current_end_str = current_project_time.get('end', '')

            # Normalize timezone format
            if current_start_str.endswith('Z'):
                current_start_str = current_start_str.replace('Z', '+00:00')
            if current_end_str.endswith('Z'):
                current_end_str = current_end_str.replace('Z', '+00:00')

            current_start = datetime.fromisoformat(current_start_str)
            current_end = datetime.fromisoformat(current_end_str)

            # Desired times are already datetime objects
            desired_start = desired_slot['start']
            desired_end = desired_slot['end']

            # Compare with small tolerance for rounding differences (1 second)
            start_diff = abs((current_start - desired_start).total_seconds())
            end_diff = abs((current_end - desired_end).total_seconds())

            needs_update = start_diff > 1 or end_diff > 1

            logger.info(
                f"    Time comparison for task {desired_slot['task_id']}:")
            logger.info(f"      Current: {current_start} to {current_end}")
            logger.info(f"      Desired: {desired_start} to {desired_end}")
            logger.info(
                f"      Start diff: {start_diff}s, End diff: {end_diff}s")
            logger.info(f"      Needs update: {needs_update}")

            return needs_update

        except (ValueError, TypeError, KeyError) as e:
            logger.warning(f"Error comparing project time: {e}")
            return True  # If we can't compare, assume update is needed

    def sanitize_work_times(
            self, work_times: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Sanitize work times to ensure they don't overlap.

        Args:
            work_times (list): List of working time entries

        Returns:
            list: Sanitized working time entries
        """
        if not work_times:
            return []

        # Sort work times by start time
        sorted_work_times = sorted(work_times,
                                   key=lambda wt: wt.get("start", ""))

        # Check for overlaps and adjust end times
        sanitized_work_times = [sorted_work_times[0]]

        for i in range(1, len(sorted_work_times)):
            prev_wt = sanitized_work_times[-1]
            curr_wt = sorted_work_times[i]

            # Handle different timezone formats
            prev_end_str = prev_wt.get("end", "")
            curr_start_str = curr_wt.get("start", "")

            if not prev_end_str or not curr_start_str:
                sanitized_work_times.append(curr_wt)
                continue

            # Normalize timezone format
            if prev_end_str.endswith('Z'):
                prev_end_str = prev_end_str.replace('Z', '+00:00')
            if curr_start_str.endswith('Z'):
                curr_start_str = curr_start_str.replace('Z', '+00:00')

            try:
                prev_end = datetime.fromisoformat(prev_end_str)
                curr_start = datetime.fromisoformat(curr_start_str)

                # If overlap, adjust the end time of the previous work time
                if curr_start < prev_end:
                    logger.warning(
                        f"Overlapping work times detected: {prev_wt.get('id')} and {curr_wt.get('id')}"
                    )

                    # Update the end time to match the start time of the current work time
                    prev_wt["end"] = curr_wt["start"]

                    # Log the adjustment
                    logger.info(
                        f"Adjusted end time of work time {prev_wt.get('id')} to {curr_wt.get('start')}"
                    )
            except (ValueError, TypeError) as e:
                logger.warning(f"Error parsing dates: {e}")

            sanitized_work_times.append(curr_wt)

        return sanitized_work_times

    def sanitize_project_times(
            self, working_time: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Sanitize project times to ensure they fall within working time bounds.

        Args:
            working_time (dict): The working time entry

        Returns:
            list: List of adjusted project time entries
        """
        if not working_time or "id" not in working_time:
            logger.warning(
                "Invalid working time provided to sanitize_project_times")
            return []

        # Parse working time bounds
        try:
            wt_start_str = working_time.get("start", "")
            wt_end_str = working_time.get("end", "")

            if not wt_start_str or not wt_end_str:
                logger.warning("Working time missing start or end time")
                return []

            # Normalize timezone format
            if wt_start_str.endswith('Z'):
                wt_start_str = wt_start_str.replace('Z', '+00:00')
            if wt_end_str.endswith('Z'):
                wt_end_str = wt_end_str.replace('Z', '+00:00')

            wt_start = datetime.fromisoformat(wt_start_str)
            wt_end = datetime.fromisoformat(wt_end_str)
        except (ValueError, TypeError) as e:
            logger.error(f"Error parsing working time dates: {e}")
            return []

        # Get project times for this working time
        project_times = self.timr_api._get_project_times_in_work_time(
            working_time)

        # Check each project time and adjust if needed
        adjusted_project_times = []

        for pt in project_times:
            try:
                pt_start_str = pt.get("start", "")
                pt_end_str = pt.get("end", "")
                pt_id = pt.get("id")

                if not pt_start_str or not pt_end_str or not pt_id:
                    continue

                # Normalize timezone format
                if pt_start_str.endswith('Z'):
                    pt_start_str = pt_start_str.replace('Z', '+00:00')
                if pt_end_str.endswith('Z'):
                    pt_end_str = pt_end_str.replace('Z', '+00:00')

                pt_start = datetime.fromisoformat(pt_start_str)
                pt_end = datetime.fromisoformat(pt_end_str)

                # Check if project time is out of bounds
                needs_adjustment = False

                # Project time starts before working time
                if pt_start < wt_start:
                    pt_start = wt_start
                    needs_adjustment = True
                    logger.info(
                        f"Project time {pt_id} starts before working time, adjusting to {wt_start}"
                    )

                # Project time durations must be preserved - do not truncate end times

                # If time order is wrong (start > end), fix it
                if pt_start > pt_end:
                    pt_end = pt_start + timedelta(
                        minutes=15)  # Default to 15 minutes
                    needs_adjustment = True
                    logger.warning(
                        f"Project time {pt_id} has start > end, setting duration to 15 minutes"
                    )

                # Update project time if needed
                if needs_adjustment:
                    updated_pt = self.timr_api.update_project_time(
                        project_time_id=pt_id, start=pt_start, end=pt_end)
                    adjusted_project_times.append(updated_pt)
                else:
                    adjusted_project_times.append(pt)
            except (ValueError, TypeError, TimrApiError) as e:
                logger.error(f"Error adjusting project time: {e}")

        return adjusted_project_times

    def consolidate_project_times(
            self, working_time: Dict[str, Any]) -> Dict[str, Any]:
        """
        Consolidate project times for a specific working time into UIProjectTime objects.

        Args:
            working_time (dict): The working time entry from the Timr API

        Returns:
            dict: A dictionary containing:
                - working_time: The original working time entry
                - ui_project_times: List of UIProjectTime objects consolidated by task ID
                - consolidated_project_times: List of dictionaries for compatibility
                - total_duration: Total duration of all project times in minutes
                - remaining_duration: Remaining unallocated time in minutes
                - is_fully_allocated: Whether all time is allocated
        """
        if not working_time:
            raise ValueError("Working time is required")

        logger.info(
            f"CONSOLIDATE: Starting consolidation for working time {working_time.get('id', 'unknown')}"
        )

        # Get the start and end times of the working time
        try:
            work_start = parse_iso_datetime(working_time.get("start"))
            work_end = parse_iso_datetime(working_time.get("end"))

            if not work_start:
                raise ValueError("Working time must have a start time")

            if not work_end:
                logger.warning(
                    "Working time missing end time; assuming ongoing recording"
                )
                work_end = datetime.now(
                    tz=work_start.tzinfo or datetime.timezone.utc)

            work_duration = int((work_end - work_start).total_seconds() / 60)
            logger.info(
                f"CONSOLIDATE: Working time duration: {work_duration} minutes")
        except (ValueError, TypeError) as e:
            raise ValueError(f"Invalid date format in working time entry: {e}")

        # Get break duration
        break_duration = working_time.get("break_time_total_minutes", 0)
        logger.info(f"CONSOLIDATE: Break duration: {break_duration} minutes")

        # Calculate net working time (total minus breaks)
        net_duration = work_duration - break_duration
        logger.info(
            f"CONSOLIDATE: Net working duration: {net_duration} minutes")

        # Get project times for this working time
        original_project_times = self.timr_api._get_project_times_in_work_time(
            working_time)

        # Ensure original_project_times is a list, even if it's empty
        if original_project_times is None:
            original_project_times = []

        logger.info(
            f"CONSOLIDATE: Found {len(original_project_times)} original project times from Timr"
        )

        # Consolidate project times by task into UIProjectTime objects
        ui_project_times = self._consolidate_by_task(original_project_times)
        logger.info(
            f"CONSOLIDATE: Consolidated into {len(ui_project_times)} UI project times"
        )

        # Calculate total allocated time
        total_allocated = sum(pt.duration_minutes for pt in ui_project_times)
        logger.info(
            f"CONSOLIDATE: Total allocated duration: {total_allocated} minutes"
        )

        # Calculate remaining time (can be negative for over-allocation)
        remaining_duration = net_duration - total_allocated
        logger.info(
            f"CONSOLIDATE: Remaining duration: {remaining_duration} minutes")

        # Determine allocation status with minimal tolerance for rounding errors
        tolerance = 0.5  # 30 second tolerance to avoid false positives from rounding
        is_over_allocated = total_allocated > (net_duration + tolerance)
        is_fully_allocated = (abs(net_duration - total_allocated) <= tolerance) and not is_over_allocated
        
        logger.info(f"CONSOLIDATE: Is fully allocated: {is_fully_allocated}")
        logger.info(f"CONSOLIDATE: Is over allocated: {is_over_allocated}")

        # Log final UI project times
        for i, pt in enumerate(ui_project_times):
            logger.info(
                f"CONSOLIDATE: Final UI project time {i}: {pt.task_id} = {pt.duration_minutes} minutes"
            )

        # Create result structure
        return {
            "working_time": working_time,
            "ui_project_times": ui_project_times,
            "consolidated_project_times":
            [pt.to_dict() for pt in ui_project_times],
            "total_duration": total_allocated,
            "net_duration": net_duration,
            "remaining_duration": remaining_duration,
            "is_fully_allocated": is_fully_allocated,
            "is_over_allocated": is_over_allocated
        }

    def _consolidate_by_task(
            self, project_times: List[Dict[str, Any]]) -> List[UIProjectTime]:
        """
        Consolidate project time entries by task ID into UIProjectTime objects.

        Args:
            project_times (list): List of project time entries from the Timr API

        Returns:
            list: List of UIProjectTime objects with consolidated information
        """
        # Ensure project_times is a list, even if it's empty
        if project_times is None:
            project_times = []

        logger.info(
            f"CONSOLIDATE_BY_TASK: Processing {len(project_times)} project times"
        )

        # Group by task ID
        task_entries = {}

        for pt in project_times:
            # Skip None entries and non-dict entries
            if not pt or not isinstance(pt, dict):
                continue
                
            task = pt.get("task", {})
            task_id = task.get("id")

            if not task_id:
                logger.warning(
                    f"CONSOLIDATE_BY_TASK: Project time missing task ID, skipping: {pt}"
                )
                continue

            # Get or create list for this task
            if task_id not in task_entries:
                task_entries[task_id] = []

            # Add this project time to the list for its task
            task_entries[task_id].append(pt)

        logger.info(
            f"CONSOLIDATE_BY_TASK: Grouped into {len(task_entries)} unique tasks"
        )

        # Create UIProjectTime objects for each task
        ui_project_times = []

        for task_id, entries in task_entries.items():
            if not entries:
                continue

            logger.info(
                f"CONSOLIDATE_BY_TASK: Processing task {task_id} with {len(entries)} entries"
            )

            # Use first entry to get task details
            first_entry = entries[0]
            task = first_entry.get("task", {})

            # Create UIProjectTime object for this task
            ui_project_time = UIProjectTime(
                task_id=task_id,
                task_name=task.get("name", ""),
                task_breadcrumbs=task.get("breadcrumbs", ""),
                duration_minutes=0  # Will be calculated from entries
            )

            # Calculate the total duration by summing durations from all entries
            total_duration = 0

            for entry in entries:
                try:
                    # First try to get duration from the API-provided duration field
                    if 'duration' in entry and entry[
                            'duration'] and 'minutes' in entry['duration']:
                        entry_duration = int(entry['duration']['minutes'])
                        logger.info(
                            f"CONSOLIDATE_BY_TASK: Task {task_id} entry has API duration: {entry_duration} minutes"
                        )
                    else:
                        # Otherwise, calculate it from the start and end times
                        start_str = entry.get("start", "")
                        end_str = entry.get("end", "")

                        if not start_str or not end_str:
                            logger.warning(
                                f"CONSOLIDATE_BY_TASK: Task {task_id} entry missing start/end times, skipping"
                            )
                            continue

                        # Handle different timezone formats in the API response
                        if start_str.endswith('Z'):
                            start_str = start_str.replace('Z', '+00:00')
                        if end_str.endswith('Z'):
                            end_str = end_str.replace('Z', '+00:00')

                        start = datetime.fromisoformat(start_str)
                        end = datetime.fromisoformat(end_str)
                        entry_duration = int(
                            (end - start).total_seconds() / 60)
                        logger.info(
                            f"CONSOLIDATE_BY_TASK: Task {task_id} entry calculated duration: {entry_duration} minutes"
                        )

                    # Add this entry's duration to the total
                    total_duration += entry_duration

                    # Link this project time to the UIProjectTime
                    ui_project_time.add_project_time(entry)

                except (ValueError, TypeError, KeyError) as e:
                    logger.warning(
                        f"CONSOLIDATE_BY_TASK: Error calculating duration for project time: {e}"
                    )

            # Set the calculated duration
            ui_project_time.duration_minutes = total_duration
            logger.info(
                f"CONSOLIDATE_BY_TASK: Task {task_id} final duration: {total_duration} minutes"
            )

            # Add the UIProjectTime to the result list if it has a positive duration
            if total_duration > 0:
                ui_project_times.append(ui_project_time)
            else:
                logger.warning(
                    f"CONSOLIDATE_BY_TASK: Task {task_id} has zero duration, skipping"
                )

        logger.info(
            f"CONSOLIDATE_BY_TASK: Created {len(ui_project_times)} UI project times"
        )
        return ui_project_times

    def distribute_time(self, work_time_entry: Dict[str, Any],
                        ui_project_times: List[UIProjectTime],
                        replace_all: bool = True,
                        source_working_time: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Distribute time among tasks within a working time using differential update.
        """
        # Use the existing differential update method
        self.apply_differential_updates(work_time_entry, ui_project_times, source_working_time)
        
        # Return current project times for compatibility
        return self.timr_api._get_project_times_in_work_time(work_time_entry)


