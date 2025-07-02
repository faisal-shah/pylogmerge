"""
Log Table Model

Contains the table model for displaying log entries in the main table view.
"""

from pathlib import Path
from typing import List, Dict
from datetime import datetime

from PyQt5.QtCore import QAbstractTableModel, QModelIndex, Qt
from PyQt5.QtGui import QColor

from ..data_structures import LogEntry
from ..constants import COLOR_LIGHTEN_FACTOR


class LogTableModel(QAbstractTableModel):
    """Table model for displaying log entries."""
    
    # Cache type constants for clear invalidation
    CACHE_DATETIME_STRINGS = 'datetime_strings'
    CACHE_FILE_COLORS = 'file_colors'
    CACHE_VISIBLE_ENTRIES = 'visible_entries'
    
    # Virtual column name for source file
    SOURCE_FILE_COLUMN = "Source File"
    
    def __init__(self, schema, parent=None):
        super().__init__(parent)
        self.schema = schema
        self.log_entries = []
        self.checked_files = set()
        self.visible_entries = []  # Cached filtered entries for performance
        self.cached_file_colors = {}  # Cache for lightened background colors
        self.cached_datetime_strings = {}  # Cache for formatted datetime strings
        self.file_colors = {}  # File path to color mapping
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
        if file_path in self.file_colors:
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
