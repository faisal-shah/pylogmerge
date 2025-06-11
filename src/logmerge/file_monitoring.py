"""
File Monitoring - Live log file monitoring and parsing

Contains components for monitoring log files in real-time, including worker threads,
file state tracking, and parsing statistics.
"""

import os
import time
import threading
from typing import List, Optional, Dict, Any
from datetime import datetime
from PyQt5.QtCore import QThread

from .data_structures import LogEntry, SharedLogBuffer
from .plugin_utils import LogParsingPlugin
from .parsing_utils import parse_line_with_regex
from .logging_config import get_logger


# ============================================================================
# FILE MONITORING CONSTANTS
# ============================================================================

# Threading & Performance Constants
DEFAULT_SHARED_BUFFER_SIZE = 10000
DEFAULT_POLL_INTERVAL_SECONDS = 1.0
DEFAULT_BATCH_SIZE = 100
WORKER_POLL_INTERVAL_MS = 1000  # msleep interval

# File Operations Constants
DEFAULT_FILE_ENCODING = "utf-8"
DEFAULT_FILE_ERROR_HANDLING = "ignore"


# ============================================================================
# FILE MONITORING CLASSES
# ============================================================================


class FileMonitorState:
    """State for monitoring a single log file."""

    def __init__(self, file_path: str):
        self.file_path = file_path
        self.last_position = 0  # Last read position in file
        self.last_size = 0
        self.last_modified = 0
        self.total_lines = 0
        self.parsed_lines = 0
        self.dropped_lines = 0
        self.is_complete = False
        self.file_handle = None


class LogParsingWorker(QThread):
    """Background thread for live log file monitoring and parsing."""

    def __init__(
        self, schema: LogParsingPlugin, shared_buffer: SharedLogBuffer, parent=None
    ):
        super().__init__(parent)
        self.logger = get_logger(__name__)
        self.schema = schema
        self.shared_buffer = shared_buffer
        self.monitored_files = {}  # file_path -> FileMonitorState
        self.file_list_lock = threading.Lock()
        self.should_stop = False
        self.poll_interval = DEFAULT_POLL_INTERVAL_SECONDS  # seconds
        self.batch_size = DEFAULT_BATCH_SIZE  # entries per batch

        # Set up the parsing function - use custom function if available, otherwise use regex
        if self.schema.parse_function:
            self.parse_function = self.schema.parse_function
        else:
            self.parse_function = self._parse_line_with_regex

    def stop(self):
        """Stop the monitoring thread."""
        self.should_stop = True

    def update_file_list(self, file_paths: List[str]):
        """Update the complete list of files to monitor (thread-safe)."""
        with self.file_list_lock:
            # Close file handles for files no longer in the list
            for file_path in list(self.monitored_files.keys()):
                if file_path not in file_paths:
                    state = self.monitored_files[file_path]
                    if state.file_handle:
                        state.file_handle.close()
                        state.file_handle = None
                    del self.monitored_files[file_path]

            # Add new files to monitoring
            for file_path in file_paths:
                if file_path not in self.monitored_files:
                    state = FileMonitorState(file_path)
                    self.monitored_files[file_path] = state

    def run(self):
        """Main polling loop for file monitoring."""
        batch = []

        while not self.should_stop:
            try:
                # Get a local copy of monitored files for thread safety
                with self.file_list_lock:
                    files_to_check = list(self.monitored_files.items())

                # Check all monitored files for changes
                for file_path, state in files_to_check:
                    new_entries = self._check_file_for_new_lines(file_path, state)
                    batch.extend(new_entries)

                    # Batch processing - add to shared buffer every batch_size entries
                    if len(batch) >= self.batch_size:
                        self.shared_buffer.add_entries(batch)
                        batch = []

                # Add remaining entries to buffer
                if batch:
                    self.shared_buffer.add_entries(batch)
                    batch = []

            except Exception as e:
                # Log error internally - no signal emit
                self.logger.error(f"Monitoring error: {str(e)}")

            # Sleep until next poll
            self.msleep(int(self.poll_interval * 1000))

    def _check_file_for_new_lines(
        self, file_path: str, state: FileMonitorState
    ) -> List[LogEntry]:
        """Check file for new lines since last read."""
        new_entries = []

        try:
            # Check if file exists and get current stats
            if not os.path.exists(file_path):
                return new_entries

            file_stat = os.stat(file_path)
            current_size = file_stat.st_size
            current_modified = file_stat.st_mtime

            # Check if file has been modified or grown
            if (
                current_modified <= state.last_modified
                and current_size <= state.last_size
            ):
                return new_entries

            start_time = time.perf_counter()
            # File has changed - read new content
            if not state.file_handle:
                state.file_handle = open(
                    file_path,
                    "r",
                    encoding=DEFAULT_FILE_ENCODING,
                    errors=DEFAULT_FILE_ERROR_HANDLING,
                )
                state.file_handle.seek(state.last_position)

            # Read new lines
            new_lines = state.file_handle.readlines()

            for line in new_lines:
                # Increment line counter
                state.total_lines += 1
                line_number = state.total_lines

                log_entry = self._parse_line(file_path, line_number, line)
                if log_entry:
                    state.parsed_lines += 1
                    new_entries.append(log_entry)
                else:
                    state.dropped_lines += 1

            # Update position tracking
            state.last_position = state.file_handle.tell()
            state.last_size = current_size
            state.last_modified = current_modified

            execution_time = time.perf_counter() - start_time
            self.logger.debug(
                f"Processed {len(new_entries)} new entries from {file_path} in {execution_time:.6f} seconds"
            )

        except Exception as e:
            self.logger.error(f"Error monitoring file {file_path}: {str(e)}")
            # Close and reset file handle on error
            if state.file_handle:
                state.file_handle.close()
                state.file_handle = None

        return new_entries

    def _parse_line_with_regex(self, raw_line: str) -> Optional[Dict[str, Any]]:
        """Parse a single log line using the compiled regex pattern and convert field values.

        Args:
            raw_line: The raw log line to parse

        Returns:
            Dictionary with parsed and converted field values (ready for display), or None if parsing fails
        """
        return parse_line_with_regex(raw_line, self.schema)

    def _parse_line(
        self, file_path: str, line_number: int, raw_line: str
    ) -> Optional[LogEntry]:
        """Parse a single log line and create a LogEntry.

        Args:
            file_path: Path to the source file
            line_number: Line number in the file
            raw_line: The raw log line to parse

        Returns:
            LogEntry object or None if parsing fails
        """
        try:
            # Use the configured parse function (both return fully converted field values)
            parsed_fields = self.parse_function(raw_line)
            if parsed_fields is None or not isinstance(parsed_fields, dict):
                return None

            # Extract timestamp from the designated timestamp field
            # Parsers return datetime objects for epoch/strptime fields, or float for float_timestamp fields
            timestamp = parsed_fields.get(self.schema.timestamp_field, None)

            # Use current time if no timestamp found
            if timestamp is None:
                timestamp = datetime.now()

            return LogEntry(
                file_path=file_path,
                line_number=line_number,
                timestamp=timestamp,
                fields=parsed_fields,
                raw_line=raw_line,
            )

        except Exception:
            return None
