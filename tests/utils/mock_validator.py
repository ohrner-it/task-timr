"""
Mock validation framework for ensuring test data accuracy.

This module provides comprehensive validation of mock data against real API responses:

Key Features:
- Bidirectional field validation (missing + extra fields)
- Type checking and validation
- String format validation (UUID, email, ISO dates)
- Severity-based reporting (critical, warning, info)
- Structure template extraction from real data

Usage:
    validator = MockValidator()
    issues = validator.validate_structure(mock_data, real_data)
    report = validator.generate_report()
    
    # Or use convenience function
    report = validate_mock_against_real(mock_data, real_data, "endpoint_name")
"""

import json
import re
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass
from enum import Enum


class ValidationSeverity(Enum):
    CRITICAL = "CRITICAL"
    WARNING = "WARNING"  
    INFO = "INFO"


@dataclass
class ValidationIssue:
    severity: ValidationSeverity
    category: str
    path: str
    issue: str
    suggestion: Optional[str] = None
    mock_value: Any = None
    real_value: Any = None


class MockValidator:
    """Comprehensive validator for comparing mock data against real API responses."""
    
    def __init__(self):
        self.issues: List[ValidationIssue] = []
        
    def validate_structure(self, mock_data: Any, real_data: Any, path: str = "root") -> List[ValidationIssue]:
        """
        Comprehensively validate mock data against real API response.
        
        Args:
            mock_data: Mock data structure to validate
            real_data: Real API response data
            path: Current path in the data structure (for reporting)
            
        Returns:
            List of validation issues found
        """
        self.issues = []
        self._validate_recursive(mock_data, real_data, path)
        return self.issues
    
    def _validate_recursive(self, mock: Any, real: Any, path: str):
        """Recursively validate data structures."""
        
        # Handle None/null values
        if mock is None and real is None:
            return
        if mock is None and real is not None:
            self._add_issue(ValidationSeverity.WARNING, "null_mismatch", path,
                          f"Mock is null but real API returns {type(real).__name__}")
        if mock is not None and real is None:
            self._add_issue(ValidationSeverity.WARNING, "null_mismatch", path,
                          f"Mock has {type(mock).__name__} but real API returns null")
            return
            
        # Type validation
        mock_type = type(mock)
        real_type = type(real)
        
        if mock_type != real_type:
            self._add_issue(ValidationSeverity.CRITICAL, "type_mismatch", path,
                          f"Type mismatch: mock is {mock_type.__name__}, real is {real_type.__name__}",
                          f"Change mock value from {mock_type.__name__} to {real_type.__name__}")
            return
            
        # Dictionary validation
        if isinstance(mock, dict) and isinstance(real, dict):
            self._validate_dict(mock, real, path)
            
        # List validation  
        elif isinstance(mock, list) and isinstance(real, list):
            self._validate_list(mock, real, path)
            
        # Primitive value validation
        else:
            self._validate_primitive(mock, real, path)
    
    def _validate_dict(self, mock: Dict, real: Dict, path: str):
        """Validate dictionary structures bidirectionally."""
        
        mock_keys = set(mock.keys())
        real_keys = set(real.keys())
        
        # Check for missing fields in mock
        missing_in_mock = real_keys - mock_keys
        for key in missing_in_mock:
            self._add_issue(ValidationSeverity.CRITICAL, "missing_field", f"{path}.{key}",
                          f"Field exists in real API but missing in mock",
                          f"Add field '{key}' to mock with value type {type(real[key]).__name__}")
        
        # Check for extra fields in mock
        extra_in_mock = mock_keys - real_keys
        for key in extra_in_mock:
            self._add_issue(ValidationSeverity.WARNING, "extra_field", f"{path}.{key}",
                          f"Field exists in mock but not in real API",
                          f"Remove field '{key}' from mock or verify API response")
        
        # Recursively validate common fields
        common_keys = mock_keys & real_keys
        for key in common_keys:
            self._validate_recursive(mock[key], real[key], f"{path}.{key}")
    
    def _validate_list(self, mock: List, real: List, path: str):
        """Validate list structures."""
        
        if len(mock) == 0 and len(real) == 0:
            return
            
        if len(mock) == 0 and len(real) > 0:
            self._add_issue(ValidationSeverity.WARNING, "empty_list", path,
                          f"Mock list is empty but real API returns {len(real)} items",
                          f"Add at least one mock item matching real API structure")
            return
            
        if len(real) == 0 and len(mock) > 0:
            self._add_issue(ValidationSeverity.INFO, "mock_has_data", path,
                          f"Mock has {len(mock)} items but real API returned empty list")
            return
        
        # Validate first items of each list (assuming homogeneous lists)
        if len(mock) > 0 and len(real) > 0:
            self._validate_recursive(mock[0], real[0], f"{path}[0]")
            
        # Check for length discrepancies (info level)
        if len(mock) != len(real):
            self._add_issue(ValidationSeverity.INFO, "length_mismatch", path,
                          f"Mock list has {len(mock)} items, real API has {len(real)} items")
    
    def _validate_primitive(self, mock: Any, real: Any, path: str):
        """Validate primitive values for realism."""
        
        # For strings, check format patterns
        if isinstance(mock, str) and isinstance(real, str):
            self._validate_string_patterns(mock, real, path)
            
        # For numbers, check reasonable ranges
        elif isinstance(mock, (int, float)) and isinstance(real, (int, float)):
            self._validate_numeric_ranges(mock, real, path)
    
    def _validate_string_patterns(self, mock: str, real: str, path: str):
        """Validate string patterns and formats."""
        
        # UUID pattern validation
        uuid_pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
        if re.match(uuid_pattern, real) and not re.match(uuid_pattern, mock):
            self._add_issue(ValidationSeverity.WARNING, "format_mismatch", path,
                          f"Real API uses UUID format but mock doesn't",
                          f"Use UUID format for mock value (e.g., 'xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx')")
        
        # ISO date pattern validation
        iso_date_pattern = r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\+\d{2}:\d{2}|Z)$'
        if re.match(iso_date_pattern, real) and not re.match(iso_date_pattern, mock):
            self._add_issue(ValidationSeverity.WARNING, "format_mismatch", path,
                          f"Real API uses ISO date format but mock doesn't",
                          f"Use ISO date format for mock value (e.g., '2025-04-01T09:00:00+00:00')")
        
        # Email pattern validation  
        email_pattern = r'^[^@]+@[^@]+\.[^@]+$'
        if re.match(email_pattern, real) and not re.match(email_pattern, mock):
            self._add_issue(ValidationSeverity.WARNING, "format_mismatch", path,
                          f"Real API uses email format but mock doesn't",
                          f"Use email format for mock value (e.g., 'test@example.com')")
    
    def _validate_numeric_ranges(self, mock: Any, real: Any, path: str):
        """Validate numeric values are in reasonable ranges."""
        
        # Check for obviously unrealistic values
        if isinstance(mock, int) and isinstance(real, int):
            if real > 0 and mock <= 0:
                self._add_issue(ValidationSeverity.WARNING, "unrealistic_value", path,
                              f"Mock value {mock} seems unrealistic compared to real value {real}",
                              f"Use positive integer for mock value")
    
    def _add_issue(self, severity: ValidationSeverity, category: str, path: str, 
                   issue: str, suggestion: Optional[str] = None):
        """Add a validation issue to the results."""
        self.issues.append(ValidationIssue(
            severity=severity,
            category=category,
            path=path,
            issue=issue,
            suggestion=suggestion
        ))
    
    def generate_report(self) -> str:
        """Generate a comprehensive validation report."""
        if not self.issues:
            return "✅ **VALIDATION PASSED**: Mock data perfectly matches real API structure!"
            
        report = []
        report.append("# 🔍 **MOCK VALIDATION REPORT**\n")
        
        # Summary
        critical_count = sum(1 for issue in self.issues if issue.severity == ValidationSeverity.CRITICAL)
        warning_count = sum(1 for issue in self.issues if issue.severity == ValidationSeverity.WARNING)
        info_count = sum(1 for issue in self.issues if issue.severity == ValidationSeverity.INFO)
        
        report.append(f"**Summary**: {len(self.issues)} issues found")
        report.append(f"- 🚨 Critical: {critical_count}")
        report.append(f"- ⚠️  Warnings: {warning_count}")
        report.append(f"- ℹ️  Info: {info_count}\n")
        
        # Group issues by severity
        for severity in [ValidationSeverity.CRITICAL, ValidationSeverity.WARNING, ValidationSeverity.INFO]:
            severity_issues = [issue for issue in self.issues if issue.severity == severity]
            if not severity_issues:
                continue
                
            icon = {"CRITICAL": "🚨", "WARNING": "⚠️", "INFO": "ℹ️"}[severity.value]
            report.append(f"## {icon} **{severity.value} ISSUES** ({len(severity_issues)})\n")
            
            for issue in severity_issues:
                report.append(f"### `{issue.path}`")
                report.append(f"**Category**: {issue.category}")
                report.append(f"**Issue**: {issue.issue}")
                if issue.suggestion:
                    report.append(f"**Suggestion**: {issue.suggestion}")
                report.append("")
        
        return "\n".join(report)
    
    def get_critical_issues(self) -> List[ValidationIssue]:
        """Get only critical issues that must be fixed."""
        return [issue for issue in self.issues if issue.severity == ValidationSeverity.CRITICAL]
    
    def has_critical_issues(self) -> bool:
        """Check if there are any critical issues."""
        return len(self.get_critical_issues()) > 0


def validate_mock_against_real(mock_data: Any, real_data: Any, data_type: str = "response") -> str:
    """
    Convenience function to validate mock data against real API response.
    
    Args:
        mock_data: Mock data to validate
        real_data: Real API response data
        data_type: Type of data being validated (for reporting)
        
    Returns:
        Validation report as string
    """
    validator = MockValidator()
    validator.validate_structure(mock_data, real_data, data_type)
    return validator.generate_report()


def extract_structure_template(data: Any, path: str = "root") -> Dict:
    """
    Extract a structure template from real API data that can be used to create mocks.
    
    Args:
        data: Real API response data
        path: Current path in the structure
        
    Returns:
        Structure template with type information
    """
    if data is None:
        return {"type": "null", "value": None}
    
    data_type = type(data).__name__
    
    if isinstance(data, dict):
        return {
            "type": "object",
            "fields": {key: extract_structure_template(value, f"{path}.{key}") 
                      for key, value in data.items()}
        }
    elif isinstance(data, list):
        if len(data) == 0:
            return {"type": "array", "items": "empty"}
        else:
            return {
                "type": "array", 
                "items": extract_structure_template(data[0], f"{path}[0]"),
                "length": len(data)
            }
    elif isinstance(data, str):
        # Detect common patterns
        uuid_pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
        iso_date_pattern = r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\+\d{2}:\d{2}|Z)$'
        email_pattern = r'^[^@]+@[^@]+\.[^@]+$'
        
        if re.match(uuid_pattern, data):
            return {"type": "string", "format": "uuid", "example": data}
        elif re.match(iso_date_pattern, data):
            return {"type": "string", "format": "iso_date", "example": data}
        elif re.match(email_pattern, data):
            return {"type": "string", "format": "email", "example": data}
        else:
            return {"type": "string", "example": data}
    else:
        return {"type": data_type, "example": data}