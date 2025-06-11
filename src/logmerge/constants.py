"""Application constants for essential shared values."""

from PyQt5.QtGui import QColor

# Core performance and threading
BUFFER_DRAIN_INTERVAL_MS = 500
THREAD_SHUTDOWN_TIMEOUT_MS = 3000
THREAD_FORCE_TERMINATE_TIMEOUT_MS = 1000

# File colors for log sources
DEFAULT_FILE_COLORS = [
    QColor(255, 99, 71),  # Tomato
    QColor(60, 179, 113),  # Medium Sea Green
    QColor(30, 144, 255),  # Dodger Blue
    QColor(255, 165, 0),  # Orange
    QColor(138, 43, 226),  # Blue Violet
    QColor(220, 20, 60),  # Crimson
    QColor(0, 191, 255),  # Deep Sky Blue
    QColor(255, 20, 147),  # Deep Pink
]
COLOR_LIGHTEN_FACTOR = 0.9

# UI layout
MAIN_WINDOW_DEFAULT_GEOMETRY = (100, 100, 1200, 800)
PANEL_MIN_WIDTH = 250
PANEL_MAX_WIDTH = 400
SIDEBAR_CONTENT_MARGINS = (5, 5, 5, 5)
FILE_ITEM_CONTENT_MARGINS = (5, 2, 5, 2)
COLOR_INDICATOR_SIZE = (16, 16)

# Core UI text that appears in multiple places
WINDOW_TITLE = "Merged Log Viewer"
LOG_FILES_TITLE = "Log Files"
FILTERS_TITLE = "Filters"
FOLLOW_ACTION_TEXT = "▼ Follow"
COLUMN_CONFIG_ACTION_TEXT = "⚙ Configure Columns"

# Essential status and error message formats
READY_STATUS = "Ready - add log files to begin"
FILE_COUNT_STATUS_FORMAT = "Files: {total} total, {selected} selected"
PROCESSING_ENTRIES_FORMAT = "Processing {count} entries..."
BUFFER_DRAINED_FORMAT = "Buffer drained with {count} entries in {time:.3f} seconds"
BUFFER_EMPTY_MESSAGE = "Buffer empty - no entries to process"
NO_SHARED_BUFFER_MESSAGE = "No shared buffer"
SCHEMA_LOAD_ERROR_FORMAT = "Failed to load schema file:\n{error}"

# Style templates that need dynamic content
COLOR_INDICATOR_STYLE_TEMPLATE = """
QLabel {{
    background-color: {color};
    border: 1px solid #666;
    border-radius: 3px;
}}
"""
TITLE_LABEL_STYLE = "font-weight: bold; font-size: 14px; margin-bottom: 5px;"
