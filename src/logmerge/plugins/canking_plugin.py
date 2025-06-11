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
    "timestamp_field": "timestamp",
    "fields": [
        {"name": "chn", "type": "int"},
        {"name": "identifier", "type": "int", "is_discrete": True},
        {"name": "flg", "type": "string", "is_discrete": True},
        {"name": "dlc", "type": "int", "is_discrete": True},
        {"name": "data", "type": "string", "is_discrete": False},
        {
            "name": "timestamp",
            "type": "float_timestamp",
        },
        {
            "name": "dir",
            "type": "enum",
            "enum_values": [
                {"value": "T", "name": "TRANSMIT"},
                {"value": "R", "name": "RECEIVE"},
            ],
        },
    ],
}


def parse_raw_line(line: str) -> Optional[Dict[str, Any]]:
    """Fastest parser with header/error handling."""

    if line.endswith("\n"):
        line = line[:-1]

    parts = line.split()

    # Quick header check
    if len(parts) < 5 or not parts[0].isdigit():
        return None  # Skip headers/invalid lines

    try:
        field_offset = 0
        chn = int(parts[0])
        identifier = int(parts[1], 16)

        if len(parts[2]) == 1 and ord(parts[2]) > 57:  # > '9'
            flg = parts[2]
            field_offset = 1
        else:
            flg = None

        dlc = int(parts[2 + field_offset])
        data_start = 3 + field_offset
        data_end = data_start + dlc
        data_string = " ".join(parts[data_start:data_end])

        return {
            "chn": chn,
            "identifier": identifier,
            "flg": flg,
            "dlc": dlc,
            "data": data_string,
            "timestamp": float(parts[-2]),
            "dir": parts[-1],
        }
    except (ValueError, IndexError):
        logger.debug("Malformed line")
        return None  # Skip malformed lines
