"""
Data Structures - Core data types and shared buffers

Contains the fundamental data structures used throughout the log viewer application,
including log entries and thread-safe buffer implementations.
"""

import threading
from collections import deque
from typing import List, Dict, Any, NamedTuple, Union
from datetime import datetime


class LogEntry(NamedTuple):
    """Represents a parsed log entry."""

    file_path: str
    line_number: int
    timestamp: Union[datetime, float]
    fields: Dict[str, Any]
    raw_line: str


class SharedLogBuffer:
    """High-performance shared buffer for log entries between threads."""

    def __init__(self, max_size: int = 10000000):
        self.buffer = deque(maxlen=max_size)
        self.lock = threading.Lock()

    def add_entries(self, entries: List[LogEntry]):
        """Add multiple entries to the buffer (thread-safe)."""
        with self.lock:
            self.buffer.extend(entries)

    def drain_entries(self) -> List[LogEntry]:
        """Remove and return all entries from buffer (thread-safe)."""
        with self.lock:
            entries = list(self.buffer)
            self.buffer.clear()
            return entries

    def size(self) -> int:
        """Get current buffer size (thread-safe)."""
        with self.lock:
            return len(self.buffer)
