#!/usr/bin/env python3
"""
Debug Log Plugin for Merged Log Viewer

This plugin defines the schema for parsing debug log files.
The log format uses severity levels, Unix microsecond timestamps, module names, and messages.

This plugin demonstrates both regex-based parsing and custom parsing function approaches.
The parse_raw_line function takes precedence over the regex pattern when provided.
"""

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
                {"value": "7", "name": "DEBUG"},
            ],
        },
        {"name": "timestamp", "type": "epoch"},
        {"name": "module", "type": "string", "is_discrete": True},
        {"name": "message", "type": "string", "is_discrete": False},
    ],
}
