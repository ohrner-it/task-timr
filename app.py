"""
Task Timr - Task duration-focused alternative frontend to Timr.com
Main Flask application module

Copyright (c) 2025 Ohrner IT GmbH
Licensed under the MIT License
"""

import os
import logging
from datetime import datetime, timedelta, timezone
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from timr_api import TimrApi, TimrApiError
from timr_utils import ProjectTimeConsolidator, UIProjectTime
from config import COMPANY_ID, TIME_FORMAT, DATE_FORMAT, TASKLIST_TIMR_USER, TASKLIST_TIMR_PASSWORD, SESSION_SECRET

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
# Secret key is required for Flask sessions - used to cryptographically sign session cookies
# This secures user login tokens and session data stored in browser cookies
app.secret_key = SESSION_SECRET

# Initialize Timr API clients and ProjectTimeConsolidator
timr_api = TimrApi(company_id=COMPANY_ID)
timr_api_elevated = TimrApi(company_id=COMPANY_ID)
project_time_consolidator = ProjectTimeConsolidator(timr_api)

# Recent tasks cache
recent_tasks_cache = {}

# Utility functions for date and time handling
def parse_date(date_str):
    """
    Parse a date string into a datetime.date object.
    
    Args:
        date_str (str): Date string in ISO format or YYYY-MM-DD
        
    Returns:
        datetime.date: Parsed date or None if parsing failed
    """
    if not date_str:
        return None
        
    formats = [DATE_FORMAT, "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%SZ"]
    
    for fmt in formats:
        try:
            if fmt == DATE_FORMAT:
                return datetime.strptime(date_str, fmt).date()
            else:
                # Replace Z with +00:00 for ISO format compatibility
                if date_str.endswith('Z'):
                    date_str = date_str[:-1] + '+00:00'
                dt = datetime.strptime(date_str, fmt)
                return dt.date()
        except ValueError:
            continue
            
    return None

def parse_time(time_str):
    """
    Parse a time string into a datetime.time object.
    
    Args:
        time_str (str): Time string in ISO format or HH:MM
        
    Returns:
        datetime.time: Parsed time or None if parsing failed
    """
    if not time_str:
        return None
        
    formats = [TIME_FORMAT, "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%SZ"]
    
    for fmt in formats:
        try:
            if fmt == TIME_FORMAT:
                return datetime.strptime(time_str, fmt).time()
            else:
                # Replace Z with +00:00 for ISO format compatibility
                if time_str.endswith('Z'):
                    time_str = time_str[:-1] + '+00:00'
                dt = datetime.strptime(time_str, fmt)
                return dt.time()
        except ValueError:
            continue
            
    return None

def combine_datetime(date_obj, time_obj):
    """
    Combine date and time objects into a datetime object.
    
    Args:
        date_obj (datetime.date): Date object
        time_obj (datetime.time): Time object
        
    Returns:
        datetime.datetime: Combined datetime object
    """
    return datetime.combine(date_obj, time_obj)

def format_duration(minutes):
    """
    Format duration in minutes to hours and minutes.
    
    Args:
        minutes (int): Duration in minutes
        
    Returns:
        str: Formatted duration string (e.g., "2h 30m")
    """
    hours = minutes // 60
    remaining_mins = minutes % 60
    return f"{hours}h {remaining_mins}m"

# Function for getting project times (for testing)
def get_project_times():
    """API endpoint to get project times for a working time."""
    user = get_current_user()
    
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
        
    working_time_id = request.args.get('working_time_id')
    
    if not working_time_id:
        return jsonify({'error': 'Working time ID is required'}), 400
        
    # Set token in API client
    timr_api.token = session.get('token')
    timr_api.user = user
    
    try:
        # Get the working time
        working_time = timr_api.get_working_time(working_time_id)
        
        if not working_time:
            return jsonify({'error': 'Working time not found'}), 404
            
        # Use ProjectTimeConsolidator to consolidate project times
        consolidated_data = project_time_consolidator.consolidate_project_times(working_time)
        
        # Convert UI project times to dictionary format
        consolidated_project_times = []
        for ui_pt in consolidated_data['ui_project_times']:
            consolidated_project_times.append(ui_pt.to_dict())
            
        # Return the consolidated data
        return jsonify({
            'consolidated_project_times': consolidated_project_times,
            'total_duration': consolidated_data['total_duration'],
            'net_duration': consolidated_data['net_duration'],
            'remaining_duration': consolidated_data['remaining_duration'],
            'is_fully_allocated': consolidated_data['is_fully_allocated']
        })
    except TimrApiError as e:
        logger.error(f"Timr API Error in get_project_times: {e}")
        return jsonify({'error': str(e)}), 400


def get_current_user():
    """Get the current authenticated user."""
    if not session.get('token'):
        return None
    return session.get('user')


def format_date(date_obj):
    """Format date as YYYY-MM-DD."""
    if isinstance(date_obj, datetime):
        return date_obj.strftime(DATE_FORMAT)
    return date_obj


@app.route('/health')
def health_check():
    """Health check endpoint for Docker and systemd monitoring."""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'service': 'task-timr'
    })


@app.route('/')
def index():
    """Render the main page."""
    user = get_current_user()

    if user:
        # User is authenticated, show the main page
        current_date = datetime.now().date()
        date_str = current_date.strftime(DATE_FORMAT)

        return render_template('index.html',
                               user=user,
                               date=date_str,
                               company_id=COMPANY_ID)
    else:
        # User is not authenticated, show login form
        return render_template('index.html', user=None, company_id=COMPANY_ID)


@app.route('/login', methods=['POST'])
def login():
    """Handle login form submission."""
    username = request.form.get('username')
    password = request.form.get('password')

    if not username or not password:
        flash('Username and password are required', 'danger')
        return redirect(url_for('index'))

    try:
        # Attempt to log in
        response = timr_api.login(username, password)

        # Store token and user in session
        session['token'] = response.get('token')
        session['user'] = response.get('user')

        flash('Login successful', 'success')
        return redirect(url_for('index'))
    except TimrApiError as e:
        flash(f'Login failed: {e.message}', 'danger')
        return redirect(url_for('index'))


@app.route('/logout')
def logout():
    """Handle logout."""
    # Clear session
    session.clear()

    # Clear API client token
    timr_api.logout()

    flash('Logged out successfully', 'success')
    return redirect(url_for('index'))


@app.route('/api/working-times', methods=['GET'])
def get_working_times():
    """API endpoint to get working times for a date."""
    user = get_current_user()

    if not user:
        return jsonify({'error': 'Unauthorized'}), 401

    date_str = request.args.get('date')

    if not date_str:
        return jsonify({'error': 'Date parameter is required'}), 400

    try:
        # Parse date
        if len(date_str) == 10 and date_str[4] == '-' and date_str[7] == '-':
            date = datetime.strptime(date_str, DATE_FORMAT).date()
        else:
            return jsonify({'error':
                            f"Invalid date format: '{date_str}'"}), 400

        # Set token in API client
        timr_api.token = session.get('token')
        timr_api.user = user

        # Format the dates as ISO strings for the API
        start_date_iso = f"{date.strftime('%Y-%m-%d')}T00:00:00Z"
        end_date_iso = f"{date.strftime('%Y-%m-%d')}T23:59:59Z"
        
        # Get working times for the date with ISO formatted strings
        working_times = timr_api.get_working_times(start_date=start_date_iso,
                                                  end_date=end_date_iso,
                                                  user_id=user.get('id'))

        # Sanitize working times to fix any overlaps
        if working_times:
            working_times = project_time_consolidator.sanitize_work_times(
                working_times)

            # Sanitize project times for each working time
            for wt in working_times:
                project_time_consolidator.sanitize_project_times(wt)

        # Return working times to client
        return jsonify({'data': working_times})
    except Exception as e:
        logger.error(f"Error in get_working_times: {e}")
        return jsonify({'error': str(e)}), 400


@app.route('/api/working-times', methods=['POST'])
def create_working_time():
    """API endpoint to create a working time."""
    user = get_current_user()

    if not user:
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.json

    if not data:
        return jsonify({'error': 'No data provided'}), 400

    start = data.get('start')
    end = data.get('end')
    pause_duration = data.get('pause_duration', 0)
    working_time_type_id = data.get('working_time_type_id')

    if not start or not end:
        return jsonify({'error': 'Start and end times are required'}), 400

    # Set token in API client
    timr_api.token = session.get('token')
    timr_api.user = user

    try:
        # Check for overlapping working times
        date_str = start.split('T')[0] if 'T' in start else start
        existing_working_times = timr_api.get_working_times(
            start_date=date_str, end_date=date_str, user_id=user.get('id'))

        # Check if new working time would overlap with existing ones
        start_dt = datetime.fromisoformat(start.replace('Z', '+00:00'))
        end_dt = datetime.fromisoformat(end.replace('Z', '+00:00'))

        for wt in existing_working_times:
            wt_start = datetime.fromisoformat(wt['start'].replace(
                'Z', '+00:00'))
            if wt.get('end'):
                wt_end = datetime.fromisoformat(wt['end'].replace('Z', '+00:00'))
            else:
                # Treat running working times as continuing indefinitely
                wt_end = datetime.now(timezone.utc)

            # Check for overlap
            if (start_dt < wt_end and end_dt > wt_start):
                return jsonify({
                    'error':
                    'New working time would overlap with an existing working time'
                }), 400

        # Create working time - pass datetime objects directly, API client will format them
        working_time = timr_api.create_working_time(
            start=start, end=end, pause_duration=pause_duration, working_time_type_id=working_time_type_id)

        return jsonify({'working_time': working_time})
    except TimrApiError as e:
        logger.error(f"Timr API Error in create_working_time: {e}")
        return jsonify({'error': str(e)}), 400


@app.route('/api/working-times/<working_time_id>', methods=['PATCH'])
def update_working_time(working_time_id):
    """API endpoint to update a working time."""
    user = get_current_user()

    if not user:
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.json

    if not data:
        return jsonify({'error': 'No data provided'}), 400

    start = data.get('start')
    end = data.get('end')
    pause_duration = data.get('pause_duration')
    working_time_type_id = data.get('working_time_type_id')

    # Set token in API client
    timr_api.token = session.get('token')
    timr_api.user = user

    try:

        # Check for overlap with other working times (excluding this one)
        if start and end:
            date_str = start.split('T')[0] if 'T' in start else start
            existing_working_times = timr_api.get_working_times(
                start_date=date_str, end_date=date_str, user_id=user.get('id'))

            # Filter out this working time
            existing_working_times = [
                wt for wt in existing_working_times
                if wt.get('id') != working_time_id
            ]

            # Check for overlap
            start_dt = datetime.fromisoformat(start.replace('Z', '+00:00'))
            end_dt = datetime.fromisoformat(end.replace('Z', '+00:00'))

            for wt in existing_working_times:
                wt_start = datetime.fromisoformat(wt['start'].replace(
                    'Z', '+00:00'))
                wt_end = datetime.fromisoformat(wt['end'].replace(
                    'Z', '+00:00'))

                # Check for overlap
                if (start_dt < wt_end and end_dt > wt_start):
                    return jsonify({
                        'error':
                        'Updated working time would overlap with another working time'
                    }), 400

        # If start or end time changed, preserve task allocations
        ui_project_times = None
        current_working_time = None
        if start or end:
            current_working_time = timr_api.get_working_time(working_time_id)
            if not current_working_time:
                return jsonify({'error': 'Working time not found'}), 404
            ui_project_times = project_time_consolidator.get_ui_project_times(current_working_time)

        # Update working time
        working_time = timr_api.update_working_time(
            working_time_id=working_time_id,
            start=start,
            end=end,
            pause_duration=pause_duration,
            working_time_type_id=working_time_type_id)

        # Re-apply existing tasks using distribute_time method
        if ui_project_times:
            logger.info(f"Re-applying existing tasks to changed working time: {working_time['start']} to {working_time['end']}")
            # Use existing distribute_time method which already handles time slot calculation and overlaps
            # Pass the original working time to get project times from old boundaries
            project_time_consolidator.distribute_time(working_time, ui_project_times, replace_all=True, source_working_time=current_working_time)

        return jsonify({'working_time': working_time})
    except TimrApiError as e:
        logger.error(f"Timr API Error in update_working_time: {e}")
        return jsonify({'error': str(e)}), 400


@app.route('/api/working-times/<working_time_id>', methods=['DELETE'])
def delete_working_time(working_time_id):
    """API endpoint to delete a working time."""
    user = get_current_user()

    if not user:
        return jsonify({'error': 'Unauthorized'}), 401

    # Set token in API client
    timr_api.token = session.get('token')
    timr_api.user = user

    try:
        # Delete working time
        timr_api.delete_working_time(working_time_id)

        return jsonify({'success': True})
    except TimrApiError as e:
        logger.error(f"Timr API Error in delete_working_time: {e}")
        return jsonify({'error': str(e)}), 400


@app.route('/api/tasks/search', methods=['GET'])
def search_tasks():
    """API endpoint to search tasks."""
    user = get_current_user()

    if not user:
        return jsonify({'error': 'Unauthorized'}), 401

    # Get search term from query parameter
    search_term = request.args.get('q', '')

    if len(search_term) < 3:
        return jsonify({'tasks': []})

    # Use elevated API client for task operations (user authentication still required)
    # Authenticate elevated API client if not already authenticated
    if not timr_api_elevated.is_authenticated():
        if TASKLIST_TIMR_USER and TASKLIST_TIMR_PASSWORD:
            try:
                timr_api_elevated.login(TASKLIST_TIMR_USER, TASKLIST_TIMR_PASSWORD)
                logger.info("Task list user authenticated successfully for task search")
            except TimrApiError as e:
                logger.error(f"Task list user authentication failed: {e}")
                return jsonify({'tasks': [], 'error': 'Task search is currently unavailable. Please contact your administrator to configure the task list credentials.'})
        else:
            logger.error("Task list user credentials not configured")
            return jsonify({'tasks': [], 'error': 'Task search unavailable - task list user not configured'})
    
    try:
        # Search for tasks using elevated privileges
        tasks = timr_api_elevated.get_tasks(search=search_term, active_only=True)

        # Add search term to task name if not already in the name
        for task in tasks:
            if 'name' not in task and 'title' in task:
                task['name'] = task['title']

        # Sort tasks by name ascending, then by ID ascending as fallback
        sorted_tasks = sorted(tasks, key=lambda x: (x.get('name', ''), x.get('id', '')))

        return jsonify({'tasks': sorted_tasks})
    except Exception as e:
        logger.error(f"Error in search_tasks: {e}")
        return jsonify({'tasks': [], 'error': str(e)})


@app.route('/api/recent-tasks', methods=['GET'])
def get_recent_tasks():
    """API endpoint to get recent tasks."""
    user = get_current_user()

    if not user:
        return jsonify({'error': 'Unauthorized'}), 401

    user_id = user.get('id')

    # If cache is empty, populate it from recent project times
    if user_id not in recent_tasks_cache or not recent_tasks_cache[user_id]:
        # Set token in API client
        timr_api.token = session.get('token')
        timr_api.user = user
        
        try:
            # Get recent project times from the last 30 days
            from datetime import datetime, timedelta
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)
            
            project_times = timr_api.get_project_times(
                start_date=start_date,
                end_date=end_date,
                user_id=user_id
            )
            
            # Extract unique tasks and add to recent cache
            seen_tasks = set()
            for pt in project_times:
                task = pt.get('task', {})
                task_id = task.get('id')
                if task_id and task_id not in seen_tasks:
                    seen_tasks.add(task_id)
                    update_recent_tasks(user_id, {
                        'id': task_id,
                        'name': task.get('name', 'Unknown Task'),
                        'breadcrumbs': task.get('breadcrumbs', '')
                    })
                    
        except Exception as e:
            logger.warning(f"Could not populate recent tasks from project times: {e}")

    # Get recent tasks from cache
    tasks = recent_tasks_cache.get(user_id, [])

    return jsonify({'tasks': tasks})


@app.route('/api/working-time-types', methods=['GET'])
def get_working_time_types():
    """API endpoint to get working time types."""
    user = get_current_user()

    if not user:
        return jsonify({'error': 'Unauthorized'}), 401

    # Set token in API client
    timr_api.token = session.get('token')
    timr_api.user = user

    try:
        # Get all working time types and let backend handle the logic
        all_working_time_types = timr_api.get_working_time_types()
        
        # Separate attendance_time types (editable) from others (read-only)
        attendance_types = []
        other_types = []
        
        for wt_type in all_working_time_types:
            if wt_type.get('category') == 'attendance_time' and not wt_type.get('archived', False):
                attendance_types.append(wt_type)
            elif not wt_type.get('archived', False):
                other_types.append(wt_type)

        return jsonify({
            'attendance_types': attendance_types,
            'other_types': other_types
        })
    except Exception as e:
        logger.error(f"Error in get_working_time_types: {e}")
        return jsonify({'attendance_types': [], 'other_types': [], 'error': str(e)})


def update_recent_tasks(user_id, task):
    """Update the recent tasks cache for a user."""
    if user_id not in recent_tasks_cache:
        recent_tasks_cache[user_id] = []

    # Make a copy of the task to avoid reference issues
    task_copy = dict(task)

    # Check if task already exists in recent tasks
    existing_tasks = [
        t for t in recent_tasks_cache[user_id] if t.get('id') == task['id']
    ]
    if existing_tasks:
        # Remove existing entry
        recent_tasks_cache[user_id] = [
            t for t in recent_tasks_cache[user_id] if t.get('id') != task['id']
        ]

    # Add task to beginning of list
    recent_tasks_cache[user_id].insert(0, task_copy)

    # Limit to configured number of recent tasks
    from config import MAX_RECENT_TASKS
    recent_tasks_cache[user_id] = recent_tasks_cache[
        user_id][:MAX_RECENT_TASKS]


@app.route('/api/working-times/<working_time_id>/ui-project-times',
           methods=['GET'])
def get_ui_project_times(working_time_id):
    """Get UIProjectTime objects for a working time."""
    user = get_current_user()

    if not user:
        return jsonify({'error': 'Unauthorized'}), 401

    # Set token in API client
    timr_api.token = session.get('token')
    timr_api.user = user

    try:
        # Get the working time details
        working_time = timr_api.get_working_time(working_time_id)

        if not working_time:
            return jsonify({'error': 'Working time not found'}), 404

        # Use ProjectTimeConsolidator to get consolidated project times
        consolidated_data = project_time_consolidator.consolidate_project_times(
            working_time)

        # Convert UI project times to dictionary format
        ui_project_times_data = []
        for ui_pt in consolidated_data['ui_project_times']:
            ui_project_times_data.append(ui_pt.to_dict())

        # Return the data
        return jsonify({
            'ui_project_times':
            ui_project_times_data,
            'total_duration':
            consolidated_data['total_duration'],
            'net_duration':
            consolidated_data['net_duration'],
            'remaining_duration':
            consolidated_data['remaining_duration'],
            'is_fully_allocated':
            consolidated_data['is_fully_allocated'],
            'is_over_allocated':
            consolidated_data['is_over_allocated']
        })
    except Exception as e:
        logger.error(f"Error in get_ui_project_times: {e}")
        return jsonify({'error': str(e)}), 400


@app.route('/api/working-times/<working_time_id>/ui-project-times',
           methods=['POST'])
def add_ui_project_time(working_time_id):
    """Add a new UIProjectTime to a working time."""
    user = get_current_user()

    if not user:
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.json

    if not data:
        return jsonify({'error': 'No data provided'}), 400

    task_id = data.get('task_id')
    task_name = data.get('task_name')
    task_breadcrumbs = data.get('task_breadcrumbs', '')
    duration_minutes = data.get('duration_minutes', 0)

    if not task_id or not task_name:
        return jsonify({'error': 'task_id and task_name are required'}), 400

    if duration_minutes <= 0:
        return jsonify({'error': 'duration_minutes must be positive'}), 400

    # Set token in API client
    timr_api.token = session.get('token')
    timr_api.user = user

    try:
        # Get the working time details
        working_time = timr_api.get_working_time(working_time_id)

        if not working_time:
            return jsonify({'error': 'Working time not found'}), 404

        # Add to recent tasks
        update_recent_tasks(user.get('id'), {
            'id': task_id,
            'name': task_name,
            'breadcrumbs': task_breadcrumbs
        })

        # Check if adding this duration would exceed available time
        consolidated_data = project_time_consolidator.consolidate_project_times(
            working_time)

        remaining_duration = consolidated_data.get('remaining_duration', 0)
        existing_task = next(
            (t for t in consolidated_data.get('ui_project_times', [])
             if t.task_id == task_id), None)

        # If this is a new task and the duration exceeds remaining time
        if not existing_task and duration_minutes > remaining_duration:
            # If no time left at all, return error
            if remaining_duration <= 0:
                return jsonify({
                    'error':
                    f'No remaining time available in this working time'
                }), 400

            # Otherwise, adjust the duration to fit remaining time
            logger.warning(
                f"Requested duration {duration_minutes}m exceeds remaining time {remaining_duration}m. "
                f"Adjusting to fit.")
            duration_minutes = remaining_duration

        # Add UI project time
        result = project_time_consolidator.add_ui_project_time(
            working_time, task_id=task_id, task_name=task_name, duration_minutes=duration_minutes)

        # Convert UI project times to dictionary format
        ui_project_times_data = []
        for ui_pt in result['ui_project_times']:
            ui_project_times_data.append(ui_pt.to_dict())

        # Return the updated data
        return jsonify({
            'ui_project_times': ui_project_times_data,
            'total_duration': result['total_duration'],
            'net_duration': result['net_duration'],
            'remaining_duration': result['remaining_duration'],
            'is_fully_allocated': result['is_fully_allocated'],
            'is_over_allocated': result['is_over_allocated']
        })

    except (TimrApiError, ValueError) as e:
        logger.error(f"Error in add_ui_project_time: {e}", extra={
            'working_time_id': working_time_id,
            'task_id': task_id,
            'task_name': task_name,
            'duration_minutes': duration_minutes,
            'user_id': user.get('id') if user else None,
            'request_data': data,
            'error_type': type(e).__name__
        })
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Unexpected error in add_ui_project_time: {e}", extra={
            'working_time_id': working_time_id,
            'task_id': task_id,
            'task_name': task_name,
            'duration_minutes': duration_minutes,
            'user_id': user.get('id') if user else None,
            'request_data': data,
            'error_type': type(e).__name__
        })
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/working-times/<working_time_id>/ui-project-times/<task_id>',
           methods=['PATCH'])
def update_ui_project_time(working_time_id, task_id):
    """Update a UIProjectTime for a working time."""
    user = get_current_user()

    if not user:
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.json

    if not data:
        return jsonify({'error': 'No data provided'}), 400

    duration_minutes = data.get('duration_minutes')
    task_name = data.get('task_name')

    if duration_minutes is not None and duration_minutes <= 0:
        return jsonify({'error': 'duration_minutes must be positive'}), 400

    # Set token in API client
    timr_api.token = session.get('token')
    timr_api.user = user

    try:
        # Get the working time details
        working_time = timr_api.get_working_time(working_time_id)

        if not working_time:
            return jsonify({'error': 'Working time not found'}), 404

        # Check if updating this duration would exceed available time
        if duration_minutes is not None:
            consolidated_data = project_time_consolidator.consolidate_project_times(
                working_time)

            existing_task = next(
                (t for t in consolidated_data.get('ui_project_times', [])
                 if t.task_id == task_id), None)

            if existing_task:
                current_duration = existing_task.duration_minutes
                available_increase = consolidated_data.get(
                    'remaining_duration', 0) + current_duration

                # If the new duration exceeds what's available
                if duration_minutes > available_increase:
                    # Adjust the duration to fit available time
                    logger.warning(
                        f"Requested duration {duration_minutes}m exceeds available time {available_increase}m. "
                        f"Adjusting to fit.")
                    duration_minutes = available_increase

        # Update UI project time
        result = project_time_consolidator.update_ui_project_time(
            working_time, task_id=task_id, duration_minutes=duration_minutes, task_name=task_name)

        # Convert UI project times to dictionary format
        ui_project_times_data = []
        for ui_pt in result['ui_project_times']:
            ui_project_times_data.append(ui_pt.to_dict())

        # Return the updated data
        return jsonify({
            'ui_project_times': ui_project_times_data,
            'total_duration': result['total_duration'],
            'net_duration': result['net_duration'],
            'remaining_duration': result['remaining_duration'],
            'is_fully_allocated': result['is_fully_allocated'],
            'is_over_allocated': result['is_over_allocated']
        })

    except (TimrApiError, ValueError) as e:
        logger.error(f"Error in update_ui_project_time: {e}")
        return jsonify({'error': str(e)}), 400


@app.route('/api/working-times/<working_time_id>/ui-project-times/<task_id>',
           methods=['DELETE'])
def delete_ui_project_time(working_time_id, task_id):
    """Delete a UIProjectTime from a working time."""
    user = get_current_user()

    if not user:
        return jsonify({'error': 'Unauthorized'}), 401

    # Set token in API client
    timr_api.token = session.get('token')
    timr_api.user = user

    try:
        # Get the working time details
        working_time = timr_api.get_working_time(working_time_id)

        if not working_time:
            return jsonify({'error': 'Working time not found'}), 404

        # Delete UI project time
        result = project_time_consolidator.delete_ui_project_time(
            working_time, task_id=task_id)

        # Convert UI project times to dictionary format
        ui_project_times_data = []
        for ui_pt in result['ui_project_times']:
            ui_project_times_data.append(ui_pt.to_dict())

        # Return the updated data
        return jsonify({
            'ui_project_times': ui_project_times_data,
            'total_duration': result['total_duration'],
            'net_duration': result['net_duration'],
            'remaining_duration': result['remaining_duration'],
            'is_fully_allocated': result['is_fully_allocated'],
            'is_over_allocated': result['is_over_allocated']
        })

    except (TimrApiError, ValueError) as e:
        logger.error(f"Error in delete_ui_project_time: {e}")
        return jsonify({'error': str(e)}), 400


@app.route('/api/working-times/<working_time_id>/ui-project-times',
           methods=['PUT'])
def replace_ui_project_times(working_time_id):
    """Replace all UIProjectTimes for a working time."""
    user = get_current_user()

    if not user:
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.json

    if not data or 'ui_project_times' not in data:
        return jsonify({'error': 'ui_project_times is required'}), 400

    # Set token in API client
    timr_api.token = session.get('token')
    timr_api.user = user

    try:
        # Get the working time details
        working_time = timr_api.get_working_time(working_time_id)

        if not working_time:
            return jsonify({'error': 'Working time not found'}), 404

        # Check if the total duration would exceed available time
        total_requested_duration = sum(
            pt.get('duration_minutes', 0) for pt in data['ui_project_times'])

        # Get available time
        start_str = working_time.get("start", "").replace('Z', '+00:00')
        end_str = working_time.get("end")
        if end_str:
            end_str = end_str.replace('Z', '+00:00')
        break_duration = working_time.get("break_time_total_minutes", 0)

        try:
            work_start = datetime.fromisoformat(start_str)
            if end_str:
                work_end = datetime.fromisoformat(end_str)
            else:
                work_end = datetime.now(timezone.utc)
            available_minutes = int(
                (work_end - work_start).total_seconds() / 60) - break_duration

            # If total duration exceeds available time
            if total_requested_duration > available_minutes:
                return jsonify({
                    'error':
                    f'Total requested duration {total_requested_duration}m exceeds '
                    f'available time {available_minutes}m in this working time'
                }), 400
        except (ValueError, TypeError) as e:
            logger.error(f"Error calculating available time: {e}")

        # Convert dictionary data to UIProjectTime objects
        ui_project_times = []
        for ui_pt_data in data['ui_project_times']:
            ui_project_time = UIProjectTime.from_dict(ui_pt_data)
            ui_project_times.append(ui_project_time)

        # Replace UI project times
        result = project_time_consolidator.replace_ui_project_times(
            working_time, ui_project_times)

        # Convert UI project times to dictionary format
        ui_project_times_data = []
        for ui_pt in result['ui_project_times']:
            ui_project_times_data.append(ui_pt.to_dict())

        # Return the updated data
        return jsonify({
            'ui_project_times': ui_project_times_data,
            'total_duration': result['total_duration'],
            'net_duration': result['net_duration'],
            'remaining_duration': result['remaining_duration'],
            'is_fully_allocated': result['is_fully_allocated'],
            'is_over_allocated': result['is_over_allocated']
        })

    except (TimrApiError, ValueError) as e:
        logger.error(f"Error in replace_ui_project_times: {e}")
        return jsonify({'error': str(e)}), 400


@app.route('/api/validate-working-times', methods=['POST'])
def validate_working_times():
    """API endpoint to validate and sanitize working times."""
    user = get_current_user()

    if not user:
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.json

    if not data or 'working_times' not in data:
        return jsonify({'error': 'working_times is required'}), 400

    # Set token in API client
    timr_api.token = session.get('token')
    timr_api.user = user

    try:
        # Sanitize working times
        sanitized_working_times = project_time_consolidator.sanitize_work_times(
            data['working_times'])

        return jsonify({'working_times': sanitized_working_times})
    except Exception as e:
        logger.error(f"Error in validate_working_times: {e}")
        return jsonify({'error': str(e)}), 400


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
