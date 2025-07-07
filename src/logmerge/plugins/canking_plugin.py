#!/usr/bin/env python3
"""
CAN King Log Plugin for Merged Log Viewer

This plugin defines the schema for parsing CAN King log files.
The log format contains CAN bus messages with identifiers, data, timestamps, and direction.

Example log format:
Chn Identifier Flg   DLC  D0...1...2...3...4...5...6..D7       Time     Dir
 0    0000014B         1  00                                1675.570498 T
 0    00000065         5  01  00  00  00  00                1675.572378 T
 0    00002102 X       8  60  00  00  5F  60  60  E2  F2   46055.090598 R
"""

import re
import sys
from pathlib import Path
from typing import Dict, Optional, Any

# Import logging from parent package
sys.path.insert(0, str(Path(__file__).parent.parent))
from logging_config import get_logger

# Get logger for this plugin
logger = get_logger(__name__)

# Schema definition for CAN King log format
SCHEMA = {
    "regex": r"^\s*(?P<channel>\d+)\s+(?P<identifier>[0-9A-Fa-f]+)\s*(?P<flag>[A-Z]?)\s+(?P<dlc>\d+)\s+(?P<data>(?:[0-9A-Fa-f]{2}(?:\s+[0-9A-Fa-f]{2})*)?)\s+(?P<timestamp>\d+\.\d+)\s+(?P<direction>[TR])\s*$",
    "timestamp_field": "timestamp", 
    "fields": [
        {
            "name": "channel",
            "type": "int"
        },
        {
            "name": "identifier",
            "type": "string",
            "is_discrete": True
        },
        {
            "name": "flag",
            "type": "string",
            "is_discrete": True
        },
        {
            "name": "dlc",
            "type": "int"
        },
        {
            "name": "data",
            "type": "string",
            "is_discrete": False
        },
        {
            "name": "timestamp",
            "type": "float_timestamp",
        },
        {
            "name": "direction",
            "type": "enum",
            "enum_values": [
                {"value": "T", "name": "TRANSMIT"},
                {"value": "R", "name": "RECEIVE"}
            ]
        }
    ]
}

# Pre-compiled regex for maximum performance - get pattern from schema to avoid duplication
_COMPILED_REGEX = re.compile(SCHEMA["regex"])


def parse_raw_line(raw_line: str) -> Optional[Dict[str, Any]]:
    """
    Custom parsing function for CAN King log lines.
    
    This function parses CAN bus log lines and returns a dictionary with field values
    as they appear in the log file. Enum fields return raw values for display layer handling.
    
    Args:
        raw_line: The raw log line to parse
        
    Returns:
        Dictionary with fully converted field values (ready for display), or None if parsing fails
        
    Example log line:
        " 0    0000014B         1  00                                1675.570498 T"
        " 0    00002102 X       8  60  00  00  5F  60  60  E2  F2   46055.090598 R"
        
    Expected return:
        {
            'channel': 0,                    # int
            'identifier': '0000014B',        # string (hex ID)
            'flag': '',                      # string (flag character or empty)
            'dlc': 1,                        # int (data length)
            'data': '00',                    # string (hex data bytes)
            'timestamp': datetime(...),      # datetime object
            'direction': 'T'          # raw enum value from log
        }
    """
    # Strip whitespace
    line = raw_line.strip()
    if not line:
        return None
        
    # Skip header lines - optimized for performance
    # Check first character for quick rejection of header lines
    first_char = line[0] if line else ''
    if first_char in ('C', '-') or (first_char.isalpha() and 'Identifier' in line):
        return None
    
    try:
        # Use pre-compiled regex for maximum performance
        match = _COMPILED_REGEX.match(line)
        
        if not match:
            return None
            
        groups = match.groupdict()
        
        # Parse and convert channel to int
        channel = int(groups['channel'])
        
        # Identifier as uppercase hex string
        identifier = groups['identifier'].upper()
        
        # Flag field (can be empty)
        flag = groups['flag'] if groups['flag'] else ''
        
        # Parse and convert DLC to int
        dlc = int(groups['dlc'])
        
        # Optimize data bytes processing - single pass operation
        data_raw = groups['data']
        if data_raw:
            data = ' '.join(data_raw.upper().split())
        else:
            data = ''
        
        # Parse timestamp as float and convert to datetime
        timestamp_float = float(groups['timestamp'])

        # Return raw direction enum value from log (don't convert to display name)
        direction = groups['direction']  # Keep "T" or "R" as raw value
        
        # Return fully converted values ready for display
        result = {
            'channel': channel,           # int
            'identifier': identifier,     # string (hex)
            'flag': flag,                # string (flag character)
            'dlc': dlc,                  # int
            'data': data,                # string (formatted hex)
            'timestamp': timestamp_float,       # datetime object
            'direction': direction        # raw enum value ("T" or "R")
        }
        return result
        
    except Exception as e:
        # Debug: you can uncomment this to see parsing errors
        logger.debug(f"Parse error for line '{line}': {e}")
        return None
