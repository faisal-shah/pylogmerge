#!/usr/bin/env python3
"""
Syslog Plugin for Merged Log Viewer

This plugin defines the schema for parsing standard syslog format files.
The log format contains timestamp, hostname, process/facility, and message components.

Note, the standard syslog format does not include the year in the timestamp. It will default to 1900 *shrug*.

Example log format:
Jul  8 08:41:15 THISHOST kernel: [    3.469942] misc dxg: dxgkio_is_feature_enabled: Ioctl failed: -22
Jul  8 08:42:00 THISHOST kernel: [   49.173417] hv_balloon: Max. dynamic memory size: 16214 MB
"""

# Schema definition for syslog format
SCHEMA = {
    "regex": r"^(?P<timestamp>\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})\s+(?P<hostname>\S+)\s+(?P<process>[^:\[]+)(?:\[(?P<pid>\d+)\])?:\s*(?P<message>.*)$",
    "timestamp_field": "timestamp",
    "fields": [
        {"name": "timestamp", "type": "strptime", "strptime_fmt": "%b %d %H:%M:%S"},
        {"name": "hostname", "type": "string", "is_discrete": True},
        {"name": "process", "type": "string", "is_discrete": True},
        {"name": "pid", "type": "int", "is_discrete": True},
        {"name": "message", "type": "string", "is_discrete": False},
    ],
}
