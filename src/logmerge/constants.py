"""
Application Constants for Merged Log Viewer

This module contains all constants used throughout the application,
organized into logical groups for easy maintenance and discovery.
"""

from PyQt5.QtGui import QColor

# ============================================================================
# THREADING & PERFORMANCE CONSTANTS
# ============================================================================

BUFFER_DRAIN_INTERVAL_MS = 500  # Timer interval for draining buffer (half the file polling interval)
SCROLL_TOLERANCE_PIXELS = 1     # Tolerance for "at bottom" detection
THREAD_SHUTDOWN_TIMEOUT_MS = 3000
THREAD_FORCE_TERMINATE_TIMEOUT_MS = 1000

# ============================================================================
# COLOR CONSTANTS
# ============================================================================

DEFAULT_FILE_COLORS = [
    QColor(255, 99, 71),   # Tomato
    QColor(60, 179, 113),  # Medium Sea Green
    QColor(30, 144, 255),  # Dodger Blue
    QColor(255, 165, 0),   # Orange
    QColor(138, 43, 226),  # Blue Violet
    QColor(220, 20, 60),   # Crimson
    QColor(0, 191, 255),   # Deep Sky Blue
    QColor(255, 20, 147),  # Deep Pink
]
COLOR_LIGHTEN_FACTOR = 0.9      # Factor for lightening background colors

# ============================================================================
# UI LAYOUT CONSTANTS
# ============================================================================

MAIN_WINDOW_DEFAULT_GEOMETRY = (100, 100, 1200, 800)  # x, y, width, height
DEFAULT_SPLITTER_SIZES = [300, 900]  # Sidebar width, main view width

# Dialog Dimensions
ADD_FILES_DIALOG_SIZE = (500, 400)
FILE_DISCOVERY_DIALOG_SIZE = (600, 400)
COLUMN_CONFIG_DIALOG_SIZE = (600, 500)

# Layout Margins and Spacing
SIDEBAR_CONTENT_MARGINS = (5, 5, 5, 5)
FILE_ITEM_CONTENT_MARGINS = (5, 2, 5, 2)
ZERO_CONTENT_MARGINS = (0, 0, 0, 0)
COLOR_INDICATOR_SIZE = (16, 16)

# Panel Constants
PANEL_MIN_WIDTH = 250  # Minimum width for panels
PANEL_MAX_WIDTH = 400  # Maximum width for panels
PANEL_HEADER_HEIGHT = 40  # Height of panel headers

# ============================================================================
# STRING CONSTANTS - UI LABELS
# ============================================================================

WINDOW_TITLE = "Merged Log Viewer"
LOG_FILES_TITLE = "Log Files"
FILTERS_TITLE = "Filters"
SELECT_ALL_TEXT = "Select All"
DESELECT_ALL_TEXT = "Deselect All"
ADD_BUTTON_EMOJI = "➕"
REMOVE_BUTTON_EMOJI = "➖"
FOLLOW_ACTION_TEXT = "▼ Follow"
COLUMN_CONFIG_ACTION_TEXT = "⚙ Configure Columns"

# ============================================================================
# BUTTON LABELS
# ============================================================================

BROWSE_BUTTON_TEXT = "Browse..."
CLEAR_BUTTON_TEXT = "Clear"
BROWSE_FILES_TEXT = "Browse Files..."
PREVIEW_FILES_TEXT = "Preview Matching Files..."
ADD_SELECTED_TEXT = "Add >"
ADD_ALL_TEXT = "Add All >>"
REMOVE_SELECTED_TEXT = "< Remove"
REMOVE_ALL_TEXT = "<< Remove"
MOVE_UP_TEXT = "Move Up"
MOVE_DOWN_TEXT = "Move Down"
ADD_ALL_FILES_TEXT = "Add All Files"
CANCEL_TEXT = "Cancel"

# ============================================================================
# DIALOG TITLES
# ============================================================================

ADD_FILES_DIALOG_TITLE = "Add Log Files"
FILES_FOUND_DIALOG_TITLE = "Files Found"
COLUMN_CONFIG_DIALOG_TITLE = "Configure Columns"
REMOVE_FILES_DIALOG_TITLE = "Remove Files"
DUPLICATE_FILES_DIALOG_TITLE = "Duplicate Files"
NO_DIRECTORY_DIALOG_TITLE = "No Directory"
INVALID_REGEX_DIALOG_TITLE = "Invalid Regex"
NO_FILES_FOUND_DIALOG_TITLE = "No Files Found"
SEARCH_ERROR_DIALOG_TITLE = "Search Error"
SCHEMA_ERROR_DIALOG_TITLE = "Schema Error"

# ============================================================================
# TAB LABELS
# ============================================================================

SELECT_FILES_TAB = "Select Files"
DIRECTORY_REGEX_TAB = "Directory + Regex"

# ============================================================================
# PLACEHOLDER TEXTS
# ============================================================================

DIRECTORY_PLACEHOLDER = "Click 'Browse' to select a directory..."
REGEX_PLACEHOLDER = "Enter regex pattern (e.g., .*\\.log$)"

# ============================================================================
# TOOLTIP TEXTS
# ============================================================================

ADD_FILES_TOOLTIP = "Add log files or directory"
REMOVE_FILES_TOOLTIP = "Remove selected files"
FOLLOW_MODE_TOOLTIP = "Automatically scroll to show latest log entries"
COLUMN_CONFIG_TOOLTIP = "Configure which columns to display and their order"
ADD_COLUMNS_TOOLTIP = "Add selected columns to visible list"
ADD_ALL_COLUMNS_TOOLTIP = "Add all available columns to visible list"
REMOVE_COLUMNS_TOOLTIP = "Remove selected columns from visible list"
REMOVE_ALL_COLUMNS_TOOLTIP = "Remove all columns from visible list"
MOVE_UP_TOOLTIP = "Move selected columns up in display order"
MOVE_DOWN_TOOLTIP = "Move selected columns down in display order"
RESTORE_DEFAULTS_TOOLTIP = "Reset to show all columns in default order"

# ============================================================================
# FILE PATTERNS AND FILTERS
# ============================================================================

LOG_FILE_PATTERNS = ["*.log", "*.txt"]
PYTHON_FILE_PATTERN = "*.py"
ALL_FILES_PATTERN = "*"
LOG_FILE_FILTER = "Log files (*.log *.txt);;All files (*)"
PYTHON_FILE_FILTER = "Python files (*.py);;All files (*)"

# ============================================================================
# DEFAULT VALUES
# ============================================================================

DEFAULT_REGEX_PATTERN = ".*\\.log$"
DEFAULT_DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'
DEFAULT_STRFTIME_FORMAT = '%Y-%m-%d %H:%M:%S'
DEFAULT_RECURSIVE_SEARCH = True
DEFAULT_CHECKBOX_CHECKED = True
DEFAULT_FOLLOW_MODE = True

# Format Strings for Time Conversion
DATETIME_FORMAT_PATTERNS = {
    'YYYY': '%Y',
    'MM': '%m', 
    'DD': '%d',
    'HH': '%H',
    'mm': '%M',
    'ss': '%S'
}

# ============================================================================
# STATUS MESSAGES
# ============================================================================

READY_STATUS = "Ready - add log files to begin"
FILE_COUNT_STATUS_FORMAT = "Files: {total} total, {selected} selected"
PROCESSING_ENTRIES_FORMAT = "Processing {count} entries..."
BUFFER_DRAINED_FORMAT = "Buffer drained with {count} entries in {time:.3f} seconds"
BUFFER_EMPTY_MESSAGE = "Buffer empty - no entries to process"
NO_SHARED_BUFFER_MESSAGE = "No shared buffer"
MONITORING_ERROR_FORMAT = "Monitoring error: {error}"
FILE_PROCESSING_FORMAT = "Processed {count} new entries from {file} in {time:.6f} seconds"
FILE_MONITORING_ERROR_FORMAT = "Error monitoring file {file}: {error}"

# ============================================================================
# ERROR MESSAGES
# ============================================================================

SCHEMA_LOAD_ERROR_FORMAT = "Failed to load schema file:\n{error}"
DUPLICATE_FILE_MESSAGE_SINGLE = "File '{file}' is already in the list."
DUPLICATE_FILES_MESSAGE_MULTIPLE = "{count} files were already in the list and skipped."
REMOVE_MULTIPLE_FILES_CONFIRM = "Remove {count} selected files?"
NO_DIRECTORY_MESSAGE = "Please select a directory first."
INVALID_REGEX_MESSAGE = "Please enter a valid regex pattern."
NO_DIRECTORY_SELECT_MESSAGE = "Please select a directory."
NO_FILES_FOUND_MESSAGE = "No files found matching the specified pattern."
SEARCH_ERROR_MESSAGE_FORMAT = "Error searching for files: {error}"

# ============================================================================
# REGEX VALIDATION MESSAGES
# ============================================================================

ENTER_REGEX_MESSAGE = "Enter a regex pattern"
VALID_REGEX_MESSAGE = "✓ Valid regex pattern"
INVALID_REGEX_MESSAGE_FORMAT = "✗ Invalid regex: {error}"

# ============================================================================
# INSTRUCTIONAL TEXT
# ============================================================================

FILES_TAB_INSTRUCTIONS = "Select individual log files to add to the viewer."
DIRECTORY_TAB_INSTRUCTIONS = "Select a directory and specify a regex pattern to match log files."

COLUMN_CONFIG_INSTRUCTIONS = """
<b>Configure Visible Columns</b><br><br>
Select which columns to display in the log table and arrange their order.
Use the buttons to move columns between available and visible lists.
"""

# ============================================================================
# REGEX EXAMPLES
# ============================================================================

REGEX_EXAMPLES_HTML = """
<b>Regex Examples:</b><br>
• <code>.*\\.log$</code> - All .log files<br>
• <code>.*/error.*\\.log$</code> - Log files containing 'error' in any subdirectory<br>
• <code>^daily/.*</code> - Files only in 'daily' directory<br>
• <code>.*\\.(log|txt)$</code> - All .log and .txt files
"""

# ============================================================================
# CSS STYLES
# ============================================================================

TITLE_LABEL_STYLE = "font-weight: bold; font-size: 14px; margin-bottom: 5px;"
SUMMARY_LABEL_STYLE = "font-weight: bold; margin-bottom: 10px;"
INFO_LABEL_STYLE = "color: #666; font-size: 10px; margin-top: 10px;"
NO_FILES_STYLE = "color: #666; font-style: italic;"

COLOR_INDICATOR_STYLE_TEMPLATE = """
QLabel {{
    background-color: {color};
    border: 1px solid #666;
    border-radius: 3px;
}}
"""

# Regex Validation Styles
REGEX_VALID_STYLE = "color: green;"
REGEX_WARNING_STYLE = "color: orange;"
REGEX_ERROR_STYLE = "color: red;"
REGEX_INPUT_ERROR_STYLE = "border: 1px solid red;"
REGEX_INPUT_NORMAL_STYLE = ""

# ============================================================================
# FIELD LABELS
# ============================================================================

DIRECTORY_LABEL = "Directory:"
REGEX_PATTERN_LABEL = "Regex Pattern:"
AVAILABLE_COLUMNS_LABEL = "Available Columns:"
VISIBLE_COLUMNS_LABEL = "Visible Columns (in display order):"
FILES_TO_ADD_LABEL = "Files to be added:"

# ============================================================================
# VIRTUAL COLUMN NAMES
# ============================================================================

SOURCE_FILE_VIRTUAL_COLUMN = "Source File"

# ============================================================================
# SPECIAL DISPLAY VALUES
# ============================================================================

VIRTUAL_COLUMN_SUFFIX = " (virtual)"
TYPE_SUFFIX_FORMAT = " ({type})"
RECOMMENDED_SUFFIX = " [Recommended]"
UNRECOGNIZED_ENUM_FORMAT = "UNRECOGNIZED_{value}"

# ============================================================================
# SUMMARY TEXT FORMATS
# ============================================================================

FILES_FOUND_SUMMARY_FORMAT = "Found {count} files matching pattern '{pattern}' in directory '{directory}'"
