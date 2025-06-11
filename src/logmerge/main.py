#!/usr/bin/env python3
"""
Merged Log Viewer - Main Application

A GUI application for viewing and analyzing multiple log files with advanced filtering
and merging capabilities.
"""

import sys
import os
import re
import threading
import time
import argparse
from pathlib import Path
from typing import List, Optional, Dict, Any, Union, NamedTuple
from datetime import datetime
from collections import deque
from .parsing_utils import parse_line_with_regex
from .plugin_utils import LogParsingPlugin
from .data_structures import LogEntry, SharedLogBuffer
from .logging_config import setup_logging, get_logger
from .file_monitoring import (
    LogParsingWorker, FileParsingStats, FileMonitorState,
    DEFAULT_SHARED_BUFFER_SIZE, DEFAULT_BATCH_SIZE, DEFAULT_FILE_ENCODING, 
    DEFAULT_FILE_ERROR_HANDLING, DEFAULT_POLL_INTERVAL_SECONDS
)
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QSplitter, QPushButton, QListWidget, QListWidgetItem, QFileDialog,
    QCheckBox, QLabel, QFrame, QMessageBox, QDialog, QTabWidget,
    QLineEdit, QTextEdit, QDialogButtonBox, QTableView, QHeaderView,
    QToolBar, QAction
)
from PyQt5.QtCore import Qt, pyqtSignal, QThread, QAbstractTableModel, QModelIndex, QVariant, QTimer
from PyQt5.QtGui import QIcon, QColor, QPalette


# ============================================================================
# APPLICATION CONSTANTS
# ============================================================================

# Threading & Performance Constants
BUFFER_DRAIN_INTERVAL_MS = 100  # Timer interval for draining buffer
SCROLL_TOLERANCE_PIXELS = 1     # Tolerance for "at bottom" detection

# Color Constants
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

# UI Layout Constants
MAIN_WINDOW_DEFAULT_GEOMETRY = (100, 100, 1200, 800)  # x, y, width, height
SIDEBAR_MIN_WIDTH = 250
SIDEBAR_MAX_WIDTH = 400
DEFAULT_SPLITTER_SIZES = [300, 900]  # Sidebar width, main view width

# Dialog Dimensions
SCHEMA_DIALOG_SIZE = (500, 400)
ADD_FILES_DIALOG_SIZE = (500, 400)
FILE_DISCOVERY_DIALOG_SIZE = (600, 400)
COLUMN_CONFIG_DIALOG_SIZE = (600, 500)

# Layout Margins and Spacing
SIDEBAR_CONTENT_MARGINS = (5, 5, 5, 5)
FILE_ITEM_CONTENT_MARGINS = (5, 2, 5, 2)
ZERO_CONTENT_MARGINS = (0, 0, 0, 0)
COLOR_INDICATOR_SIZE = (16, 16)

# Thread Shutdown Constants
THREAD_SHUTDOWN_TIMEOUT_MS = 3000
THREAD_FORCE_TERMINATE_TIMEOUT_MS = 1000

# String Constants - UI Labels
WINDOW_TITLE = "Merged Log Viewer"
LOG_FILES_TITLE = "Log Files"
SELECT_ALL_TEXT = "Select All"
DESELECT_ALL_TEXT = "Deselect All"
ADD_BUTTON_EMOJI = "➕"
REMOVE_BUTTON_EMOJI = "➖"
FOLLOW_ACTION_TEXT = "▼ Follow"
COLUMN_CONFIG_ACTION_TEXT = "⚙ Configure Columns"

# Button Labels
BROWSE_BUTTON_TEXT = "Browse..."
CLEAR_BUTTON_TEXT = "Clear"
BROWSE_FILES_TEXT = "Browse Files..."
PREVIEW_FILES_TEXT = "Preview Matching Files..."
ADD_SELECTED_TEXT = "Add >"
ADD_ALL_TEXT = "Add All >>"
REMOVE_SELECTED_TEXT = "< Remove"
REMOVE_ALL_TEXT = "<< Remove All"
MOVE_UP_TEXT = "Move Up"
MOVE_DOWN_TEXT = "Move Down"
ADD_ALL_FILES_TEXT = "Add All Files"
CANCEL_TEXT = "Cancel"

# Dialog Titles
SCHEMA_DIALOG_TITLE = "Select Log Plugin"
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

# Tab Labels
SELECT_FILES_TAB = "Select Files"
DIRECTORY_REGEX_TAB = "Directory + Regex"

# Placeholder Texts
SCHEMA_PATH_PLACEHOLDER = "No plugin file selected..."
DIRECTORY_PLACEHOLDER = "Click 'Browse' to select a directory..."
REGEX_PLACEHOLDER = "Enter regex pattern (e.g., .*\\.log$)"

# Tooltip Texts
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

# File Patterns and Filters
LOG_FILE_PATTERNS = ["*.log", "*.txt"]
PYTHON_FILE_PATTERN = "*.py"
ALL_FILES_PATTERN = "*"
LOG_FILE_FILTER = "Log files (*.log *.txt);;All files (*)"
PYTHON_FILE_FILTER = "Python files (*.py);;All files (*)"

# Default Values
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

# Status Messages
READY_STATUS = "Ready - add log files to begin"
FILE_COUNT_STATUS_FORMAT = "Files: {total} total, {selected} selected"
PROCESSING_ENTRIES_FORMAT = "Processing {count} entries..."
BUFFER_DRAINED_FORMAT = "Buffer drained with {count} entries in {time:.3f} seconds"
BUFFER_EMPTY_MESSAGE = "Buffer empty - no entries to process"
NO_SHARED_BUFFER_MESSAGE = "No shared buffer"
MONITORING_ERROR_FORMAT = "Monitoring error: {error}"
FILE_PROCESSING_FORMAT = "Processed {count} new entries from {file} in {time:.6f} seconds"
FILE_MONITORING_ERROR_FORMAT = "Error monitoring file {file}: {error}"

# Error Messages
SCHEMA_LOAD_ERROR_FORMAT = "Failed to load schema file:\n{error}"
DUPLICATE_FILE_MESSAGE_SINGLE = "File '{file}' is already in the list."
DUPLICATE_FILES_MESSAGE_MULTIPLE = "{count} files were already in the list and skipped."
REMOVE_MULTIPLE_FILES_CONFIRM = "Remove {count} selected files?"
NO_DIRECTORY_MESSAGE = "Please select a directory first."
INVALID_REGEX_MESSAGE = "Please enter a valid regex pattern."
NO_DIRECTORY_SELECT_MESSAGE = "Please select a directory."
NO_FILES_FOUND_MESSAGE = "No files found matching the specified pattern."
SEARCH_ERROR_MESSAGE_FORMAT = "Error searching for files: {error}"

# Regex Validation Messages
ENTER_REGEX_MESSAGE = "Enter a regex pattern"
VALID_REGEX_MESSAGE = "✓ Valid regex pattern"
INVALID_REGEX_MESSAGE_FORMAT = "✗ Invalid regex: {error}"

# Instructional Text
SCHEMA_INSTRUCTIONS = """
<b>Select Log Parsing Plugin</b><br><br>
Choose from the pre-installed plugins below, or browse for a custom plugin file.
Each plugin defines how to parse a specific log format.
"""

PREINSTALLED_PLUGINS_LABEL = "Pre-installed Plugins:"

FILES_TAB_INSTRUCTIONS = "Select individual log files to add to the viewer."

DIRECTORY_TAB_INSTRUCTIONS = "Select a directory and specify a regex pattern to match log files."

COLUMN_CONFIG_INSTRUCTIONS = """
<b>Configure Visible Columns</b><br><br>
Select which columns to display in the log table and arrange their order.
Use the buttons to move columns between available and visible lists.
"""

# Regex Examples
REGEX_EXAMPLES_HTML = """
<b>Regex Examples:</b><br>
• <code>.*\\.log$</code> - All .log files<br>
• <code>.*/error.*\\.log$</code> - Log files containing 'error' in any subdirectory<br>
• <code>^daily/.*</code> - Files only in 'daily' directory<br>
• <code>.*\\.(log|txt)$</code> - All .log and .txt files
"""

# CSS Styles
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

# Field Labels
DIRECTORY_LABEL = "Directory:"
REGEX_PATTERN_LABEL = "Regex Pattern:"
AVAILABLE_COLUMNS_LABEL = "Available Columns:"
VISIBLE_COLUMNS_LABEL = "Visible Columns (in display order):"
FILES_TO_ADD_LABEL = "Files to be added:"

# Virtual Column Names
SOURCE_FILE_VIRTUAL_COLUMN = "Source File"

# Special Display Values
VIRTUAL_COLUMN_SUFFIX = " (virtual)"
TYPE_SUFFIX_FORMAT = " ({type})"
RECOMMENDED_SUFFIX = " [Recommended]"
UNRECOGNIZED_ENUM_FORMAT = "UNRECOGNIZED_{value}"

# Summary Text Formats
FILES_FOUND_SUMMARY_FORMAT = "Found {count} files matching pattern '{pattern}' in directory '{directory}'"


class LogTableModel(QAbstractTableModel):
    """Table model for displaying log entries."""
    
    # Cache type constants for clear invalidation
    CACHE_DATETIME_STRINGS = 'datetime_strings'
    CACHE_FILE_COLORS = 'file_colors'
    CACHE_VISIBLE_ENTRIES = 'visible_entries'
    
    # Virtual column name for source file
    SOURCE_FILE_COLUMN = "Source File"
    
    def __init__(self, schema: LogParsingPlugin, parent=None):
        super().__init__(parent)
        self.schema = schema
        self.log_entries = []
        self.checked_files = set()
        self.visible_entries = []  # Cached filtered entries for performance
        self.cached_file_colors = {}  # Cache for lightened background colors
        self.cached_datetime_strings = {}  # Cache for formatted datetime strings
        # Column configuration - include virtual Source File column first, then schema columns
        self.visible_columns = [self.SOURCE_FILE_COLUMN] + [field['name'] for field in schema.fields]
    
    # Unified Cache Management Methods
    def _invalidate_cache(self, cache_types=None):
        """
        Invalidate specified caches or all caches if none specified.
        
        Args:
            cache_types: List of cache type constants to invalidate, or None for all
        """
        if cache_types is None:
            # Invalidate all caches
            cache_types = [self.CACHE_DATETIME_STRINGS, self.CACHE_FILE_COLORS, self.CACHE_VISIBLE_ENTRIES]
        
        for cache_type in cache_types:
            if cache_type == self.CACHE_DATETIME_STRINGS:
                self.cached_datetime_strings.clear()
            elif cache_type == self.CACHE_FILE_COLORS:
                self.cached_file_colors.clear()
            elif cache_type == self.CACHE_VISIBLE_ENTRIES:
                self._rebuild_visible_entries()
    
    def _invalidate_display_caches(self):
        """Invalidate caches that affect display rendering (colors and datetime formatting)."""
        self._invalidate_cache([self.CACHE_DATETIME_STRINGS, self.CACHE_FILE_COLORS])
    
    def _invalidate_structure_caches(self):
        """Invalidate caches that depend on data structure (entries and datetime formatting)."""
        self._invalidate_cache([self.CACHE_DATETIME_STRINGS, self.CACHE_VISIBLE_ENTRIES])
        
    def _invalidate_all_caches(self):
        """Invalidate all caches - use when major changes occur."""
        self._invalidate_cache()  # No arguments = all caches
    
    def update_checked_files(self, checked_files: List[str]):
        """Update which files should be displayed."""
        self.checked_files = set(checked_files)
        # Invalidate caches that depend on visible entries structure
        self._invalidate_structure_caches()
        self.beginResetModel()
        self.endResetModel()
        
    def _rebuild_visible_entries(self):
        """Rebuild the cached visible entries list based on checked files."""
        self.visible_entries = [entry for entry in self.log_entries 
                              if entry.file_path in self.checked_files]
        
    def add_log_entry(self, entry: LogEntry):
        """Add a new log entry using binary search for optimal insertion."""
        # Use binary search to find insertion position
        insert_index = self._binary_search_insert_position(entry.timestamp)
        
        # Add to log entries
        self.log_entries.insert(insert_index, entry)
        
        # Invalidate datetime cache since entry IDs may shift
        self._invalidate_cache([self.CACHE_DATETIME_STRINGS])
        
        # Update visible entries if this entry should be visible
        if entry.file_path in self.checked_files:
            # Find insertion position in visible entries
            visible_insert_index = self._binary_search_visible_insert_position(entry.timestamp)
            
            # Notify Qt about the insertion in visible entries space
            self.beginInsertRows(QModelIndex(), visible_insert_index, visible_insert_index)
            self.visible_entries.insert(visible_insert_index, entry)
            self.endInsertRows()
        # If entry is not visible, no Qt notification needed
        
    def add_entries_batch(self, entries: List[LogEntry]):
        """Add multiple log entries efficiently using optimized merging."""
        if not entries:
            return
            
        # Sort the new entries by timestamp first
        sorted_entries = sorted(entries, key=lambda entry: entry.timestamp)
        
        # For any reasonable batch size, use reset model for simplicity and correctness
        # This avoids complex index calculations between log_entries and visible_entries
        self.beginResetModel()
        
        # Add to full log entries list
        self.log_entries.extend(sorted_entries)
        self.log_entries.sort(key=lambda entry: entry.timestamp)
        
        # Invalidate structure caches as we have new entries
        self._invalidate_structure_caches()
        
        self.endResetModel()
    
    def _binary_search_insert_position(self, timestamp: datetime) -> int:
        """Find the position where a timestamp should be inserted to maintain sort order."""
        left, right = 0, len(self.log_entries)
        
        while left < right:
            mid = (left + right) // 2
            if self.log_entries[mid].timestamp <= timestamp:
                left = mid + 1
            else:
                right = mid
        
        return left
    
    def _binary_search_visible_insert_position(self, timestamp: datetime) -> int:
        """Find the position where a timestamp should be inserted in visible entries."""
        left, right = 0, len(self.visible_entries)
        
        while left < right:
            mid = (left + right) // 2
            if self.visible_entries[mid].timestamp <= timestamp:
                left = mid + 1
            else:
                right = mid
        
        return left
        
    def clear_entries(self):
        """Clear all log entries."""
        self.beginResetModel()
        self.log_entries.clear()
        self.visible_entries.clear()
        # Clear all caches since all entries are gone
        self._invalidate_all_caches()
        self.endResetModel()
        
    def rowCount(self, parent=QModelIndex()):
        """Return number of visible rows."""
        # Use cached visible entries for O(1) performance
        return len(self.visible_entries)
        
    def columnCount(self, parent=QModelIndex()):
        """Return number of visible columns."""
        return len(self.visible_columns)
        
    def headerData(self, section, orientation, role=Qt.DisplayRole):
        """Return header data."""
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            if 0 <= section < len(self.visible_columns):
                return self.visible_columns[section]
        return None
        
    def data(self, index, role=Qt.DisplayRole):
        """Return data for a cell."""
        if not index.isValid():
            return None
            
        # Use cached visible entries for O(1) performance
        if not (0 <= index.row() < len(self.visible_entries)):
            return None
            
        entry = self.visible_entries[index.row()]
        field_name = self.visible_columns[index.column()]
        
        if role == Qt.DisplayRole:
            # Handle virtual Source File column
            if field_name == self.SOURCE_FILE_COLUMN:
                return Path(entry.file_path).name
            
            # Handle schema fields
            value = entry.fields.get(field_name, '')
            if isinstance(value, datetime):
                # Use cached datetime formatting for performance
                cache_key = (id(entry), field_name)
                if cache_key in self.cached_datetime_strings:
                    return self.cached_datetime_strings[cache_key]
                
                # Format and cache the datetime string
                formatted_str = value.strftime('%Y-%m-%d %H:%M:%S')
                self.cached_datetime_strings[cache_key] = formatted_str
                return formatted_str
            return str(value)
        elif role == Qt.UserRole:
            # Handle virtual Source File column
            if field_name == self.SOURCE_FILE_COLUMN:
                return Path(entry.file_path).name
            
            # Return raw datetime object for future filtering/sorting operations
            value = entry.fields.get(field_name, '')
            return value
        elif role == Qt.BackgroundRole:
            # Color rows by file - find the file's color from sidebar
            return self._get_file_color(entry.file_path)
            
        return None
        
    def _get_file_color(self, file_path: str):
        """Get the background color for a file path."""
        # Check cache first
        if file_path in self.cached_file_colors:
            return self.cached_file_colors[file_path]
            
        # Calculate and cache the lightened color
        if hasattr(self, 'file_colors') and file_path in self.file_colors:
            color = self.file_colors[file_path]
            # Return a very light version of the color for background
            # Convert float calculations to integers
            red = int(color.red() + (255 - color.red()) * COLOR_LIGHTEN_FACTOR)
            green = int(color.green() + (255 - color.green()) * COLOR_LIGHTEN_FACTOR)
            blue = int(color.blue() + (255 - color.blue()) * COLOR_LIGHTEN_FACTOR)
            lightened_color = QColor(red, green, blue)
            
            # Cache the result
            self.cached_file_colors[file_path] = lightened_color
            return lightened_color
        
        return None
    
    def update_file_colors(self, file_colors: Dict[str, QColor]):
        """Update file colors and clear the cache."""
        self.file_colors = file_colors
        self._invalidate_cache([self.CACHE_FILE_COLORS])  # Clear file color cache when colors change
    
    def update_column_configuration(self, visible_columns: List[str]):
        """Update which columns are visible and their order."""
        # Validate that all column names exist in schema or are virtual columns
        valid_columns = []
        schema_field_names = {field['name'] for field in self.schema.fields}
        # Add virtual columns
        virtual_columns = {self.SOURCE_FILE_COLUMN}
        allowed_columns = schema_field_names | virtual_columns
        
        for column_name in visible_columns:
            if column_name in allowed_columns:
                valid_columns.append(column_name)
        
        if valid_columns != self.visible_columns:
            self.beginResetModel()
            self.visible_columns = valid_columns
            # Clear datetime cache since column structure changed
            self._invalidate_cache([self.CACHE_DATETIME_STRINGS])
            self.endResetModel()
    
    def get_column_configuration(self) -> List[str]:
        """Return the current visible columns configuration."""
        return self.visible_columns.copy()


class SchemaSelectionDialog(QDialog):
    """Dialog for selecting a log schema file."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = get_logger(__name__)
        self.selected_schema_path = None
        self.preinstalled_plugins = self.discover_preinstalled_plugins()
        self.setup_ui()
        
    def discover_preinstalled_plugins(self) -> List[Dict[str, str]]:
        """Discover preinstalled plugins in the logmerge.plugins package."""
        plugin_list = []
        
        try:
            # Get the plugins directory path
            from . import plugins
            plugins_path = Path(plugins.__file__).parent
            
            # Find all Python files in the plugins directory (except __init__.py)
            for plugin_file in plugins_path.glob("*.py"):
                if plugin_file.name != "__init__.py":
                    plugin_info = {
                        'name': plugin_file.stem.replace('_plugin', '').replace('_', ' ').title(),
                        'path': str(plugin_file),
                        'description': f"Plugin for {plugin_file.stem.replace('_plugin', '').replace('_', ' ')} format"
                    }
                    plugin_list.append(plugin_info)
                    
        except Exception as e:
            self.logger.warning(f"Could not discover preinstalled plugins: {e}")
            
        return plugin_list
        
    def setup_ui(self):
        """Set up the dialog UI."""
        self.setWindowTitle(SCHEMA_DIALOG_TITLE)
        self.setModal(True)
        self.resize(*SCHEMA_DIALOG_SIZE)
        
        layout = QVBoxLayout()
        
        # Instructions
        instructions = QLabel(SCHEMA_INSTRUCTIONS)
        instructions.setWordWrap(True)
        layout.addWidget(instructions)
        
        # Pre-installed plugins section
        if self.preinstalled_plugins:
            plugins_label = QLabel(PREINSTALLED_PLUGINS_LABEL)
            plugins_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
            layout.addWidget(plugins_label)
            
            # Plugin list
            self.plugin_list = QListWidget()
            self.plugin_list.setSelectionMode(QListWidget.SingleSelection)
            
            for plugin in self.preinstalled_plugins:
                item = QListWidgetItem(plugin['name'])
                item.setData(Qt.UserRole, plugin['path'])
                item.setToolTip(f"{plugin['description']}\n\nPath: {plugin['path']}")
                self.plugin_list.addItem(item)
            
            self.plugin_list.itemSelectionChanged.connect(self.on_plugin_selection_changed)
            self.plugin_list.itemDoubleClicked.connect(self.on_plugin_double_clicked)
            layout.addWidget(self.plugin_list)
        else:
            # Fallback to file browser if no preinstalled plugins found
            warning_label = QLabel("No preinstalled plugins found. Please browse for a plugin file.")
            warning_label.setStyleSheet("color: orange; font-weight: bold;")
            layout.addWidget(warning_label)
            
            # Schema file selection
            file_layout = QHBoxLayout()
            self.schema_path_edit = QLineEdit()
            self.schema_path_edit.setReadOnly(True)
            self.schema_path_edit.setPlaceholderText(SCHEMA_PATH_PLACEHOLDER)
            file_layout.addWidget(self.schema_path_edit)
            
            browse_btn = QPushButton(BROWSE_BUTTON_TEXT)
            browse_btn.clicked.connect(self.browse_schema_file)
            file_layout.addWidget(browse_btn)
            layout.addLayout(file_layout)
        
        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        
        # Add Browse button on the left side
        if self.preinstalled_plugins:
            browse_button = button_box.addButton("Browse...", QDialogButtonBox.ActionRole)
            browse_button.clicked.connect(self.browse_schema_file)
        
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        self.ok_button = button_box.button(QDialogButtonBox.Ok)
        self.ok_button.setEnabled(False)
        layout.addWidget(button_box)
        
        self.setLayout(layout)
        
    def on_plugin_selection_changed(self):
        """Handle plugin selection change."""
        selected_items = self.plugin_list.selectedItems()
        if not selected_items:
            self.ok_button.setEnabled(False)
            return
            
        item = selected_items[0]
        plugin_path = item.data(Qt.UserRole)
        
        # Set selected plugin path and enable OK
        self.selected_schema_path = plugin_path
        self.ok_button.setEnabled(True)
            
    def on_plugin_double_clicked(self, item):
        """Handle double-click on plugin item."""
        plugin_path = item.data(Qt.UserRole)
        
        # Accept the selection for preinstalled plugins
        self.selected_schema_path = plugin_path
        self.accept()
        
    def browse_schema_file(self):
        """Browse for plugin file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "Select Log Plugin File", 
            "", 
            PYTHON_FILE_FILTER
        )
        
        if file_path:
            # Set the selected plugin path and immediately accept the dialog
            self.selected_schema_path = file_path
            self.accept()  # Close the dialog and proceed
            
            # If we have the text edit (fallback mode), update it
            if hasattr(self, 'schema_path_edit'):
                self.schema_path_edit.setText(Path(file_path).name)
        

class FileListWidget(QListWidget):
    """Custom list widget for displaying log files with checkboxes and color indicators."""
    
    checkbox_changed = pyqtSignal()  # Signal emitted when any checkbox state changes
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSelectionMode(QListWidget.ExtendedSelection)  # Allow Ctrl/Shift selection
        
    def add_log_file(self, file_path: str, color: QColor = None) -> None:
        """Add a log file to the list with checkbox and color indicator."""
        if color is None:
            # Generate a default color based on the number of items
            color = DEFAULT_FILE_COLORS[self.count() % len(DEFAULT_FILE_COLORS)]
        
        # Create a custom widget for the list item
        item_widget = FileListItemWidget(file_path, color)
        item_widget.checkbox_changed.connect(self.checkbox_changed.emit)
        
        # Create the list item
        item = QListWidgetItem()
        item.setSizeHint(item_widget.sizeHint())
        
        # Add to list and set the custom widget
        self.addItem(item)
        self.setItemWidget(item, item_widget)
        
        return item_widget


class FileListItemWidget(QWidget):
    """Custom widget for each file list item with checkbox and color indicator."""
    
    checkbox_changed = pyqtSignal()  # Signal emitted when checkbox state changes
    
    def __init__(self, file_path: str, color: QColor, parent=None):
        super().__init__(parent)
        self.file_path = file_path
        self.color = color
        
        self.setup_ui()
        
    def setup_ui(self):
        """Set up the UI components for the file item."""
        layout = QHBoxLayout()
        layout.setContentsMargins(*FILE_ITEM_CONTENT_MARGINS)
        
        # Checkbox for enabling/disabling the file
        self.checkbox = QCheckBox()
        self.checkbox.setChecked(DEFAULT_CHECKBOX_CHECKED)  # Default to checked
        self.checkbox.stateChanged.connect(self.checkbox_changed.emit)
        layout.addWidget(self.checkbox)
        
        # Color indicator
        self.color_label = QLabel()
        self.color_label.setFixedSize(*COLOR_INDICATOR_SIZE)
        self.color_label.setStyleSheet(COLOR_INDICATOR_STYLE_TEMPLATE.format(color=self.color.name()))
        layout.addWidget(self.color_label)
        
        # File name label
        file_name = Path(self.file_path).name
        self.file_label = QLabel(file_name)
        self.file_label.setToolTip(self.file_path)  # Show full path on hover
        layout.addWidget(self.file_label, 1)  # Stretch to fill available space
        
        self.setLayout(layout)
    
    def is_checked(self) -> bool:
        """Return whether the file is currently checked."""
        return self.checkbox.isChecked()
    
    def set_checked(self, checked: bool) -> None:
        """Set the checked state of the file."""
        self.checkbox.setChecked(checked)
    
    def get_color(self) -> QColor:
        """Return the current color of the file."""
        return self.color
    
    def set_color(self, color: QColor) -> None:
        """Set the color of the file indicator."""
        self.color = color
        self.color_label.setStyleSheet(COLOR_INDICATOR_STYLE_TEMPLATE.format(color=color.name()))


class LogViewerSidebar(QWidget):
    """Sidebar widget containing file management controls and file list."""
    
    files_changed = pyqtSignal()  # Signal emitted when file list changes
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        """Set up the sidebar UI components."""
        layout = QVBoxLayout()
        layout.setContentsMargins(*SIDEBAR_CONTENT_MARGINS)
        
        # Title
        title_label = QLabel(LOG_FILES_TITLE)
        title_label.setStyleSheet(TITLE_LABEL_STYLE)
        layout.addWidget(title_label)
        
        # Select All / Deselect All buttons
        button_layout = QHBoxLayout()
        
        self.select_all_btn = QPushButton(SELECT_ALL_TEXT)
        self.select_all_btn.clicked.connect(self.select_all_files)
        button_layout.addWidget(self.select_all_btn)
        
        self.deselect_all_btn = QPushButton(DESELECT_ALL_TEXT)
        self.deselect_all_btn.clicked.connect(self.deselect_all_files)
        button_layout.addWidget(self.deselect_all_btn)
        
        layout.addLayout(button_layout)
        
        # File list
        self.file_list = FileListWidget()
        self.file_list.checkbox_changed.connect(self.files_changed.emit)
        layout.addWidget(self.file_list, 1)  # Stretch to fill available space
        
        # Add/Remove buttons
        control_layout = QHBoxLayout()
        
        self.add_btn = QPushButton(ADD_BUTTON_EMOJI)
        self.add_btn.setToolTip(ADD_FILES_TOOLTIP)
        self.add_btn.clicked.connect(self.add_files)
        control_layout.addWidget(self.add_btn)
        
        self.remove_btn = QPushButton(REMOVE_BUTTON_EMOJI)
        self.remove_btn.setToolTip(REMOVE_FILES_TOOLTIP)
        self.remove_btn.clicked.connect(self.remove_selected_files)
        control_layout.addWidget(self.remove_btn)
        
        control_layout.addStretch()  # Push buttons to the left
        
        layout.addLayout(control_layout)
        
        self.setLayout(layout)
        
        # Enable keyboard shortcuts
        self.file_list.keyPressEvent = self.handle_key_press
        
    def handle_key_press(self, event):
        """Handle keyboard events for the file list."""
        if event.key() == Qt.Key_Delete:
            self.remove_selected_files()
        else:
            # Call the original keyPressEvent
            QListWidget.keyPressEvent(self.file_list, event)
    
    def add_files(self):
        """Open tabbed dialog to add log files."""
        dialog = AddFilesDialog(self)
        
        if dialog.exec_() == QDialog.Accepted:
            file_paths = dialog.selected_files
            existing_files = self.get_all_files()
            added_files = []
            skipped_files = []
            
            for file_path in file_paths:
                # Normalize path for comparison
                normalized_path = str(Path(file_path).resolve())
                
                # Check if file is already in the list
                already_exists = any(
                    str(Path(existing_file).resolve()) == normalized_path 
                    for existing_file in existing_files
                )
                
                if not already_exists:
                    self.file_list.add_log_file(file_path)
                    added_files.append(file_path)
                else:
                    skipped_files.append(Path(file_path).name)
            
            # Show message if some files were skipped
            if skipped_files:
                if len(skipped_files) == 1:
                    message = DUPLICATE_FILE_MESSAGE_SINGLE.format(file=skipped_files[0])
                else:
                    message = DUPLICATE_FILES_MESSAGE_MULTIPLE.format(count=len(skipped_files))
                
                QMessageBox.information(self, DUPLICATE_FILES_DIALOG_TITLE, message)
            
            if added_files:
                self.files_changed.emit()
    
    def remove_selected_files(self):
        """Remove currently selected files from the list."""
        selected_items = self.file_list.selectedItems()
        if not selected_items:
            return
        
        # Confirm removal if multiple files selected
        if len(selected_items) > 1:
            reply = QMessageBox.question(
                self, 
                REMOVE_FILES_DIALOG_TITLE,
                REMOVE_MULTIPLE_FILES_CONFIRM.format(count=len(selected_items)),
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply != QMessageBox.Yes:
                return
        
        # Remove items in reverse order to avoid index issues
        for item in reversed(selected_items):
            row = self.file_list.row(item)
            self.file_list.takeItem(row)
        
        self.files_changed.emit()
    
    def select_all_files(self):
        """Check all files in the list."""
        for i in range(self.file_list.count()):
            item = self.file_list.item(i)
            widget = self.file_list.itemWidget(item)
            if isinstance(widget, FileListItemWidget):
                widget.set_checked(True)
    
    def deselect_all_files(self):
        """Uncheck all files in the list."""
        for i in range(self.file_list.count()):
            item = self.file_list.item(i)
            widget = self.file_list.itemWidget(item)
            if isinstance(widget, FileListItemWidget):
                widget.set_checked(False)
    
    def get_checked_files(self) -> List[str]:
        """Return list of file paths that are currently checked."""
        checked_files = []
        for i in range(self.file_list.count()):
            item = self.file_list.item(i)
            widget = self.file_list.itemWidget(item)
            if isinstance(widget, FileListItemWidget) and widget.is_checked():
                checked_files.append(widget.file_path)
        return checked_files
    
    def get_all_files(self) -> List[str]:
        """Return list of all file paths (checked and unchecked)."""
        all_files = []
        for i in range(self.file_list.count()):
            item = self.file_list.item(i)
            widget = self.file_list.itemWidget(item)
            if isinstance(widget, FileListItemWidget):
                all_files.append(widget.file_path)
        return all_files


class FileDiscoveryResultsDialog(QDialog):
    """Dialog to show discovered files and allow user to confirm addition."""
    
    def __init__(self, found_files: List[str], directory: str, regex_pattern: str, parent=None):
        super().__init__(parent)
        self.found_files = found_files
        self.directory = directory
        self.regex_pattern = regex_pattern
        self.setup_ui()
        
    def setup_ui(self):
        """Set up the dialog UI."""
        self.setWindowTitle(FILES_FOUND_DIALOG_TITLE)
        self.setModal(True)
        self.resize(*FILE_DISCOVERY_DIALOG_SIZE)
        
        layout = QVBoxLayout()
        
        # Summary label
        summary_text = FILES_FOUND_SUMMARY_FORMAT.format(count=len(self.found_files), pattern=self.regex_pattern, directory=self.directory)
        summary_label = QLabel(summary_text)
        summary_label.setWordWrap(True)
        summary_label.setStyleSheet(SUMMARY_LABEL_STYLE)
        layout.addWidget(summary_label)
        
        # File list
        if self.found_files:
            files_label = QLabel(FILES_TO_ADD_LABEL)
            layout.addWidget(files_label)
            
            self.file_list = QListWidget()
            for file_path in self.found_files:
                # Show relative path from the selected directory
                rel_path = str(Path(file_path).relative_to(self.directory))
                item = QListWidgetItem(rel_path)
                item.setToolTip(file_path)  # Full path on hover
                self.file_list.addItem(item)
            layout.addWidget(self.file_list)
        else:
            no_files_label = QLabel("No files found matching the specified pattern.")
            no_files_label.setStyleSheet(NO_FILES_STYLE)
            layout.addWidget(no_files_label)
        
        # Buttons
        button_box = QDialogButtonBox()
        if self.found_files:
            add_button = button_box.addButton(ADD_ALL_FILES_TEXT, QDialogButtonBox.AcceptRole)
            add_button.setDefault(True)
        
        cancel_button = button_box.addButton(CANCEL_TEXT, QDialogButtonBox.RejectRole)
        
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        self.setLayout(layout)


class AddFilesDialog(QDialog):
    """Dialog with tabs for selecting individual files or directory + regex."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.selected_files = []
        self.setup_ui()
        
    def setup_ui(self):
        """Set up the tabbed dialog UI."""
        self.setWindowTitle(ADD_FILES_DIALOG_TITLE)
        self.setModal(True)
        self.resize(*ADD_FILES_DIALOG_SIZE)
        
        layout = QVBoxLayout()
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        
        # Tab 1: Select Files
        self.files_tab = self.create_files_tab()
        self.tab_widget.addTab(self.files_tab, SELECT_FILES_TAB)
        
        # Tab 2: Directory + Regex
        self.directory_tab = self.create_directory_tab()
        self.tab_widget.addTab(self.directory_tab, DIRECTORY_REGEX_TAB)
        
        layout.addWidget(self.tab_widget)
        
        # Dialog buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept_selection)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        self.setLayout(layout)
        
    def create_files_tab(self):
        """Create the individual files selection tab."""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # Instructions
        instructions = QLabel(FILES_TAB_INSTRUCTIONS)
        instructions.setWordWrap(True)
        layout.addWidget(instructions)
        
        # File selection area
        self.selected_files_list = QListWidget()
        layout.addWidget(self.selected_files_list)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.browse_files_btn = QPushButton(BROWSE_FILES_TEXT)
        self.browse_files_btn.clicked.connect(self.browse_individual_files)
        button_layout.addWidget(self.browse_files_btn)
        
        self.clear_files_btn = QPushButton(CLEAR_BUTTON_TEXT)
        self.clear_files_btn.clicked.connect(self.clear_selected_files)
        button_layout.addWidget(self.clear_files_btn)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        tab.setLayout(layout)
        return tab
        
    def create_directory_tab(self):
        """Create the directory + regex selection tab."""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # Instructions
        instructions = QLabel(DIRECTORY_TAB_INSTRUCTIONS)
        instructions.setWordWrap(True)
        layout.addWidget(instructions)
        
        # Directory selection
        dir_layout = QHBoxLayout()
        dir_layout.addWidget(QLabel(DIRECTORY_LABEL))
        self.directory_edit = QLineEdit()
        self.directory_edit.setReadOnly(True)
        self.directory_edit.setPlaceholderText(DIRECTORY_PLACEHOLDER)
        dir_layout.addWidget(self.directory_edit)
        
        self.browse_dir_btn = QPushButton(BROWSE_BUTTON_TEXT)
        self.browse_dir_btn.clicked.connect(self.browse_directory)
        dir_layout.addWidget(self.browse_dir_btn)
        layout.addLayout(dir_layout)
        
        # Regex pattern
        regex_layout = QHBoxLayout()
        regex_layout.addWidget(QLabel(REGEX_PATTERN_LABEL))
        self.regex_edit = QLineEdit()
        self.regex_edit.setText(DEFAULT_REGEX_PATTERN)  # Default pattern
        self.regex_edit.setPlaceholderText(REGEX_PLACEHOLDER)
        self.regex_edit.textChanged.connect(self.validate_regex)
        regex_layout.addWidget(self.regex_edit)
        layout.addLayout(regex_layout)
        
        # Regex validation message
        self.regex_status_label = QLabel("")
        self.regex_status_label.setStyleSheet("color: green;")
        layout.addWidget(self.regex_status_label)
        
        # Recursive option
        self.recursive_checkbox = QCheckBox("Search subdirectories recursively")
        self.recursive_checkbox.setChecked(DEFAULT_RECURSIVE_SEARCH)  # Default to recursive
        layout.addWidget(self.recursive_checkbox)
        
        # Preview button
        self.preview_btn = QPushButton(PREVIEW_FILES_TEXT)
        self.preview_btn.clicked.connect(self.preview_directory_files)
        self.preview_btn.setEnabled(False)  # Enabled when directory is selected
        layout.addWidget(self.preview_btn)
        
        # Examples
        examples_label = QLabel(REGEX_EXAMPLES_HTML)
        examples_label.setWordWrap(True)
        examples_label.setStyleSheet(INFO_LABEL_STYLE)
        layout.addWidget(examples_label)
        
        layout.addStretch()
        tab.setLayout(layout)
        return tab
        
    def browse_individual_files(self):
        """Browse for individual files."""
        file_dialog = QFileDialog()
        file_dialog.setFileMode(QFileDialog.ExistingFiles)
        file_dialog.setNameFilter(LOG_FILE_FILTER)
        file_dialog.setViewMode(QFileDialog.Detail)
        
        if file_dialog.exec_() == QFileDialog.Accepted:
            files = file_dialog.selectedFiles()
            for file_path in files:
                # Check for duplicates in the current selection
                if file_path not in [self.selected_files_list.item(i).data(Qt.UserRole) 
                                   for i in range(self.selected_files_list.count())]:
                    item = QListWidgetItem(Path(file_path).name)
                    item.setData(Qt.UserRole, file_path)
                    item.setToolTip(file_path)
                    self.selected_files_list.addItem(item)
                    
    def clear_selected_files(self):
        """Clear the selected files list."""
        self.selected_files_list.clear()
        
    def browse_directory(self):
        """Browse for directory."""
        directory = QFileDialog.getExistingDirectory(self, "Select Directory")
        if directory:
            self.directory_edit.setText(directory)
            self.preview_btn.setEnabled(True)
            self.validate_regex()  # Re-validate with directory selected
            
    def validate_regex(self):
        """Validate the regex pattern and update status."""
        pattern = self.regex_edit.text().strip()
        if not pattern:
            self.regex_status_label.setText(ENTER_REGEX_MESSAGE)
            self.regex_status_label.setStyleSheet(REGEX_WARNING_STYLE)
            self.regex_edit.setStyleSheet("")
            return False
            
        try:
            re.compile(pattern, re.IGNORECASE)
            self.regex_status_label.setText(VALID_REGEX_MESSAGE)
            self.regex_status_label.setStyleSheet(REGEX_VALID_STYLE)
            self.regex_edit.setStyleSheet("")
            return True
        except re.error as e:
            self.regex_status_label.setText(INVALID_REGEX_MESSAGE_FORMAT.format(error=str(e)))
            self.regex_status_label.setStyleSheet(REGEX_ERROR_STYLE)
            self.regex_edit.setStyleSheet(REGEX_INPUT_ERROR_STYLE)
            return False
            
    def find_matching_files(self, directory: str, pattern: str, recursive: bool) -> List[str]:
        """Find files matching the regex pattern in the directory."""
        try:
            regex = re.compile(pattern, re.IGNORECASE)
            matching_files = []
            directory_path = Path(directory)
            
            if recursive:
                # Recursive search using rglob
                for file_path in directory_path.rglob("*"):
                    if file_path.is_file():
                        # Get relative path from directory for regex matching
                        rel_path = str(file_path.relative_to(directory_path))
                        if regex.search(rel_path):
                            matching_files.append(str(file_path))
            else:
                # Non-recursive search using iterdir
                for file_path in directory_path.iterdir():
                    if file_path.is_file():
                        # For non-recursive, just match the filename
                        if regex.search(file_path.name):
                            matching_files.append(str(file_path))
                            
            return sorted(matching_files)
        except Exception as e:
            QMessageBox.warning(self, SEARCH_ERROR_DIALOG_TITLE, SEARCH_ERROR_MESSAGE_FORMAT.format(error=str(e)))
            return []
            
    def preview_directory_files(self):
        """Preview files that would be matched by the directory + regex."""
        directory = self.directory_edit.text().strip()
        pattern = self.regex_edit.text().strip()
        recursive = self.recursive_checkbox.isChecked()
        
        if not directory:
            QMessageBox.warning(self, NO_DIRECTORY_DIALOG_TITLE, NO_DIRECTORY_MESSAGE)
            return
            
        if not self.validate_regex():
            QMessageBox.warning(self, INVALID_REGEX_DIALOG_TITLE, INVALID_REGEX_MESSAGE)
            return
            
        # Find matching files
        matching_files = self.find_matching_files(directory, pattern, recursive)
        
        # Show results dialog
        results_dialog = FileDiscoveryResultsDialog(matching_files, directory, pattern, self)
        if results_dialog.exec_() == QDialog.Accepted:
            # User clicked "Add All Files" in preview - complete the entire flow
            self.selected_files = matching_files
            self.accept()  # Close the main AddFilesDialog and add files
        
    def accept_selection(self):
        """Accept the selection from the active tab."""
        current_tab = self.tab_widget.currentIndex()
        
        if current_tab == 0:  # Files tab
            # Get selected individual files
            self.selected_files = []
            for i in range(self.selected_files_list.count()):
                item = self.selected_files_list.item(i)
                file_path = item.data(Qt.UserRole)
                self.selected_files.append(file_path)
                
        elif current_tab == 1:  # Directory tab
            # Get files from directory + regex
            directory = self.directory_edit.text().strip()
            pattern = self.regex_edit.text().strip()
            recursive = self.recursive_checkbox.isChecked()
            
            if not directory:
                QMessageBox.warning(self, NO_DIRECTORY_DIALOG_TITLE, NO_DIRECTORY_MESSAGE)
                return
                
            if not self.validate_regex():
                QMessageBox.warning(self, INVALID_REGEX_DIALOG_TITLE, INVALID_REGEX_MESSAGE)
                return
                
            # Find matching files
            matching_files = self.find_matching_files(directory, pattern, recursive)
            
            if not matching_files:
                QMessageBox.information(self, NO_FILES_FOUND_DIALOG_TITLE, 
                                      NO_FILES_FOUND_MESSAGE)
                return
                
            # Show results and get confirmation
            results_dialog = FileDiscoveryResultsDialog(matching_files, directory, pattern, self)
            if results_dialog.exec_() == QDialog.Accepted:
                self.selected_files = matching_files
            else:
                return  # User cancelled
                
        self.accept()


class ColumnConfigurationDialog(QDialog):
    """Dialog for configuring which columns to display and their order."""
    
    def __init__(self, schema: LogParsingPlugin, visible_columns: List[str], parent=None):
        super().__init__(parent)
        self.schema = schema
        self.visible_columns = visible_columns.copy()  # Current configuration
        
        # Build list of all possible columns (schema fields + virtual columns)
        all_columns = [LogTableModel.SOURCE_FILE_COLUMN] + [field['name'] for field in schema.fields]
        self.available_columns = [col for col in all_columns if col not in visible_columns]
        self.setup_ui()
        
    def setup_ui(self):
        """Set up the dialog UI with dual-list selection pattern."""
        self.setWindowTitle(COLUMN_CONFIG_DIALOG_TITLE)
        self.setModal(True)
        self.resize(*COLUMN_CONFIG_DIALOG_SIZE)
        
        layout = QVBoxLayout()
        
        # Instructions
        instructions = QLabel(COLUMN_CONFIG_INSTRUCTIONS)
        instructions.setWordWrap(True)
        layout.addWidget(instructions)
        
        # Main dual-list area
        main_layout = QHBoxLayout()
        
        # Available columns (left side)
        left_layout = QVBoxLayout()
        left_layout.addWidget(QLabel(AVAILABLE_COLUMNS_LABEL))
        self.available_list = QListWidget()
        self.available_list.setSelectionMode(QListWidget.ExtendedSelection)
        self.available_list.itemDoubleClicked.connect(self.add_selected_columns)
        left_layout.addWidget(self.available_list)
        
        # Control buttons (center)
        button_layout = QVBoxLayout()
        button_layout.addStretch()
        
        self.add_button = QPushButton(ADD_SELECTED_TEXT)
        self.add_button.setToolTip(ADD_COLUMNS_TOOLTIP)
        self.add_button.clicked.connect(self.add_selected_columns)
        button_layout.addWidget(self.add_button)
        
        self.add_all_button = QPushButton(ADD_ALL_TEXT)
        self.add_all_button.setToolTip(ADD_ALL_COLUMNS_TOOLTIP)
        self.add_all_button.clicked.connect(self.add_all_columns)
        button_layout.addWidget(self.add_all_button)
        
        button_layout.addSpacing(20)
        
        self.remove_button = QPushButton(REMOVE_SELECTED_TEXT)
        self.remove_button.setToolTip(REMOVE_COLUMNS_TOOLTIP)
        self.remove_button.clicked.connect(self.remove_selected_columns)
        button_layout.addWidget(self.remove_button)
        
        self.remove_all_button = QPushButton(REMOVE_ALL_TEXT)
        self.remove_all_button.setToolTip(REMOVE_ALL_COLUMNS_TOOLTIP)
        self.remove_all_button.clicked.connect(self.remove_all_columns)
        button_layout.addWidget(self.remove_all_button)
        
        button_layout.addStretch()
        
        # Visible columns (right side)
        right_layout = QVBoxLayout()
        right_layout.addWidget(QLabel(VISIBLE_COLUMNS_LABEL))
        self.visible_list = QListWidget()
        self.visible_list.setSelectionMode(QListWidget.ExtendedSelection)
        self.visible_list.itemDoubleClicked.connect(self.remove_selected_columns)
        right_layout.addWidget(self.visible_list)
        
        # Ordering buttons for visible list
        order_layout = QHBoxLayout()
        
        self.move_up_button = QPushButton(MOVE_UP_TEXT)
        self.move_up_button.setToolTip(MOVE_UP_TOOLTIP)
        self.move_up_button.clicked.connect(self.move_columns_up)
        order_layout.addWidget(self.move_up_button)
        
        self.move_down_button = QPushButton(MOVE_DOWN_TEXT)
        self.move_down_button.setToolTip(MOVE_DOWN_TOOLTIP)
        self.move_down_button.clicked.connect(self.move_columns_down)
        order_layout.addWidget(self.move_down_button)
        
        order_layout.addStretch()
        right_layout.addLayout(order_layout)
        
        # Assemble main layout
        main_layout.addLayout(left_layout, 1)
        main_layout.addLayout(button_layout, 0)
        main_layout.addLayout(right_layout, 1)
        layout.addLayout(main_layout)
        
        # Dialog buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel | QDialogButtonBox.RestoreDefaults)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        
        # Connect restore defaults button
        restore_button = button_box.button(QDialogButtonBox.RestoreDefaults)
        restore_button.clicked.connect(self.restore_defaults)
        restore_button.setToolTip("Reset to show all columns in default order")
        
        layout.addWidget(button_box)
        self.setLayout(layout)
        
        # Populate lists with current configuration
        self.populate_lists()
        
        # Connect selection change events to update button states
        self.available_list.itemSelectionChanged.connect(self.update_button_states)
        self.visible_list.itemSelectionChanged.connect(self.update_button_states)
        self.update_button_states()
        
    def populate_lists(self):
        """Populate the available and visible lists based on current configuration."""
        # Clear both lists
        self.available_list.clear()
        self.visible_list.clear()
        
        # Add available columns
        for column_name in self.available_columns:
            if column_name == LogTableModel.SOURCE_FILE_COLUMN:
                # Handle virtual column
                display_text = f"{column_name}{VIRTUAL_COLUMN_SUFFIX}"
                item = QListWidgetItem(display_text)
                item.setData(Qt.UserRole, column_name)
                item.setToolTip("Virtual column showing the source filename")
                self.available_list.addItem(item)
            else:
                # Find the field to get its display information
                field = next((f for f in self.schema.fields if f['name'] == column_name), None)
                if field:
                    display_text = f"{column_name} ({field['type']})"
                    item = QListWidgetItem(display_text)
                    item.setData(Qt.UserRole, column_name)
                    item.setToolTip(f"Type: {field['type']}")
                    self.available_list.addItem(item)
        
        # Add visible columns in their current order
        for column_name in self.visible_columns:
            if column_name == LogTableModel.SOURCE_FILE_COLUMN:
                # Handle virtual column
                display_text = f"{column_name}{VIRTUAL_COLUMN_SUFFIX}"
                item = QListWidgetItem(display_text)
                item.setData(Qt.UserRole, column_name)
                item.setToolTip("Virtual column showing the source filename")
                self.visible_list.addItem(item)
            else:
                # Find the field to get its display information
                field = next((f for f in self.schema.fields if f['name'] == column_name), None)
                if field:
                    display_text = f"{column_name} ({field['type']})"
                    item = QListWidgetItem(display_text)
                    item.setData(Qt.UserRole, column_name)
                    item.setToolTip(f"Type: {field['type']}")
                    self.visible_list.addItem(item)
    
    def add_selected_columns(self):
        """Move selected columns from available to visible list."""
        selected_items = self.available_list.selectedItems()
        if not selected_items:
            return
            
        # Get column names to move
        columns_to_move = [item.data(Qt.UserRole) for item in selected_items]
        
        # Update internal lists
        for column_name in columns_to_move:
            if column_name in self.available_columns:
                self.available_columns.remove(column_name)
                self.visible_columns.append(column_name)
        
        # Refresh display
        self.populate_lists()
        self.update_button_states()
    
    def add_all_columns(self):
        """Move all available columns to visible list."""
        # Move all available columns to visible
        self.visible_columns.extend(self.available_columns)
        self.available_columns.clear()
        
        # Refresh display
        self.populate_lists()
        self.update_button_states()
    
    def remove_selected_columns(self):
        """Move selected columns from visible to available list."""
        selected_items = self.visible_list.selectedItems()
        if not selected_items:
            return
            
        # Get column names to move
        columns_to_move = [item.data(Qt.UserRole) for item in selected_items]
        
        # Update internal lists
        for column_name in columns_to_move:
            if column_name in self.visible_columns:
                self.visible_columns.remove(column_name)
                self.available_columns.append(column_name)
        
        # Sort available columns alphabetically for easier browsing
        self.available_columns.sort()
        
        # Refresh display
        self.populate_lists()
        self.update_button_states()
    
    def remove_all_columns(self):
        """Move all visible columns to available list."""
        # Move all visible columns to available
        self.available_columns.extend(self.visible_columns)
        self.visible_columns.clear()
        
        # Sort available columns alphabetically
        self.available_columns.sort()
        
        # Refresh display
        self.populate_lists()
        self.update_button_states()
    
    def move_columns_up(self):
        """Move selected columns up in the visible list."""
        selected_items = self.visible_list.selectedItems()
        if not selected_items:
            return
            
        # Get selected rows (need to work with indices)
        selected_rows = sorted([self.visible_list.row(item) for item in selected_items])
        
        # Can't move up if first item is selected
        if selected_rows[0] == 0:
            return
            
        # Move each selected item up one position
        for row in selected_rows:
            column_name = self.visible_columns.pop(row)
            self.visible_columns.insert(row - 1, column_name)
        
        # Refresh display and maintain selection
        self.populate_lists()
        
        # Restore selection (shifted up by one)
        for row in selected_rows:
            if row > 0:
                self.visible_list.item(row - 1).setSelected(True)
        
        self.update_button_states()
    
    def move_columns_down(self):
        """Move selected columns down in the visible list."""
        selected_items = self.visible_list.selectedItems()
        if not selected_items:
            return
            
        # Get selected rows (need to work with indices)
        selected_rows = sorted([self.visible_list.row(item) for item in selected_items], reverse=True)
        
        # Can't move down if last item is selected
        if selected_rows[0] == len(self.visible_columns) - 1:
            return
            
        # Move each selected item down one position (in reverse order)
        for row in selected_rows:
            column_name = self.visible_columns.pop(row)
            self.visible_columns.insert(row + 1, column_name)
        
        # Refresh display and maintain selection
        self.populate_lists()
        
        # Restore selection (shifted down by one)
        for row in reversed(selected_rows):
            if row < len(self.visible_columns) - 1:
                self.visible_list.item(row + 1).setSelected(True)
        
        self.update_button_states()
    
    def restore_defaults(self):
        """Restore default configuration (all columns in schema order)."""
        # Reset to show all columns in schema order including virtual columns
        self.visible_columns = [LogTableModel.SOURCE_FILE_COLUMN] + [field['name'] for field in self.schema.fields]
        self.available_columns = []
        
        # Refresh display
        self.populate_lists()
        self.update_button_states()
    
    def update_button_states(self):
        """Update button enabled/disabled states based on current selections."""
        has_available_selection = len(self.available_list.selectedItems()) > 0
        has_visible_selection = len(self.visible_list.selectedItems()) > 0
        has_available_items = self.available_list.count() > 0
        has_visible_items = self.visible_list.count() > 0
        
        # Add/Remove buttons
        self.add_button.setEnabled(has_available_selection)
        self.add_all_button.setEnabled(has_available_items)
        self.remove_button.setEnabled(has_visible_selection)
        self.remove_all_button.setEnabled(has_visible_items)
        
        # Move buttons
        self.move_up_button.setEnabled(has_visible_selection and has_visible_items)
        self.move_down_button.setEnabled(has_visible_selection and has_visible_items)
    
    def get_column_configuration(self) -> List[str]:
        """Return the current visible columns configuration."""
        return self.visible_columns.copy()


class MergedLogViewer(QMainWindow):
    """Main application window for the merged log viewer."""
    
    def __init__(self):
        super().__init__()
        self.logger = get_logger(__name__)
        self.schema = None
        self.log_table_model = None
        self.parsing_worker = None
        self.shared_buffer = None
        self.follow_mode = True  # Auto-scroll to bottom by default
        self.auto_scroll_disabled = False  # Track if user manually scrolled away
        
        # First, select schema before setting up UI
        if not self.select_schema():
            sys.exit()  # User cancelled schema selection
            
        self.setup_ui()
        
    def setup_ui(self):
        """Set up the main window UI."""
        self.setWindowTitle(WINDOW_TITLE)
        self.setGeometry(*MAIN_WINDOW_DEFAULT_GEOMETRY)
        
        # Create toolbar
        self.setup_toolbar()
                
        # Create central widget with splitter
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Create splitter for resizable panels
        splitter = QSplitter(Qt.Horizontal)
        
        # Sidebar
        self.sidebar = LogViewerSidebar()
        self.sidebar.files_changed.connect(self.on_files_changed)
        self.sidebar.setMinimumWidth(SIDEBAR_MIN_WIDTH)
        self.sidebar.setMaximumWidth(SIDEBAR_MAX_WIDTH)
        splitter.addWidget(self.sidebar)
        
        # Main log view area with table
        self.log_table_view = QTableView()
        self.log_table_model = LogTableModel(self.schema)
        self.log_table_view.setModel(self.log_table_model)
        
        # Configure table view
        self.log_table_view.setAlternatingRowColors(True)
        self.log_table_view.setSelectionBehavior(QTableView.SelectRows)
        self.log_table_view.setSortingEnabled(True)
        
        # Setup initial header resize modes
        self.update_header_resize_modes()
        
        # Connect scroll bar signals for follow mode
        vertical_scrollbar = self.log_table_view.verticalScrollBar()
        vertical_scrollbar.valueChanged.connect(self.on_scroll_changed)
        vertical_scrollbar.rangeChanged.connect(self.on_scroll_range_changed)
            
        splitter.addWidget(self.log_table_view)
        
        # Set initial splitter sizes (sidebar: 300px, main view: rest)
        splitter.setSizes(DEFAULT_SPLITTER_SIZES)
        
        layout.addWidget(splitter)
        central_widget.setLayout(layout)
        
        # Initialize shared buffer and worker
        self.shared_buffer = SharedLogBuffer()
        self.parsing_worker = LogParsingWorker(self.schema, self.shared_buffer, self)
        
        # Timer to drain shared buffer
        self.buffer_timer = QTimer()
        self.buffer_timer.timeout.connect(self.drain_log_buffer)
        self.buffer_timer.start(BUFFER_DRAIN_INTERVAL_MS)  # Drain every 100ms
        
        # Start the parsing worker
        self.parsing_worker.start()
        
        # Status bar
        self.statusBar().showMessage(READY_STATUS)
    
    def setup_toolbar(self):
        """Set up the main toolbar with follow mode controls."""
        toolbar = self.addToolBar("Main")
        toolbar.setMovable(False)
        
        # Follow mode toggle action
        self.follow_action = QAction(FOLLOW_ACTION_TEXT, self)
        self.follow_action.setCheckable(True)
        self.follow_action.setChecked(self.follow_mode)
        self.follow_action.setToolTip(FOLLOW_MODE_TOOLTIP)
        self.follow_action.triggered.connect(self.toggle_follow_mode)
        toolbar.addAction(self.follow_action)
        
        # Add separator
        toolbar.addSeparator()
        
        # Column configuration action
        self.column_config_action = QAction(COLUMN_CONFIG_ACTION_TEXT, self)
        self.column_config_action.setToolTip(COLUMN_CONFIG_TOOLTIP)
        self.column_config_action.triggered.connect(self.open_column_configuration)
        toolbar.addAction(self.column_config_action)
    
    def toggle_follow_mode(self):
        """Toggle follow mode on/off."""
        self.follow_mode = self.follow_action.isChecked()
        self.auto_scroll_disabled = False  # Reset manual scroll override
        
        # Immediately scroll to bottom when enabling follow mode
        if self.follow_mode:
            self.scroll_to_bottom()
    
    def on_scroll_changed(self, value):
        """Handle manual scrolling by the user."""
        if not self.follow_mode:
            return
        
        # Check if user manually scrolled away from the bottom
        scrollbar = self.log_table_view.verticalScrollBar()
        is_at_bottom = (value >= scrollbar.maximum() - SCROLL_TOLERANCE_PIXELS)  # Allow for 1 pixel tolerance
        
        if not is_at_bottom and not self.auto_scroll_disabled:
            # User manually scrolled away from bottom - disable auto-scroll
            self.auto_scroll_disabled = True
    
    def on_scroll_range_changed(self, min_val, max_val):
        """Handle when the scroll range changes (new content added)."""
        if self.follow_mode and not self.auto_scroll_disabled:
            # Auto-scroll to bottom when new content is added
            QTimer.singleShot(0, self.scroll_to_bottom)
    
    def scroll_to_bottom(self):
        """Scroll the table view to the bottom."""
        scrollbar = self.log_table_view.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def select_schema(self) -> bool:
        """Show schema selection dialog and load the selected schema."""
        # Select schema file
        schema_dialog = SchemaSelectionDialog(self)
        if schema_dialog.exec_() != QDialog.Accepted or not schema_dialog.selected_schema_path:
            return False
            
        try:
            # Load and create plugin from file
            self.schema = LogParsingPlugin.from_file(schema_dialog.selected_schema_path)
            return True
            
        except Exception as e:
            QMessageBox.critical(
                self, 
                SCHEMA_ERROR_DIALOG_TITLE, 
                SCHEMA_LOAD_ERROR_FORMAT.format(error=str(e))
            )
            return False
    
    def drain_log_buffer(self):
        start_time = time.perf_counter()
        """Drain entries from shared buffer and update table."""
        if self.shared_buffer:
            entries = self.shared_buffer.drain_entries()
            if entries:
                self.logger.debug(PROCESSING_ENTRIES_FORMAT.format(count=len(entries)))
                
                # Remember current scroll position for follow mode logic
                scrollbar = self.log_table_view.verticalScrollBar()
                was_at_bottom = (scrollbar.value() >= scrollbar.maximum() - 1)
                
                # Batch add to table model
                self.log_table_model.add_entries_batch(entries)
                
                # Force Qt to process all pending events (including table redraws)
                QApplication.processEvents()
                
                # Handle follow mode scrolling
                if self.follow_mode and not self.auto_scroll_disabled:
                    # If we were at the bottom before adding entries, stay at bottom
                    if was_at_bottom or scrollbar.maximum() == 0:
                        self.scroll_to_bottom()
                elif self.follow_mode and self.auto_scroll_disabled and was_at_bottom:
                    # User was manually at bottom - re-enable auto-scroll
                    self.auto_scroll_disabled = False
                    self.scroll_to_bottom()
                
                elapsed_time = time.perf_counter() - start_time
                self.logger.debug(BUFFER_DRAINED_FORMAT.format(count=len(entries), time=elapsed_time))
            else:
                self.logger.debug(BUFFER_EMPTY_MESSAGE)
        else:
            self.logger.warning(NO_SHARED_BUFFER_MESSAGE)

    def on_files_changed(self):
        """Handle changes to the file list."""
        checked_files = self.sidebar.get_checked_files()
        all_files = self.sidebar.get_all_files()
        
        # Update table model to show only checked files
        self.log_table_model.update_checked_files(checked_files)
        
        # Update file colors for the table model
        self._update_file_colors()
        
        # Update worker with the complete file list - worker handles all internal management
        if hasattr(self, 'parsing_worker') and self.parsing_worker:
            self.parsing_worker.update_file_list(all_files)
        
        # Update status message with file counts
        status_msg = FILE_COUNT_STATUS_FORMAT.format(total=len(all_files), selected=len(checked_files))
        if not all_files:
            status_msg = READY_STATUS
        self.statusBar().showMessage(status_msg)
        
    def _update_file_colors(self):
        """Update the file colors in the table model from the sidebar."""
        file_colors = {}
        for i in range(self.sidebar.file_list.count()):
            item = self.sidebar.file_list.item(i)
            widget = self.sidebar.file_list.itemWidget(item)
            if isinstance(widget, FileListItemWidget):
                file_colors[widget.file_path] = widget.get_color()
        
        # Set the colors on the table model using the new caching method
        self.log_table_model.update_file_colors(file_colors)
        
    def closeEvent(self, event):
        """Handle application close event - properly stop worker thread."""
        # Stop the buffer timer
        if hasattr(self, 'buffer_timer'):
            self.buffer_timer.stop()
            
        # Stop and wait for the parsing worker thread
        if hasattr(self, 'parsing_worker') and self.parsing_worker:
            self.parsing_worker.stop()
            # Wait for thread to finish (with timeout)
            if self.parsing_worker.isRunning():
                self.parsing_worker.wait(THREAD_SHUTDOWN_TIMEOUT_MS)  # Wait up to 3 seconds
                if self.parsing_worker.isRunning():
                    # Force terminate if still running
                    self.parsing_worker.terminate()
                    self.parsing_worker.wait(THREAD_FORCE_TERMINATE_TIMEOUT_MS)  # Wait 1 more second
                    
        # Accept the close event
        event.accept()

    def open_column_configuration(self):
        """Open the column configuration dialog."""
        current_config = self.log_table_model.get_column_configuration()
        
        dialog = ColumnConfigurationDialog(self.schema, current_config, self)
        if dialog.exec_() == QDialog.Accepted:
            new_config = dialog.get_column_configuration()
            self.log_table_model.update_column_configuration(new_config)
            
            # Update header resize modes for the new column configuration
            self.update_header_resize_modes()

    def update_header_resize_modes(self):
        """Update header resize modes based on current column configuration."""
        header = self.log_table_view.horizontalHeader()
        header.setStretchLastSection(True)
        
        # Set resize mode for all visible columns except the last one
        visible_column_count = len(self.log_table_model.visible_columns)
        for i in range(visible_column_count - 1):
            header.setSectionResizeMode(i, QHeaderView.ResizeToContents)


def run():
    """
    Programmatic entry point for running the LogMerge application.
    
    This function creates and runs the application without requiring command-line arguments.
    It can be used when embedding LogMerge in other Python applications.
    
    Returns:
        int: Exit code from the application (0 for success)
        
    Example:
        >>> import logmerge
        >>> exit_code = logmerge.run()
    """
    return main()


def main():
    """Main entry point for the application."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="Merged Log Viewer - A GUI application for viewing and analyzing multiple log files"
    )
    parser.add_argument(
        '--log-level', 
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
        default='WARNING',
        help='Set the logging level (default: WARNING)'
    )
    
    args = parser.parse_args()
    
    # Set up logging
    logger = setup_logging(args.log_level)
    logger.info(f"Starting Merged Log Viewer with log level: {args.log_level}")
    
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("Merged Log Viewer")
    app.setApplicationVersion("1.0.0")
    
    # Create and show main window
    window = MergedLogViewer()
    window.show()
    
    # Start event loop
    return app.exec_()


if __name__ == '__main__':
    sys.exit(main())
