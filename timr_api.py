import requests
import json
import datetime
import pytz
import logging
from config import API_BASE_URL, COMPANY_ID
from datetime import timedelta
from error_handler import timr_api_error_handler, ErrorCategory, ErrorSeverity, ErrorContext

logger = logging.getLogger(__name__)


def _calculate_ongoing_working_time_end_for_api(working_time, work_start):
    """
    Calculate effective end time for ongoing working times (for API use).
    
    Args:
        working_time: Working time dictionary with duration info
        work_start: Parsed start datetime of the working time
        
    Returns:
        datetime: Calculated end time
    """
    duration_info = working_time.get("duration", {})
    if duration_info and "minutes" in duration_info:
        return work_start + timedelta(minutes=duration_info["minutes"])
    else:
        # Fallback: use current time as the working end
        return datetime.datetime.now(pytz.UTC)


class TimrApiError(Exception):
    """Exception raised for errors with the Timr API."""

    def __init__(self, message, status_code=None, response=None):
        self.message = message
        self.status_code = status_code
        self.response = response
        self.technical_message = message  # Will be overridden if different
        super().__init__(self.message)
    
    def get_user_message(self):
        """Get the user-friendly error message."""
        return self.message
    
    def get_technical_message(self):
        """Get the technical error message for debugging."""
        return getattr(self, 'technical_message', self.message)


class TimrApi:
    """
    Python client for Timr.com API.

    This client provides methods to interact with the Timr.com API for authentication,
    working times, project times, and tasks. All list-based API endpoints automatically
    handle pagination transparently, so calling methods like get_tasks() will retrieve
    all available data regardless of API pagination limits.

    Key Features:
    - Automatic pagination handling for all list endpoints
    - Transparent data retrieval without manual pagination logic
    - Configurable page sizes and limits for performance optimization
    - Comprehensive error handling and logging
    """

    def __init__(self, company_id=COMPANY_ID):
        """
        Initialize the TimrApi client.

        Args:
            company_id (str): The company ID for Timr.com. Defaults to value from config.
        """
        self.company_id = company_id
        self.base_url = API_BASE_URL
        self.token = None
        self.token_expiry = None
        self.user = None
        self.session = requests.Session()
        # Cache for parent task data during a single get_tasks operation
        self._parent_task_cache = {}

    def _request(self, method, endpoint, data=None, params=None, headers=None):
        """
        Make a request to the Timr API.

        Args:
            method (str): HTTP method (GET, POST, PATCH, DELETE)
            endpoint (str): API endpoint
            data (dict, optional): Request data
            params (dict, optional): Query parameters
            headers (dict, optional): HTTP headers

        Returns:
            dict: Response data

        Raises:
            TimrApiError: If the request fails
        """
        url = f"{self.base_url}{endpoint}"

        if headers is None:
            headers = {}

        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"

        headers["Content-Type"] = "application/json"

        try:
            logger.debug(f"API Request: {method} {url}")
            logger.debug(f"Params: {params}")
            if data:
                # Log sanitized data (no sensitive info)
                sanitized_data = timr_api_error_handler._sanitize_request_data(data)
                logger.debug(f"Data: {json.dumps(sanitized_data)}")

            response = self.session.request(
                method=method,
                url=url,
                data=json.dumps(data) if data else None,
                params=params,
                headers=headers)

            logger.debug(f"Response status: {response.status_code}")

            # Check if the request was successful
            response.raise_for_status()

            # If no content, return empty dict
            if response.status_code == 204:
                return {}

            return response.json()
        except requests.exceptions.HTTPError as e:
            status_code = e.response.status_code
            response_data = None
            error_msg = f"API request failed with status code {status_code}"

            # Extract detailed error information from response
            try:
                if e.response.headers.get('Content-Type', '').startswith('application/json'):
                    response_data = e.response.json()
                    if isinstance(response_data, dict):
                        # Use API-provided error message if available
                        if "message" in response_data:
                            error_msg = response_data["message"]
                        elif "error" in response_data:
                            error_msg = response_data["error"]
                        elif "detail" in response_data:
                            error_msg = response_data["detail"]
                else:
                    response_data = e.response.text[:500]  # Limit text response length
            except Exception:
                response_data = e.response.text[:500] if hasattr(e.response, 'text') else None

            # Enhanced logging with complete request context for errors
            # Create an exception with the meaningful error message
            meaningful_error = Exception(error_msg)
            
            # Enhanced request data that includes method, URL, params for complete debugging context
            enhanced_request_data = {
                "method": method,
                "url": url,
                "params": params,
                "payload": data
            }
            
            user_message = timr_api_error_handler.log_api_error(
                error=meaningful_error,
                endpoint=endpoint,
                status_code=status_code,
                response=response_data,
                request_data=enhanced_request_data,
                user_id=getattr(self.user, 'id', None) if self.user else None,
                operation=f"{method} {endpoint}"
            )
            
            # Create enhanced TimrApiError with user-friendly message
            api_error = TimrApiError(user_message, status_code, response_data)
            api_error.technical_message = error_msg  # Keep technical message for debugging
            raise api_error from e
            
        except requests.exceptions.ConnectionError as e:
            # Enhanced request data for network errors
            enhanced_request_data = {
                "method": method,
                "url": url,
                "params": params,
                "payload": data
            }
            
            user_message = timr_api_error_handler.log_error(
                error=e,
                context=ErrorContext(
                    category=ErrorCategory.NETWORK,
                    severity=ErrorSeverity.MEDIUM,
                    operation=f"{method} {endpoint}",
                    user_id=getattr(self.user, 'id', None) if self.user else None,
                    api_endpoint=endpoint,
                    request_data=enhanced_request_data
                )
            )
            raise TimrApiError(user_message) from e
            
        except requests.exceptions.Timeout as e:
            # Create a timeout-specific error message
            timeout_error = Exception(f"Request timed out: {str(e)}")
            
            # Enhanced request data for timeout errors
            enhanced_request_data = {
                "method": method,
                "url": url,
                "params": params,
                "payload": data
            }
            
            user_message = timr_api_error_handler.log_error(
                error=timeout_error,
                context=ErrorContext(
                    category=ErrorCategory.NETWORK,
                    severity=ErrorSeverity.MEDIUM,
                    operation=f"{method} {endpoint} (timeout)",
                    user_id=getattr(self.user, 'id', None) if self.user else None,
                    api_endpoint=endpoint,
                    request_data=enhanced_request_data
                )
            )
            raise TimrApiError(user_message) from e
            
        except requests.exceptions.RequestException as e:
            # Enhanced request data for general request exceptions
            enhanced_request_data = {
                "method": method,
                "url": url,
                "params": params,
                "payload": data
            }
            
            user_message = timr_api_error_handler.log_error(
                error=e,
                context=ErrorContext(
                    category=ErrorCategory.NETWORK,
                    severity=ErrorSeverity.HIGH,
                    operation=f"{method} {endpoint}",
                    user_id=getattr(self.user, 'id', None) if self.user else None,
                    api_endpoint=endpoint,
                    request_data=enhanced_request_data
                )
            )
            raise TimrApiError(user_message) from e

    def _request_paginated(self, endpoint, params=None, limit=500, max_pages=None):
        """
        Make a paginated request to the Timr API using cursor pagination and collect all data.
        
        This method automatically handles Timr's cursor pagination by making multiple requests
        using page_token and limit parameters as specified in the API documentation.
        
        Args:
            endpoint (str): API endpoint to request
            params (dict, optional): Query parameters (pagination params will be added)
            limit (int, optional): Number of items per page (default: 500, max allowed by API)
            max_pages (int, optional): Maximum number of pages to fetch (default: unlimited)
            
        Returns:
            list: All items from all pages combined
            
        Raises:
            TimrApiError: If any request fails
        """
        if params is None:
            params = {}
        
        # Make a copy to avoid modifying the original params
        request_params = params.copy()
        
        all_items = []
        page_count = 0
        next_page_token = None
        
        logger.debug(f"Starting cursor paginated request to {endpoint} with limit={limit}")
        
        while True:
            page_count += 1
            
            # Add pagination parameters according to Timr API spec
            request_params["limit"] = limit
            if next_page_token:
                request_params["page_token"] = next_page_token
            else:
                # Remove page_token if it exists from previous iterations
                request_params.pop("page_token", None)
            
            logger.debug(f"Fetching page {page_count} for {endpoint} (page_token: {'Yes' if next_page_token else 'None'})")
            
            # Make the request for this page
            response = self._request("GET", endpoint, params=request_params)
            
            # Extract data from the response
            if "data" not in response:
                logger.warning(f"No 'data' field in response for {endpoint} page {page_count}")
                break
                
            items = response["data"]
            
            # If no items returned, we've reached the end
            if not items:
                logger.debug(f"No items returned for {endpoint} page {page_count}, ending pagination")
                break
            
            all_items.extend(items)
            logger.debug(f"Added {len(items)} items from page {page_count}, total so far: {len(all_items)}")
            
            # Check for next page token according to Timr API spec
            next_page_token = response.get("next_page_token")
            if not next_page_token:
                logger.debug(f"No next_page_token in response, this is the last page")
                break
            
            # Check max_pages limit
            if max_pages is not None and page_count >= max_pages:
                logger.debug(f"Reached maximum page limit of {max_pages}")
                break
        
        logger.debug(f"Completed cursor paginated request to {endpoint}: {len(all_items)} total items from {page_count} pages")
        return all_items

    def login(self, username, password):
        """
        Authenticate with the Timr API.

        Args:
            username (str): Username/email for Timr.com
            password (str): Password for Timr.com

        Returns:
            dict: Authentication response with token and user info

        Raises:
            TimrApiError: If authentication fails
        """
        data = {
            "identifier": self.company_id,
            "login": username,
            "password": password
        }

        response = self._request("POST", "/login", data=data)

        if response and "token" in response:
            self.token = response["token"]
            self.user = response.get("user", {})
            
            # Store token expiry if provided
            if "valid_until" in response and response["valid_until"]:
                try:
                    # Parse the expiry datetime string
                    expiry_str = response["valid_until"]
                    # Handle ISO format with timezone offset
                    self.token_expiry = datetime.datetime.fromisoformat(expiry_str.replace('Z', '+00:00'))
                    logger.info(f"Token expires at: {self.token_expiry}")
                except (ValueError, TypeError, AttributeError) as e:
                    logger.warning(f"Could not parse token expiry '{response.get('valid_until')}': {e}")
                    self.token_expiry = None
            else:
                self.token_expiry = None
                
            return response
        else:
            raise TimrApiError("Authentication failed, no token received")

    def logout(self):
        """Clear authentication token and user info."""
        self.token = None
        self.token_expiry = None
        self.user = None

    def is_authenticated(self):
        """Check if the client is authenticated and token is still valid."""
        if self.token is None:
            return False
            
        # If we have a token expiry, check if it's still valid
        if self.token_expiry is not None:
            current_time = datetime.datetime.now(pytz.UTC)
            
            if current_time >= self.token_expiry:
                logger.info(f"Token expired at {self.token_expiry}, current time is {current_time}")
                # Clear expired token
                self.token = None
                self.token_expiry = None
                self.user = None
                return False
                
        return True

    def _format_date_for_query(self, dt):
        """Format a date for query parameters (YYYY-MM-DD)."""
        if isinstance(dt, str):
            # If it's already in YYYY-MM-DD format, use it
            if len(dt) == 10 and dt[4] == '-' and dt[7] == '-':
                return dt
            # If it has time component, extract the date part
            if 'T' in dt:
                return dt.split('T')[0]
            # Otherwise, return as is
            return dt

        # Handle datetime objects by converting to YYYY-MM-DD
        if isinstance(dt, datetime.datetime):
            return dt.date().isoformat()
        elif isinstance(dt, datetime.date):
            return dt.isoformat()

        # If we can't handle it, return as is
        return str(dt)

    def _format_datetime_iso8601(self, dt):
        """Format a datetime in ISO 8601 format with timezone offset as required by Timr API."""
        if isinstance(dt, str):
            # If string already has timezone info, use as is
            if '+' in dt or (dt.endswith('Z') and 'T' in dt):
                # Replace Z with +00:00 to ensure consistent timezone offset format
                if dt.endswith('Z'):
                    return dt.replace('Z', '+00:00')
                return dt

            # If it's a date only string, add time and timezone
            if len(dt) == 10 and dt[4] == '-' and dt[7] == '-':
                return f"{dt}T00:00:00+00:00"

            # If it has time component without timezone, add timezone
            if 'T' in dt and not ('+' in dt or dt.endswith('Z')):
                return f"{dt}+00:00"

            # Otherwise return as is
            return dt

        # Handle datetime objects
        if isinstance(dt, datetime.datetime):
            # Ensure timezone info is present
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=pytz.UTC)

            # Format to ISO 8601 with timezone offset
            iso_format = dt.isoformat()

            # Replace Z suffix with +00:00 if needed
            if iso_format.endswith('Z'):
                return iso_format.replace('Z', '+00:00')

            return iso_format

        # If it's a date object, convert to datetime at start of day
        if isinstance(dt, datetime.date):
            dt = datetime.datetime.combine(dt,
                                           datetime.time.min,
                                           tzinfo=pytz.UTC)
            return dt.isoformat()

        # If we can't handle it, convert to string
        return str(dt)

    def get_working_times(self, start_date=None, end_date=None, user_id=None):
        """
        Get working times for a specific date range.

        Args:
            start_date (datetime, date or str): Start date for query
            end_date (datetime, date or str): End date for query
            user_id (str, optional): User ID to filter by

        Returns:
            list: Working time entries
        """
        params = {}

        if start_date:
            params["start_from"] = self._format_date_for_query(start_date)

        if end_date:
            params["start_to"] = self._format_date_for_query(end_date)

        if user_id:
            params["user"] = user_id
        elif self.user and "id" in self.user:
            params["user"] = self.user["id"]

        # Use centralized pagination handling
        return self._request_paginated("/working-times", params=params)

    def create_working_time(
            self,
            start,
            end,
            status="changeable",
            pause_duration=0,
            working_time_type_id=None):
        """
        Create a new working time entry.

        Args:
            start (datetime or str): Start time
            end (datetime or str): End time
            status (str, optional): Status of the entry
            pause_duration (int, optional): Pause duration in minutes
            working_time_type_id (str, optional): Type ID for working time

        Returns:
            dict: Created working time entry
        """
        data = {
            "start": self._format_datetime_iso8601(start),
            "end": self._format_datetime_iso8601(end),
            "status": status,
            "changed": True
        }

        # Only add working_time_type_id if provided
        if working_time_type_id:
            data["working_time_type_id"] = working_time_type_id
        else:
            # Use default attendance time working type
            data["working_time_type_id"] = "3f1953ee-f5d6-471f-a4ed-95ced921dd86"

        if pause_duration > 0:
            # Use break_times array format from the API documentation
            data["break_times"] = [{
                "type":
                "manual",
                "start":
                self._format_datetime_iso8601(start),
                "duration_minutes":
                pause_duration
            }]

        if self.user and "id" in self.user:
            data["user_id"] = self.user["id"]

        return self._request("POST", "/working-times", data=data)

    def get_working_time(self, working_time_id):
        """
        Get a specific working time entry.

        Args:
            working_time_id (str): Working time ID

        Returns:
            dict: Working time entry
        """
        return self._request("GET", f"/working-times/{working_time_id}")

    def update_working_time(self,
                            working_time_id,
                            start=None,
                            end=None,
                            status=None,
                            pause_duration=None,
                            working_time_type_id=None):
        """
        Update a working time entry.

        Args:
            working_time_id (str): Working time ID
            start (datetime or str, optional): New start time
            end (datetime or str, optional): New end time
            status (str, optional): New status
            pause_duration (int, optional): New pause duration in minutes
            working_time_type_id (str, optional): New working time type ID

        Returns:
            dict: Updated working time entry
        """
        logger.info(
            f"Updating working time {working_time_id}: start={start}, end={end}, status={status}, pause_duration={pause_duration}"
        )

        data = {"changed": True}

        if start:
            data["start"] = self._format_datetime_iso8601(start)

        if end:
            data["end"] = self._format_datetime_iso8601(end)

        if status:
            data["status"] = status

        if working_time_type_id:
            data["working_time_type_id"] = working_time_type_id

        if pause_duration is not None:
            logger.info(f"Setting pause duration to {pause_duration} minutes")
            
            # Based on the working Java pattern, create break_times with just type and duration
            # The API will handle the timing automatically
            if pause_duration == 0:
                data["break_times"] = []
            else:
                data["break_times"] = [{
                    "type": "manual",
                    "duration_minutes": pause_duration
                }]

            logger.info(f"Break times data: {data['break_times']}")

        logger.info(f"Sending update request with data: {data}")

        try:
            result = self._request("PATCH",
                                   f"/working-times/{working_time_id}",
                                   data=data)
            logger.info(f"Update successful. Response: {result}")
            return result
        except Exception as e:
            logger.error(f"Update failed with error: {e}")
            raise

    def delete_working_time(self, working_time_id):
        """
        Delete a working time entry.

        Args:
            working_time_id (str): Working time ID

        Returns:
            dict: Empty response or error
        """
        return self._request("DELETE", f"/working-times/{working_time_id}")

    def get_tasks(self, search=None, active_only=True):
        """
        Get available tasks.

        Args:
            search (str, optional): Search term for filtering tasks
            active_only (bool, optional): If True, only return active tasks

        Returns:
            list: Task entries
        """
        params = {}

        if search and len(search) >= 3:
            params["name"] = search

        # Use centralized pagination handling with correct cursor pagination
        all_tasks = self._request_paginated("/tasks", params=params, limit=500)

        # Filter active tasks if requested
        if active_only:
            # Clear parent task cache for this get_tasks operation
            self._parent_task_cache = {}
            active_tasks = []

            for task in all_tasks:
                # Use the new comprehensive filtering that checks parent tasks too
                if self._is_task_effectively_bookable(task):
                    active_tasks.append(task)

            # Clear cache after filtering is complete
            self._parent_task_cache = {}
            return active_tasks

        return all_tasks

    def _get_task_by_id(self, task_id):
        """
        Get a specific task by its ID, with caching support.
        
        Args:
            task_id (str): Task ID to fetch
            
        Returns:
            dict: Task data
            
        Raises:
            TimrApiError: If the task cannot be fetched
        """
        # Check cache first
        if task_id in self._parent_task_cache:
            return self._parent_task_cache[task_id]
        
        # Fetch from API and cache the result
        try:
            task_data = self._request("GET", f"/tasks/{task_id}")
            self._parent_task_cache[task_id] = task_data
            return task_data
        except TimrApiError:
            # Don't cache API errors - always retry failed requests
            raise

    def _is_task_effectively_bookable(self, task):
        """
        Check if a task is effectively bookable by verifying that both the task
        and all its parent tasks are not closed (don't have past end_dates).
        
        Args:
            task (dict): Task data to check
            
        Returns:
            bool: True if task is effectively bookable, False otherwise
        """
        now = datetime.datetime.now(pytz.UTC)
        
        # Check the task itself first
        if not self._is_task_active(task, now):
            return False
            
        # Check parent tasks recursively
        current_task = task
        while current_task and current_task.get('parent_task'):
            parent_info = current_task.get('parent_task')
            parent_id = parent_info.get('id')
            
            if not parent_id:
                break
                
            try:
                parent_task = self._get_task_by_id(parent_id)
                if not self._is_task_active(parent_task, now):
                    return False
                current_task = parent_task
            except TimrApiError as e:
                # If we can't fetch the parent task, assume it's active
                # to avoid blocking tasks due to temporary API issues
                break
                
        return True
        
    def _is_task_active(self, task, now):
        """
        Check if a single task is active (not past its end_date).
        
        Args:
            task (dict): Task data to check
            now (datetime): Current time for comparison
            
        Returns:
            bool: True if task is active, False if closed
        """
        if "end_date" not in task or not task["end_date"]:
            return True
            
        try:
            end_date_str = task["end_date"]
            if isinstance(end_date_str, str):
                # Handle timezone if present
                if 'Z' in end_date_str:
                    task_end_date = datetime.datetime.fromisoformat(
                        end_date_str.replace('Z', '+00:00'))
                elif '+' in end_date_str or '-' in end_date_str[10:]:
                    # Already has timezone info
                    task_end_date = datetime.datetime.fromisoformat(end_date_str)
                else:
                    # No timezone info, assume UTC
                    task_end_date = datetime.datetime.fromisoformat(end_date_str)
                    task_end_date = task_end_date.replace(tzinfo=pytz.UTC)
                    
                # Check if end date is in the future
                return task_end_date > now
        except (ValueError, TypeError):
            # If we can't parse the date, assume task is active
            pass
            
        return True

    def get_project_times(self,
                          start_date=None,
                          end_date=None,
                          user_id=None,
                          task_id=None):
        """
        Get project time entries.

        Args:
            start_date (datetime, date or str, optional): Start date for query
            end_date (datetime, date or str, optional): End date for query
            user_id (str, optional): User ID to filter by
            task_id (str, optional): Task ID to filter by

        Returns:
            list: Project time entries
        """
        params = {}

        if start_date:
            params["start_from"] = self._format_date_for_query(start_date)

        if end_date:
            params["start_to"] = self._format_date_for_query(end_date)

        if user_id:
            params["user"] = user_id
        elif self.user and "id" in self.user:
            params["user"] = self.user["id"]

        if task_id:
            params["task"] = task_id

        # Use centralized pagination handling
        return self._request_paginated("/project-times", params=params)

    def create_project_time(self, task_id, start, end, status="changeable"):
        """
        Create a new project time entry.

        Args:
            task_id (str): Task ID
            start (datetime or str): Start time
            end (datetime or str): End time
            status (str, optional): Status of the entry

        Returns:
            dict: Created project time entry

        Raises:
            TimrApiError: If creation fails due to API issues
            ValueError: If required parameters are missing or invalid
        """
        # Validate required fields
        if not task_id:
            raise ValueError("Task ID is required for creating a project time")

        if not start or not end:
            raise ValueError(
                "Start and end times are required for creating a project time")

        # Format data for API request
        data = {
            "start": self._format_datetime_iso8601(start),
            "end": self._format_datetime_iso8601(end),
            "status": status,
            "task_id": task_id,
            "changed": True
        }

        # Add user ID if available
        if self.user and "id" in self.user:
            data["user_id"] = self.user["id"]

        try:
            return self._request("POST", "/project-times", data=data)
        except TimrApiError as e:
            # Enhanced business rule detection and user messaging
            error_msg = str(e).lower()
            technical_msg = getattr(e, 'technical_message', str(e))
            
            # Detect specific business rule violations
            if "not bookable" in error_msg or "task is not bookable" in error_msg:
                user_msg = timr_api_error_handler.log_business_rule_violation(
                    rule_type="non_bookable_task",
                    details=f"Task {task_id} is not bookable",
                    user_id=getattr(self.user, 'id', None) if self.user else None,
                    task_id=task_id
                )
                enhanced_error = TimrApiError(user_msg, e.status_code, e.response)
                enhanced_error.technical_message = technical_msg
                raise enhanced_error from e
            elif "frozen" in error_msg or "locked" in error_msg:
                user_msg = timr_api_error_handler.log_business_rule_violation(
                    rule_type="frozen_time",
                    details="Working time is frozen and cannot be modified",
                    user_id=getattr(self.user, 'id', None) if self.user else None
                )
                enhanced_error = TimrApiError(user_msg, e.status_code, e.response)
                enhanced_error.technical_message = technical_msg
                raise enhanced_error from e
            elif "overlap" in error_msg:
                user_msg = timr_api_error_handler.log_business_rule_violation(
                    rule_type="overlapping_times",
                    details="Time entry overlaps with existing entries",
                    user_id=getattr(self.user, 'id', None) if self.user else None,
                    task_id=task_id
                )
                enhanced_error = TimrApiError(user_msg, e.status_code, e.response)
                enhanced_error.technical_message = technical_msg
                raise enhanced_error from e
            
            # Re-raise with original error if no specific rule detected
            raise

    def get_project_time(self, project_time_id):
        """
        Get a specific project time entry.

        Args:
            project_time_id (str): Project time ID

        Returns:
            dict: Project time entry
        """
        return self._request("GET", f"/project-times/{project_time_id}")

    def update_project_time(self,
                            project_time_id,
                            task_id=None,
                            start=None,
                            end=None,
                            status=None):
        """
        Update a project time entry.

        Args:
            project_time_id (str): Project time ID
            task_id (str, optional): New task ID
            start (datetime or str, optional): New start time
            end (datetime or str, optional): New end time
            status (str, optional): New status

        Returns:
            dict: Updated project time entry
        """
        data = {"changed": True}

        if task_id:
            data["task_id"] = task_id

        if start:
            data["start"] = self._format_datetime_iso8601(start)

        if end:
            data["end"] = self._format_datetime_iso8601(end)

        if status:
            data["status"] = status

        return self._request("PATCH",
                             f"/project-times/{project_time_id}",
                             data=data)

    def delete_project_time(self, project_time_id):
        """
        Delete a project time entry.

        Args:
            project_time_id (str): Project time ID

        Returns:
            dict: Empty response or error
        """
        return self._request("DELETE", f"/project-times/{project_time_id}")

    def _get_project_times_in_work_time(self, work_time_entry):
        """
        Get all project times within a given working time.

        Args:
            work_time_entry (dict): Working time entry

        Returns:
            list: Project times within the working time
        """
        try:
            # Parse the start time
            work_start = datetime.datetime.fromisoformat(
                work_time_entry["start"].replace("Z", "+00:00"))
            
            # Handle ongoing working times (null end time)
            work_end_str = work_time_entry.get("end")
            if work_end_str is None:
                # For ongoing working times, use calculated end time
                work_end = _calculate_ongoing_working_time_end_for_api(work_time_entry, work_start)
                logger.info(f"Using calculated end time for ongoing working time: {work_end}")
            else:
                # Standard working time with end time
                work_end = datetime.datetime.fromisoformat(
                    work_end_str.replace("Z", "+00:00"))

            # Format dates for API query
            start_date = work_start.date()
            end_date = work_end.date()

            # Get all project times for this date range
            project_times = self.get_project_times(
                start_date=start_date,
                end_date=end_date,
                user_id=self.user.get("id") if self.user else None)

            # Filter to only those within this working time
            project_times_in_working_time = []
            for pt in project_times:
                try:
                    pt_start = datetime.datetime.fromisoformat(
                        pt.get("start", "").replace("Z", "+00:00"))
                    pt_end = datetime.datetime.fromisoformat(
                        pt.get("end", "").replace("Z", "+00:00"))

                    # Check if project time overlaps with working time
                    if ((pt_start >= work_start and pt_start < work_end)
                            or (pt_end > work_start and pt_end <= work_end) or
                        (pt_start <= work_start and pt_end >= work_end)):
                        project_times_in_working_time.append(pt)
                except (ValueError, AttributeError, TypeError):
                    continue

            return project_times_in_working_time
        except Exception as e:
            logger.error(f"Error getting project times in work time: {e}")
            return []

    def get_working_time_types(self, categories=None, archived=False):
        """
        Get available working time types.

        Args:
            categories (list, optional): Filter by WorkingTimeTypeCategory
            archived (bool, optional): Include archived types (default: False)

        Returns:
            list: Working time type entries
        """
        params = {}
        
        if categories:
            params["categories"] = categories
        
        params["archived"] = archived

        # Use centralized pagination handling
        return self._request_paginated("/working-time-types", params=params)
