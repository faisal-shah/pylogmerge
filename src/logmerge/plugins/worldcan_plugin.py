"""
WorldCAN Log Plugin for Merged Log Viewer

This plugin defines the schema for parsing WorldCAN log files.
The log format contains JSON lines with CAN frame data and WorldCAN protocol information.

Example log format:
{"can_frame": {"canid": 134286341, "data": [251], "timestamp": 57728.35031, "interface": "3"}, "worldcan": {"cmd": 5, "src": 12, "dst": 1, "payload": [251], "broadcast": true, "cmd_name": "CAN_ID_BRDCST_1553", "CAN_ID_BRDCST_1553": {"payload": [251]}}}
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Any

# Import logging from parent package
sys.path.insert(0, str(Path(__file__).parent.parent))
from logging_config import get_logger

# Get logger for this plugin
logger = get_logger(__name__)

# Schema definition for WorldCAN log format
SCHEMA = {
    "timestamp_field": "timestamp",
    "fields": [
        {"name": "cmd", "type": "int", "is_discrete": True},
        {"name": "src", "type": "int", "is_discrete": True},
        {"name": "dst", "type": "int", "is_discrete": True},
        {"name": "payload", "type": "string", "is_discrete": False},
        {"name": "cmd_name", "type": "string", "is_discrete": True},
        {"name": "timestamp", "type": "epoch"},
    ],
}


def parse_raw_line(line: str) -> Optional[Dict[str, Any]]:
    """Parse JSON WorldCAN log line and extract worldcan data."""

    if line.endswith("\n"):
        line = line[:-1]

    # Skip empty lines
    if not line.strip():
        return None

    try:
        # Parse JSON line
        log_data = json.loads(line)

        # Check if this is a WorldCAN log entry
        if "worldcan" not in log_data or "can_frame" not in log_data:
            logger.debug("Line missing worldcan or can_frame data")
            return None

        worldcan_data = log_data["worldcan"]
        can_frame_data = log_data["can_frame"]

        # Extract required fields from worldcan data
        cmd = worldcan_data.get("cmd")
        src = worldcan_data.get("src")
        dst = worldcan_data.get("dst")
        payload_list = worldcan_data.get("payload", [])
        cmd_name = worldcan_data.get("cmd_name", "")

        # Convert payload list to space-separated hex string
        if isinstance(payload_list, list):
            payload_hex = " ".join(f"{byte:02X}" for byte in payload_list)
        else:
            payload_hex = ""

        # Get timestamp from can_frame
        timestamp = can_frame_data.get("timestamp")
        if timestamp is None:
            logger.debug("Missing timestamp in can_frame")
            return None

        # Convert timestamp to datetime (assuming it's already in epoch seconds)
        try:
            timestamp_dt = datetime.fromtimestamp(float(timestamp))
        except (ValueError, TypeError):
            logger.debug(f"Invalid timestamp: {timestamp}")
            return None

        return {
            "cmd": cmd,
            "src": src,
            "dst": dst,
            "payload": payload_hex,
            "cmd_name": cmd_name,
            "timestamp": timestamp_dt,
        }

    except json.JSONDecodeError as e:
        logger.debug(f"JSON decode error: {e}")
        return None
    except (KeyError, TypeError, ValueError) as e:
        logger.debug(f"Data extraction error: {e}")
        return None


def test_parsing():
    """Test function to verify the parsing works correctly."""
    test_line = '{"can_frame": {"canid": 134286341, "data": [251], "timestamp": 57728.35031, "interface": "3"}, "worldcan": {"cmd": 5, "src": 12, "dst": 1, "payload": [251], "broadcast": true, "cmd_name": "CAN_ID_BRDCST_1553", "CAN_ID_BRDCST_1553": {"payload": [251]}}}'

    result = parse_raw_line(test_line)
    if result:
        print("Test parsing successful:")
        print(f"  cmd: {result['cmd']}")
        print(f"  src: {result['src']}")
        print(f"  dst: {result['dst']}")
        print(f"  payload: {result['payload']}")
        print(f"  cmd_name: {result['cmd_name']}")
        print(f"  timestamp: {result['timestamp']}")
    else:
        print("Test parsing failed")


if __name__ == "__main__":
    test_parsing()
