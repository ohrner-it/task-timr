"""
Enhanced error handling and logging system for Task Timr.
Provides detailed error categorization, structured logging, and user-friendly error messages.

Copyright (c) 2025 Ohrner IT GmbH
Licensed under the MIT License
"""

import logging
import json
from typing import Dict, Any, Optional, Union
from enum import Enum
from dataclasses import dataclass, asdict
from datetime import datetime


class ErrorCategory(Enum):
    """Error categories for systematic error handling."""
    TIMR_API_ERROR = "timr_api_error"
    TIMR_BUSINESS_RULE = "timr_business_rule"
    DATA_VALIDATION = "data_validation"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    NETWORK = "network"
    SYSTEM = "system"
    USER_INPUT = "user_input"


class ErrorSeverity(Enum):
    """Error severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ErrorContext:
    """Context information for enhanced error logging."""
    category: ErrorCategory
    severity: ErrorSeverity
    operation: str
    user_id: Optional[str] = None
    working_time_id: Optional[str] = None
    task_id: Optional[str] = None
    request_data: Optional[Dict[str, Any]] = None
    api_endpoint: Optional[str] = None
    api_status_code: Optional[int] = None
    api_response: Optional[Union[str, Dict[str, Any]]] = None
    timestamp: Optional[str] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()


class EnhancedErrorHandler:
    """Enhanced error handler with structured logging and categorization."""
    
    def __init__(self, logger_name: str):
        self.logger = logging.getLogger(logger_name)
        
        # Define user-friendly error messages for different categories
        self.user_messages = {
            ErrorCategory.TIMR_API_ERROR: {
                400: "Invalid request data. Please check your input and try again.",
                401: "Authentication failed. Please log in again.",
                403: "Access denied. You don't have permission for this operation.",
                404: "The requested resource was not found.",
                409: "This operation conflicts with existing data.",
                422: "The data provided is invalid or incomplete.",
                500: "The Timr service is temporarily unavailable. Please try again later.",
                502: "Connection to the Timr service failed. Please check your internet connection.",
                503: "The Timr service is currently under maintenance. Please try again later."
            },
            ErrorCategory.TIMR_BUSINESS_RULE: {
                "frozen_time": "This working time is frozen and cannot be modified.",
                "non_bookable_task": "This task is not bookable. Please select a different task.",
                "overlapping_times": "This time entry overlaps with existing entries.",
                "ongoing_modification": "Cannot modify ongoing working times. Please stop the timer first.",
                "invalid_time_range": "The time range is invalid or outside allowed limits."
            },
            ErrorCategory.DATA_VALIDATION: {
                "missing_required": "Required information is missing.",
                "invalid_format": "The data format is invalid.",
                "out_of_range": "The value is outside the allowed range.",
                "invalid_duration": "The duration must be positive.",
                "invalid_date": "The date format is invalid."
            },
            ErrorCategory.NETWORK: {
                "connection_error": "Network connection failed. Please check your internet connection and try again.",
                "timeout": "The request timed out. Please try again.",
                "dns_error": "Cannot connect to the Timr service. Please check your network settings."
            },
            ErrorCategory.AUTHENTICATION: {
                "invalid_credentials": "Invalid username or password.",
                "token_expired": "Your session has expired. Please log in again.",
                "session_invalid": "Your session is invalid. Please log in again."
            }
        }
    
    def log_error(self, error: Exception, context: ErrorContext, include_stacktrace: Optional[bool] = None) -> str:
        """
        Log an error with enhanced context and return a user-friendly message.
        
        Args:
            error: The exception that occurred
            context: Error context information
            include_stacktrace: Whether to include the full stacktrace in logs.
                               If None, automatically determined based on error severity and category.
            
        Returns:
            str: User-friendly error message
        """
        # Create structured log entry
        log_entry = {
            "error_category": context.category.value,
            "error_severity": context.severity.value,
            "operation": context.operation,
            "error_message": str(error),
            "error_type": type(error).__name__,
            "timestamp": context.timestamp
        }
        
        # Add context data
        if context.user_id:
            log_entry["user_id"] = context.user_id
        if context.working_time_id:
            log_entry["working_time_id"] = context.working_time_id
        if context.task_id:
            log_entry["task_id"] = context.task_id
        if context.api_endpoint:
            log_entry["api_endpoint"] = context.api_endpoint
        if context.api_status_code:
            log_entry["api_status_code"] = context.api_status_code
        if context.api_response:
            log_entry["api_response"] = self._sanitize_response(context.api_response)
        if context.request_data:
            log_entry["request_data"] = self._sanitize_request_data(context.request_data)
        
        # Create detailed log message with context
        log_message = f"[{context.category.value.upper()}] {context.operation}: {str(error)}"
        
        # Add context details to the log message for better visibility
        context_details = []
        if context.user_id:
            context_details.append(f"user_id={context.user_id}")
        if context.working_time_id:
            context_details.append(f"working_time_id={context.working_time_id}")
        if context.task_id:
            context_details.append(f"task_id={context.task_id}")
        if context.api_endpoint:
            context_details.append(f"endpoint={context.api_endpoint}")
        if context.api_status_code:
            context_details.append(f"status={context.api_status_code}")
        
        if context_details:
            log_message += f" [{', '.join(context_details)}]"
        
        # Determine if stacktrace should be included based on severity and category
        if include_stacktrace is None:
            include_stacktrace = self._should_include_stacktrace(context)
        
        if context.severity == ErrorSeverity.CRITICAL:
            self.logger.critical(log_message, extra=log_entry, exc_info=include_stacktrace)
        elif context.severity == ErrorSeverity.HIGH:
            self.logger.error(log_message, extra=log_entry, exc_info=include_stacktrace)
        elif context.severity == ErrorSeverity.MEDIUM:
            self.logger.warning(log_message, extra=log_entry, exc_info=include_stacktrace)
        else:
            self.logger.info(log_message, extra=log_entry, exc_info=include_stacktrace if context.severity != ErrorSeverity.LOW else False)
        
        # Return user-friendly message
        return self._get_user_message(context, error)
    
    def log_api_error(self, error: Exception, endpoint: str, status_code: Optional[int] = None, 
                     response: Optional[Union[str, Dict[str, Any]]] = None, 
                     request_data: Optional[Dict[str, Any]] = None,
                     user_id: Optional[str] = None, operation: str = "API request") -> str:
        """
        Log a Timr API error with enhanced context.
        
        Args:
            error: The API exception
            endpoint: The API endpoint that failed
            status_code: HTTP status code
            response: API response data
            request_data: Request data that was sent
            user_id: User ID for context
            operation: Description of the operation
            
        Returns:
            str: User-friendly error message
        """
        # Determine error category and severity based on status code
        if status_code:
            if status_code == 401:
                category = ErrorCategory.AUTHENTICATION
                severity = ErrorSeverity.MEDIUM
            elif status_code == 403:
                category = ErrorCategory.AUTHORIZATION
                severity = ErrorSeverity.MEDIUM
            elif status_code in [400, 404, 409, 422]:
                category = ErrorCategory.TIMR_API_ERROR
                severity = ErrorSeverity.MEDIUM
            elif status_code >= 500:
                category = ErrorCategory.TIMR_API_ERROR
                severity = ErrorSeverity.HIGH
            else:
                category = ErrorCategory.TIMR_API_ERROR
                severity = ErrorSeverity.MEDIUM
        else:
            category = ErrorCategory.NETWORK
            severity = ErrorSeverity.MEDIUM
        
        context = ErrorContext(
            category=category,
            severity=severity,
            operation=operation,
            user_id=user_id,
            api_endpoint=endpoint,
            api_status_code=status_code,
            api_response=response,
            request_data=request_data
        )
        
        return self.log_error(error, context)
    
    def log_business_rule_violation(self, rule_type: str, details: str, 
                                  user_id: Optional[str] = None,
                                  working_time_id: Optional[str] = None,
                                  task_id: Optional[str] = None) -> str:
        """
        Log a Timr business rule violation.
        
        Args:
            rule_type: Type of business rule violated
            details: Detailed description
            user_id: User ID for context
            working_time_id: Working time ID for context
            task_id: Task ID for context
            
        Returns:
            str: User-friendly error message
        """
        context = ErrorContext(
            category=ErrorCategory.TIMR_BUSINESS_RULE,
            severity=ErrorSeverity.MEDIUM,
            operation=f"business_rule_check_{rule_type}",
            user_id=user_id,
            working_time_id=working_time_id,
            task_id=task_id
        )
        
        error = ValueError(details)
        return self.log_error(error, context)
    
    def log_validation_error(self, field: str, value: Any, reason: str,
                           user_id: Optional[str] = None) -> str:
        """
        Log a data validation error.
        
        Args:
            field: Field name that failed validation
            value: The invalid value
            reason: Reason for validation failure
            user_id: User ID for context
            
        Returns:
            str: User-friendly error message
        """
        context = ErrorContext(
            category=ErrorCategory.DATA_VALIDATION,
            severity=ErrorSeverity.LOW,
            operation=f"validate_{field}",
            user_id=user_id,
            request_data={"field": field, "value": str(value), "reason": reason}
        )
        
        error = ValueError(f"Validation failed for {field}: {reason}")
        return self.log_error(error, context)
    
    def _get_user_message(self, context: ErrorContext, error: Exception) -> str:
        """Get user-friendly error message based on context."""
        category_messages = self.user_messages.get(context.category, {})
        
        # For API errors, prefer specific API error message if meaningful, fall back to generic status code message
        if context.category == ErrorCategory.TIMR_API_ERROR and context.api_status_code:
            # First check if we have a meaningful API error message
            error_str = str(error)
            
            # Define patterns that indicate generic/unhelpful error messages
            generic_patterns = [
                f"API request failed with status code {context.api_status_code}",
                "bad request",
                "invalid request",
                "error occurred",
                "request failed",
                "server error",
                "internal error"
            ]
            
            # Check if this is a meaningful error message
            if (error_str and 
                len(error_str.strip()) > 15 and  # Must be reasonably long
                not error_str.lower().startswith("http") and  # Avoid HTTP error messages
                not any(pattern in error_str.lower() for pattern in generic_patterns) and  # Avoid generic patterns
                not error_str.lower() in ["bad request", "unauthorized", "forbidden", "not found"]):  # Avoid basic HTTP status messages
                return error_str
            
            # Fall back to status code specific message
            message = category_messages.get(context.api_status_code)
            if message:
                return message
        
        # For business rule violations, use specific rule type
        if context.category == ErrorCategory.TIMR_BUSINESS_RULE:
            error_str = str(error).lower()
            if "frozen" in error_str:
                return category_messages.get("frozen_time", str(error))
            elif "not bookable" in error_str:
                return category_messages.get("non_bookable_task", str(error))
            elif "overlap" in error_str:
                return category_messages.get("overlapping_times", str(error))
            elif "ongoing" in error_str:
                return category_messages.get("ongoing_modification", str(error))
        
        # For validation errors, use specific validation type
        if context.category == ErrorCategory.DATA_VALIDATION:
            error_str = str(error).lower()
            if "required" in error_str:
                return category_messages.get("missing_required", str(error))
            elif "format" in error_str:
                return category_messages.get("invalid_format", str(error))
            elif "duration" in error_str:
                return category_messages.get("invalid_duration", str(error))
        
        # For network errors
        if context.category == ErrorCategory.NETWORK:
            error_str = str(error).lower()
            if "timeout" in error_str or "timed out" in error_str:
                return category_messages.get("timeout", "The request timed out. Please try again.")
            else:
                return category_messages.get("connection_error", "Network error occurred. Please try again.")
        
        # For authentication errors
        if context.category == ErrorCategory.AUTHENTICATION:
            return category_messages.get("invalid_credentials", "Authentication failed. Please log in again.")
        
        # Default fallback
        return "An unexpected error occurred. Please try again or contact support if the problem persists."
    
    def _sanitize_request_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Remove sensitive information from request data for logging."""
        if not isinstance(data, dict):
            return {"data": str(data)}
        
        sanitized = {}
        sensitive_fields = {'password', 'token', 'secret', 'key', 'auth'}
        
        for key, value in data.items():
            if any(field in key.lower() for field in sensitive_fields):
                sanitized[key] = "***REDACTED***"
            else:
                sanitized[key] = value
        
        return sanitized
    
    def _sanitize_response(self, response: Union[str, Dict[str, Any]]) -> Union[str, Dict[str, Any]]:
        """Remove sensitive information from API response for logging."""
        if isinstance(response, str):
            return response[:1000] if len(response) > 1000 else response
        
        if isinstance(response, dict):
            sanitized = {}
            sensitive_fields = {'password', 'token', 'secret', 'key', 'auth'}
            
            for key, value in response.items():
                if any(field in key.lower() for field in sensitive_fields):
                    sanitized[key] = "***REDACTED***"
                else:
                    sanitized[key] = value
            
            return sanitized
        
        return str(response)
    
    def _should_include_stacktrace(self, context: ErrorContext) -> bool:
        """
        Determine whether to include a stacktrace based on error context.
        
        Stacktraces are included for:
        - CRITICAL and HIGH severity errors (always need debugging info)
        - SYSTEM errors (unexpected application errors)
        - API errors with 5xx status codes (server-side issues)
        - Any unexpected exceptions (not business rule violations or user input errors)
        
        Stacktraces are excluded for:
        - Expected business rule violations (user tried something not allowed)
        - Simple validation errors (user input problems)
        - Authentication failures (expected when tokens expire)
        
        Args:
            context: Error context information
            
        Returns:
            bool: True if stacktrace should be included
        """
        # Always include stacktraces for critical and high severity issues
        if context.severity in [ErrorSeverity.CRITICAL, ErrorSeverity.HIGH]:
            return True
        
        # Always include for system errors (unexpected application issues)
        if context.category == ErrorCategory.SYSTEM:
            return True
        
        # Include for server-side API errors (5xx status codes)
        if (context.category == ErrorCategory.TIMR_API_ERROR and 
            context.api_status_code and context.api_status_code >= 500):
            return True
        
        # Exclude for client-side API errors (4xx status codes) unless high severity
        if (context.category == ErrorCategory.TIMR_API_ERROR and 
            context.api_status_code and 400 <= context.api_status_code < 500 and
            context.severity not in [ErrorSeverity.CRITICAL, ErrorSeverity.HIGH]):
            return False
        
        # Include for network errors (connection issues need debugging)
        if context.category == ErrorCategory.NETWORK:
            return True
        
        # Exclude for expected business rule violations
        if context.category == ErrorCategory.TIMR_BUSINESS_RULE:
            return False
        
        # Exclude for simple validation errors  
        if context.category == ErrorCategory.DATA_VALIDATION:
            return False
        
        # Exclude for authentication issues (usually expected when sessions expire)
        if context.category == ErrorCategory.AUTHENTICATION:
            return False
        
        # Include for authorization issues (might indicate configuration problems)
        if context.category == ErrorCategory.AUTHORIZATION:
            return True
        
        # Default: include stacktrace for medium severity and above
        return context.severity != ErrorSeverity.LOW


# Global error handler instances
timr_api_error_handler = EnhancedErrorHandler("timr_api")
app_error_handler = EnhancedErrorHandler("app")
utils_error_handler = EnhancedErrorHandler("timr_utils")