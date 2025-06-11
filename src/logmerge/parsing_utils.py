#!/usr/bin/env python3
"""
Parsing Utilities

Pure functions for log parsing and field value conversion.
These functions are extracted from the main application to be reusable and testable.
"""

from typing import Dict, Any, Optional
from datetime import datetime
from .plugin_utils import LogParsingPlugin


def convert_field_value(raw_value: str, field: Dict[str, Any]) -> Any:
    """Convert a raw string value to the appropriate type.

    Args:
        raw_value: The raw string value to convert
        field: Field definition dictionary containing type and conversion info

    Returns:
        Converted value according to the field type

    Raises:
        ValueError: If conversion fails or required parameters are missing
        TypeError: If the raw_value cannot be converted to the target type
    """
    field_type = field["type"]

    if field_type == "string":
        return raw_value

    elif field_type == "int":
        return int(raw_value)

    elif field_type == "float":
        return float(raw_value)

    elif field_type == "epoch":
        # Handle Unix epoch timestamp (int or float)
        timestamp_float = float(raw_value)
        return datetime.fromtimestamp(timestamp_float)

    elif field_type == "strptime":
        # Use custom strptime format
        strptime_fmt = field.get("strptime_fmt")
        if not strptime_fmt:
            raise ValueError(
                f"Field {field['name']} uses 'strptime' but missing 'strptime_fmt'"
            )
        return datetime.strptime(raw_value, strptime_fmt)

    elif field_type == "float_timestamp":
        # Return raw float timestamp without datetime conversion
        return float(raw_value)

    elif field_type == "enum":
        # Store raw enum value directly - no conversion needed
        return raw_value

    else:
        return raw_value


def parse_line_with_regex(
    raw_line: str, schema: LogParsingPlugin
) -> Optional[Dict[str, Any]]:
    """Parse a single log line using the compiled regex pattern and convert field values.

    Args:
        raw_line: The raw log line to parse
        schema: LogSchema object containing compiled regex, fields, and enum lookups

    Returns:
        Dictionary with parsed and converted field values (ready for display), or None if parsing fails
    """
    try:
        if not schema.compiled_regex:
            return None

        match = schema.compiled_regex.match(raw_line)
        if not match:
            return None

        # Extract and convert field values from regex groups
        converted_fields = {}
        for field in schema.fields:
            field_name = field["name"]
            raw_value = match.group(field_name)

            if raw_value is None:
                # Include None values in the fields - they are valid data points
                converted_fields[field_name] = None
                continue

            try:
                # Convert the raw string value according to the field type
                converted_value = convert_field_value(raw_value, field)
                converted_fields[field_name] = converted_value
            except (ValueError, TypeError):
                # Type conversion failed - treat as None
                converted_fields[field_name] = None

        return converted_fields

    except Exception:
        return None
