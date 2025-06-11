#!/usr/bin/env python3
"""
Debug Log Plugin for Merged Log Viewer

This plugin defines the schema for parsing debug log files.
The log format uses severity levels, Unix microsecond timestamps, module names, and messages.

This plugin demonstrates both regex-based parsing and custom parsing function approaches.
The parse_raw_line function takes precedence over the regex pattern when provided.
"""

import re
from datetime import datetime
from typing import Dict, Optional, Any

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from logging_config import get_logger

# Get logger for this plugin
logger = get_logger(__name__)


# Schema definition for debug log format
SCHEMA = {
    "regex": r"(?P<severity>[0-9]) (?P<timestamp>-|[0-9]+\.[0-9]{6}) (?P<module>-|[a-zA-Z][a-zA-Z0-9_]*) (?P<message>.*)",
    "timestamp_field": "timestamp",
    "fields": [
        {
            "name": "severity",
            "type": "enum",
            "enum_values": [
                {"value": "0", "name": "EMERGENCY"},
                {"value": "1", "name": "ALERT"},
                {"value": "2", "name": "CRITICAL"},
                {"value": "3", "name": "ERROR"},
                {"value": "4", "name": "WARNING"},
                {"value": "5", "name": "NOTICE"},
                {"value": "6", "name": "INFO"},
                {"value": "7", "name": "DEBUG"}
            ]
        },
        {
            "name": "timestamp",
            "type": "epoch"
        },
        {
            "name": "module",
            "type": "string",
            "is_discrete": True
        },
        {
            "name": "message",
            "type": "string",
            "is_discrete": False
        }
    ]
}


def parse_raw_line(raw_line: str) -> Optional[Dict[str, Any]]:
    """
    Custom parsing function for debug log lines.
    
    This function should parse the raw line and return a dictionary with field values
    as they appear in the log file. For enum fields, return the raw string values
    from the log, not converted values. The display layer will handle enum-to-name conversion.
    
    Args:
        raw_line: The raw log line to parse
        
    Returns:
        Dictionary with raw field values (strings for enums), or None if parsing fails
        
    Example log line:
        "3 1640995200.123456 auth_module User authentication failed"        Expected return:
        {
            'severity': "3",  # Raw string value from log, not converted to integer
            'timestamp': datetime(2021, 12, 31, 18, 0, 0, 123456),  # datetime object
            'module': 'auth_module',  # string
            'message': 'User authentication failed'  # string
        }
    """
    # Strip whitespace
    line = raw_line.strip()
    if not line:
        return None
    
    # Split by spaces but be careful with the message field which can contain spaces
    parts = line.split(' ', 3)  # Split into max 4 parts
    
    if len(parts) < 4:
        return None
    
    try:
        severity_str = parts[0]
        timestamp_str = parts[1]
        module_str = parts[2]
        message_str = parts[3]
        
        # Parse severity (keep as raw string from log)
        if not severity_str.isdigit():
            return None
        severity = severity_str  # Store as raw string, not converted to integer
        
        # Validate that the severity value is valid
        severity_field = next((field for field in SCHEMA['fields'] if field['name'] == 'severity'), None)
        if severity_field and severity_field['type'] == 'enum':
            enum_values = severity_field.get('enum_values', [])
            valid_values = {item['value'] for item in enum_values}
            if severity not in valid_values:
                return None  # Invalid severity value
            
        # Parse and convert timestamp to datetime object
        if timestamp_str == '-':
            timestamp = None  # Special case for missing timestamp
        else:
            try:
                timestamp_float = float(timestamp_str)
                from datetime import datetime
                timestamp = datetime.fromtimestamp(timestamp_float)
            except ValueError:
                return None
        
        # Validate module (should be '-' or alphanumeric with underscores)
        if module_str != '-' and not re.match(r'^[a-zA-Z][a-zA-Z0-9_]*$', module_str):
            return None
        
        # Return the raw values from the log file
        # The display layer will handle the conversion to display names
        return {
            'severity': severity,     # Raw string value ("0"-"7"), not converted
            'timestamp': timestamp,   # Already converted to datetime object
            'module': module_str,     # String value
            'message': message_str    # String value
        }
        
    except Exception:
        return None
