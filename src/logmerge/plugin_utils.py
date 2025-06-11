#!/usr/bin/env python3
"""
Plugin Utilities

Functions and classes for loading, validating, and managing log parsing plugins.
This module handles the plugin system for the merged log viewer application.
"""

import re
import importlib.util
import importlib
from typing import Dict, Any, Callable


class LogParsingPlugin:
    """Represents a loaded and validated log parsing plugin.

    This class encapsulates a log parsing schema with optional custom parsing function,
    compiled regex patterns, and pre-built enum display mappings for performance.
    """

    def __init__(self, schema_data: Dict[str, Any], parse_function: Callable = None):
        """Initialize the plugin with schema data and optional parsing function.

        Args:
            schema_data: Dictionary containing field definitions and parsing rules
            parse_function: Optional custom parsing function from the plugin
        """
        self.schema_data = schema_data
        self.regex_pattern = schema_data.get(
            "regex"
        )  # Optional when custom parser is provided
        self.timestamp_field = schema_data.get("timestamp_field")
        self.fields = schema_data["fields"]
        self.parse_function = parse_function  # Custom parsing function from plugin

        # Only compile regex if we don't have a custom parser and regex is provided
        if not self.parse_function and self.regex_pattern:
            self.compiled_regex = re.compile(self.regex_pattern)
        else:
            self.compiled_regex = None

        # Pre-build enum display maps for performance
        self.enum_display_maps = self._build_enum_display_maps()

    def _build_enum_display_maps(self) -> Dict[str, Dict[str, str]]:
        """Build enum value->name mappings for display performance.

        Returns:
            Dictionary mapping field names to their value->name lookup dictionaries
        """
        display_maps = {}
        for field in self.fields:
            if field["type"] == "enum":
                field_name = field["name"]
                enum_values = field.get("enum_values", [])
                # Build value -> name lookup (supports both string and int values)
                display_maps[field_name] = {
                    item["value"]: item["name"] for item in enum_values
                }
        return display_maps

    @classmethod
    def from_file(cls, plugin_path: str) -> "LogParsingPlugin":
        """Load and create a LogParsingPlugin from a plugin file.

        Args:
            plugin_path: Path to the Python plugin file

        Returns:
            Initialized LogParsingPlugin instance

        Raises:
            Various exceptions from load_plugin_schema and LogParsingPlugin.__init__
        """
        schema_data, parse_function = load_plugin_schema(plugin_path)
        return cls(schema_data, parse_function)


def load_plugin_schema(plugin_path: str) -> tuple[Dict[str, Any], Callable]:
    """Load schema and optional parsing function from a Python plugin file.

    Args:
        plugin_path: Path to the Python plugin file

    Returns:
        Tuple containing (schema_data, parse_function)
        parse_function will be None if not provided by plugin

    Raises:
        FileNotFoundError: If plugin file doesn't exist
        ImportError: If plugin can't be imported
        AttributeError: If plugin doesn't have SCHEMA variable
        ValueError: If schema is invalid
    """
    try:
        # Create module spec from file path
        module_name = "log_schema_plugin"
        spec = importlib.util.spec_from_file_location(module_name, plugin_path)
        if spec is None:
            raise ImportError(f"Could not create module spec from {plugin_path}")

        # Create and execute the module
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # Check if SCHEMA variable exists
        if not hasattr(module, "SCHEMA"):
            raise AttributeError("Plugin file must contain a 'SCHEMA' variable")

        schema_data = module.SCHEMA

        # Validate that schema_data is a dictionary
        if not isinstance(schema_data, dict):
            raise ValueError("SCHEMA variable must be a dictionary")

        # Check for optional parse_raw_line function
        parse_function = getattr(module, "parse_raw_line", None)

        # Validate the schema structure
        validate_schema_structure(schema_data, parse_function)

        return schema_data, parse_function

    except FileNotFoundError:
        raise FileNotFoundError(f"Plugin file not found: {plugin_path}")
    except Exception as e:
        # Re-raise with more context for debugging
        raise type(e)(f"Error loading plugin {plugin_path}: {str(e)}")


def validate_schema_structure(
    schema_data: Dict[str, Any], parse_function: Callable = None
) -> None:
    """Validate the structure and content of a plugin schema.

    Args:
        schema_data: The schema dictionary to validate
        parse_function: Optional custom parsing function

    Raises:
        ValueError: If schema structure is invalid
    """
    # Validate required keys - 'regex' is optional if parse_function is provided
    required_keys = ["fields"]
    if parse_function is None:
        required_keys.append("regex")

    for key in required_keys:
        if key not in schema_data:
            if key == "regex" and parse_function is not None:
                continue  # regex not required if custom parser provided
            raise ValueError(f"Schema missing required key: {key}")

    # Validate timestamp_field if provided
    validate_timestamp_field(schema_data)

    # Validate parse_function if provided
    if parse_function is not None and not callable(parse_function):
        raise ValueError("parse_raw_line must be a callable function")


def validate_timestamp_field(schema_data: Dict[str, Any]) -> None:
    """Validate the timestamp field configuration in a schema.

    Args:
        schema_data: The schema dictionary containing timestamp field info

    Raises:
        ValueError: If timestamp field configuration is invalid
    """
    timestamp_field = schema_data.get("timestamp_field")
    if not timestamp_field:
        return  # No timestamp field specified - this is optional

    # Check that the timestamp_field refers to an existing field
    field_names = [field["name"] for field in schema_data["fields"]]
    if timestamp_field not in field_names:
        raise ValueError(f"timestamp_field '{timestamp_field}' not found in fields")

    # Check that the timestamp field is epoch, strptime, or float_timestamp type
    timestamp_field_def = next(
        (field for field in schema_data["fields"] if field["name"] == timestamp_field),
        None,
    )
    if timestamp_field_def and timestamp_field_def["type"] not in [
        "epoch",
        "strptime",
        "float_timestamp",
    ]:
        raise ValueError(
            f"timestamp_field '{timestamp_field}' must be of type 'epoch', 'strptime', or 'float_timestamp'"
        )

    # If strptime, ensure strptime_fmt is provided
    if timestamp_field_def and timestamp_field_def["type"] == "strptime":
        if not timestamp_field_def.get("strptime_fmt"):
            raise ValueError(
                f"Field '{timestamp_field}' uses 'strptime' but missing 'strptime_fmt'"
            )
