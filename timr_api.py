import requests
import json
import datetime
import pytz
import logging
from config import API_BASE_URL, REQUEST_TIMEOUT_SECONDS
from datetime import timedelta
from error_handler import timr_api_error_handler, ErrorCategory, ErrorSeverity, ErrorContext

logger = logging.getLogger(__name__)

# RFC 9457 problem type returned when booking a project time on a non-bookable task
PROBLEM_TYPE_TASK_NOT_BOOKABLE = "https://errors.timr.com/validation/task-not-bookable"


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


def _format_problem_message(problem):
    """
    Build an error message from an RFC 9457 problem details response.

    Args:
        problem (dict): Problem details with 'detail'/'title' and optional field 'errors'

    Returns:
        str: Message including field-level validation details, or None if not available
    """
    message = problem.get("detail") or problem.get("title")
    field_errors = []
    for error in problem.get("errors") or []:
        if error.get("field"):
            field_errors.append(f"{error['field']}: {error.get('detail', '')}")
        else:
            field_errors.append(error.get("detail", ""))
    if message and field_errors:
        return f"{message} ({'; '.join(field_errors)})"
    return message


class TimrApiError(Exception):
    """Exception raised for errors with the Timr API."""

    def __init__(self, message, status_code=None, response=None, problem_type=None):
        self.message = message
        self.status_code = status_code
        self.response = response
        # RFC 9457 problem type URI identifying the error category, if provided by the API
        self.problem_type = problem_type
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

    This client provides methods to interact with the Timr.com API for users,
    working times, project times, and tasks. Requests are authorized with an OAuth2
    access token assigned to `token`; `user` is the Timr user the client acts for
    (see timr_oauth.py for obtaining tokens). All list-based API endpoints automatically
    handle pagination transparently, so calling methods like get_bookable_tasks() will retrieve
    all available data regardless of API pagination limits.

    Key Features:
    - Automatic pagination handling for all list endpoints
    - Transparent data retrieval without manual pagination logic
    - Configurable page sizes and limits for performance optimization
    - Comprehensive error handling and logging
    """

    def __init__(self):
        """Initialize the TimrApi client."""
        self.base_url = API_BASE_URL
        self.token = None
        self.user = None
        self.session = requests.Session()

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
                headers=headers,
                timeout=REQUEST_TIMEOUT_SECONDS)

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
            problem_type = None
            error_msg = f"API request failed with status code {status_code}"

            # Extract detailed error information from the RFC 9457 problem details response
            try:
                content_type = e.response.headers.get('Content-Type', '')
                if content_type.startswith(('application/json', 'application/problem+json')):
                    response_data = e.response.json()
                    if isinstance(response_data, dict):
                        problem_type = response_data.get("type")
                        error_msg = _format_problem_message(response_data) or error_msg
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
                user_id=self.user.get('id') if self.user else None,
                operation=f"{method} {endpoint}"
            )
            
            # Create enhanced TimrApiError with user-friendly message
            api_error = TimrApiError(user_message, status_code, response_data, problem_type)
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
                    user_id=self.user.get('id') if self.user else None,
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
                    user_id=self.user.get('id') if self.user else None,
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
                    user_id=self.user.get('id') if self.user else None,
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

    def get_user(self, user_id):
        """
        Get a specific user.

        Args:
            user_id (str): User ID

        Returns:
            dict: User entry
        """
        return self._request("GET", f"/users/{user_id}")

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
            params["users"] = user_id
        elif self.user and "id" in self.user:
            params["users"] = self.user["id"]

        # Use centralized pagination handling
        return self._request_paginated("/working-times", params=params)

    def create_working_time(
            self,
            start,
            end,
            working_time_type_id,
            status="changeable",
            pause_duration=0):
        """
        Create a new working time entry for the current user.

        Args:
            start (datetime or str): Start time
            end (datetime or str): End time
            working_time_type_id (str): Type ID for working time
            status (str, optional): Status of the entry
            pause_duration (int, optional): Pause duration in minutes

        Returns:
            dict: Created working time entry
        """
        data = {
            "start": self._format_datetime_iso8601(start),
            "end": self._format_datetime_iso8601(end),
            "status": status,
            "changed": True,
            "user_id": self.user["id"],
            "working_time_type_id": working_time_type_id
        }

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

    def get_bookable_tasks(self, search=None):
        """
        Get the tasks the current user can book project times on today.

        The Timr API filters for tasks the user may record on, which are bookable
        and active today. Activity takes end dates inherited from closed parent
        tasks into account.

        Args:
            search (str, optional): Only return tasks whose name contains this text

        Returns:
            list: Task entries
        """
        params = {
            "bookable": True,
            "active_at": datetime.date.today().isoformat()
        }

        if search:
            params["name"] = search

        return self._request_paginated(f"/users/{self.user['id']}/tasks", params=params)

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
            params["users"] = user_id
        elif self.user and "id" in self.user:
            params["users"] = self.user["id"]

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
            "changed": True,
            "user_id": self.user["id"]
        }

        try:
            return self._request("POST", "/project-times", data=data)
        except TimrApiError as e:
            if e.problem_type != PROBLEM_TYPE_TASK_NOT_BOOKABLE:
                raise

            user_msg = timr_api_error_handler.log_business_rule_violation(
                rule_type="non_bookable_task",
                details=f"Task {task_id} is not bookable",
                user_id=self.user["id"],
                task_id=task_id
            )
            enhanced_error = TimrApiError(user_msg, e.status_code, e.response, e.problem_type)
            enhanced_error.technical_message = e.get_technical_message()
            raise enhanced_error from e

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
