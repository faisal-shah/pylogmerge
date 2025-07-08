"""
LogMerge - A GUI application for viewing and analyzing multiple log files

LogMerge provides advanced filtering and merging capabilities for multiple log files
with real-time monitoring, customizable parsing plugins, and an intuitive Qt-based interface.

Key Features:
- Multi-file log viewing with real-time updates
- Plugin-based parsing system for different log formats
- Advanced filtering and search capabilities
- Color-coded file identification
- Live log monitoring with follow mode
- Configurable column display and ordering

Example:
    Basic usage:
    >>> import logmerge
    >>> logmerge.main()

    Or from command line:
    $ logmerge
"""

__version__ = "0.2.0"
__author__ = "Faisal Shah"
__email__ = "faisal.shah@gmail.com"

# Core imports for package functionality
from .data_structures import LogEntry, SharedLogBuffer
from .plugin_utils import LogParsingPlugin
from .parsing_utils import parse_line_with_regex, convert_field_value
from .file_monitoring import LogParsingWorker, FileMonitorState

# Main application entry point
from .main import main

__all__ = [
    # Version and metadata
    "__version__",
    "__author__",
    "__email__",
    # Core data structures
    "LogEntry",
    "SharedLogBuffer",
    # Plugin system
    "LogParsingPlugin",
    # Parsing utilities
    "parse_line_with_regex",
    "convert_field_value",
    # File monitoring
    "LogParsingWorker",
    "FileMonitorState",
    # Main application
    "main",
]
