#!/usr/bin/env python3
"""
CAN King Log Plugin for Merged Log Viewer

This plugin defines the schema for parsing CAN King log files.
The log format contains CAN bus messages with identifiers, data, timestamps, and direction.

Example log format:
Chn Identifier Flg   DLC  D0...1...2...3...4...5...6..D7       Time     Dir
 0    0000014B         1  00                                1675.570498 T
 0    00000065         5  01  00  00  00  00                1675.572378 T
"""

import re
from datetime import datetime, timedelta
from typing import Dict, Optional, Any

# Import logging from parent package
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from logging_config import get_logger

# Get logger for this plugin
logger = get_logger(__name__)


# Schema definition for CAN King log format
SCHEMA = {
    "regex": r"^\s*(?P<channel>\d+)\s+(?P<identifier>[0-9A-Fa-f]+)\s+(?P<dlc>\d+)\s+(?P<data>(?:[0-9A-Fa-f]{2}(?:\s+[0-9A-Fa-f]{2})*)?)\s+(?P<timestamp>\d+\.\d+)\s+(?P<direction>[TR])\s*$",
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
            "type": "epoch"
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


def parse_raw_line(raw_line: str) -> Optional[Dict[str, Any]]:
    """
    Custom parsing function for CAN King log lines.
    
    This function parses CAN bus log lines and returns a dictionary with field values
    fully converted and ready for display.
    
    Args:
        raw_line: The raw log line to parse
        
    Returns:
        Dictionary with fully converted field values (ready for display), or None if parsing fails
        
    Example log line:
        " 0    0000014B         1  00                                1675.570498 T"        Expected return:
        {
            'channel': 0,                    # int
            'identifier': '0000014B',        # string (hex ID)
            'dlc': 1,                        # int (data length)
            'data': '00',                    # string (hex data bytes)
            'timestamp': datetime(...),      # datetime object
            'direction': 'TRANSMIT'          # enum converted to string name
        }
    """
    # Strip whitespace
    line = raw_line.strip()
    if not line:
        return None
        
    # Skip header lines
    if line.startswith('Chn') or line.startswith('---') or 'Identifier' in line:
        return None
    
    try:
        # Use the regex pattern from SCHEMA to avoid duplication
        pattern = SCHEMA["regex"]
        match = re.match(pattern, line)
        
        if not match:
            return None
            
        groups = match.groupdict()
        
        # Parse and convert channel to int
        channel = int(groups['channel'])
        
        # Identifier as uppercase hex string
        identifier = groups['identifier'].upper()
        
        # Parse and convert DLC to int
        dlc = int(groups['dlc'])
        
        # Clean up data bytes - remove extra spaces and format consistently
        data_raw = groups['data'] if groups['data'] else ''
        if data_raw:
            data_raw = data_raw.strip()
            # Split by whitespace and rejoin with single spaces
            data_bytes = data_raw.split()
            data = ' '.join(byte.upper() for byte in data_bytes)
        else:
            data = ''
        
        # Parse timestamp as float and convert to datetime
        timestamp_float = float(groups['timestamp'])
        # The CAN King log appears to use relative timestamps (e.g., 1675.570498 seconds)
        # Since these are not Unix timestamps, we'll add them to a reasonable base time
        # Using the current date as base time for demonstration
        base_time = datetime(2025, 6, 11, 0, 0, 0)  # Adjust this base time as needed
        timestamp = base_time + timedelta(seconds=timestamp_float)
        
        # Convert direction enum
        direction_char = groups['direction']
        direction_field = next((field for field in SCHEMA['fields'] if field['name'] == 'direction'), None)
        if direction_field and direction_field['type'] == 'enum':
            enum_values = direction_field.get('enum_values', [])
            direction_enum_map = {item['value']: item['name'] for item in enum_values}
            direction = direction_enum_map.get(direction_char, direction_char)
        else:
            direction = direction_char  # Fallback
        
        # Return fully converted values ready for display
        result = {
            'channel': channel,           # int
            'identifier': identifier,     # string (hex)
            'dlc': dlc,                  # int
            'data': data,                # string (formatted hex)
            'timestamp': timestamp,       # datetime object
            'direction': direction        # enum string
        }
        return result
        
    except Exception as e:
        # Debug: you can uncomment this to see parsing errors
        logger.debug(f"Parse error for line '{line}': {e}")
        return None
