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
    
    # Virtual column name for source file
    SOURCE_FILE_COLUMN = "Source File"
    
    def __init__(self, schema, parent=None):
        super().__init__(parent)
        self.schema = schema
        self.log_entries = []
        self.checked_files = set()
        self.visible_entries = []
        self.display_cache = {}
        self.file_colors = {}  # File path to color mapping
        # Column configuration - include virtual Source File column first, then schema columns
        self.visible_columns = [self.SOURCE_FILE_COLUMN] + [field['name'] for field in schema.fields]
        
    def _invalidate_cache(self):
        """Invalidate all caches and rebuild visible entries."""
        self.display_cache.clear()
        self._rebuild_visible_entries()
        
    def update_checked_files(self, checked_files: List[str]):
        """Update which files should be displayed efficiently."""
        self.checked_files = set(checked_files)
        self.beginResetModel()
        self._rebuild_visible_entries()  # Re-filter, but don't rebuild the whole cache
        self.endResetModel()
        
    def _rebuild_visible_entries(self):
        """Filter log entries to what is visible without rebuilding the display cache."""
        self.visible_entries = [entry for entry in self.log_entries 
                              if entry.file_path in self.checked_files]
        
    def _get_cached_row(self, entry: LogEntry) -> tuple:
        """Get a display-ready row from cache or build it if not present."""
        entry_id = id(entry)
        if entry_id in self.display_cache:
            return self.display_cache[entry_id]

        # If not in cache, build it
        row_data = []
        for col_name in self.visible_columns:
            if col_name == self.SOURCE_FILE_COLUMN:
                value = Path(entry.file_path).name
            else:
                raw_value = entry.fields.get(col_name)
                if isinstance(raw_value, datetime):
                    value = raw_value.strftime('%Y-%m-%d %H:%M:%S')
                elif raw_value is None:
                    value = ''
                else:
                    value = str(raw_value)
            row_data.append(value)
        
        bg_color = self._get_file_color(entry.file_path)
        cached_row = (row_data, bg_color)
        self.display_cache[entry_id] = cached_row
        return cached_row

    def add_log_entry(self, entry: LogEntry):
        """Add a new log entry using binary search for optimal insertion."""
        # Use binary search to find insertion position
        insert_index = self._binary_search_insert_position(entry.timestamp)
        
        # Add to log entries
        self.log_entries.insert(insert_index, entry)
        
        # If entry is visible, update visible entries and notify model
        if entry.file_path in self.checked_files:
            visible_insert_index = self._binary_search_visible_insert_position(entry.timestamp)
            self.beginInsertRows(QModelIndex(), visible_insert_index, visible_insert_index)
            self.visible_entries.insert(visible_insert_index, entry)
            self.endInsertRows()
        
    def add_entries_batch(self, entries: List[LogEntry]):
        """Add multiple log entries efficiently."""
        if not entries:
            return
            
        self.beginResetModel()
        
        # Add to full log entries list and re-sort
        self.log_entries.extend(entries)
        self.log_entries.sort(key=lambda entry: entry.timestamp)
        
        # Invalidate and rebuild cache and visible entries
        self._invalidate_cache()
        
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
    
    def get_unique_field_values(self, field_name: str) -> List:
        """Get unique values for a specific field from all log entries."""
        unique_values = set()
        
        for entry in self.log_entries:
            if field_name in entry.fields:
                value = entry.fields[field_name]
                if value is not None:
                    unique_values.add(value)
        
        # Return sorted list for consistent display
        sorted_values = sorted(list(unique_values))
        return sorted_values
    
    def clear_entries(self):
        """Clear all log entries."""
        self.beginResetModel()
        self.log_entries.clear()
        self.visible_entries.clear()
        self.display_cache.clear()
        self.endResetModel()
        
    def rowCount(self, parent=QModelIndex()):
        """Return number of visible rows."""
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
        """Return data for a cell from the cache."""
        row = index.row()
        col = index.column()
        
        if not (0 <= row < len(self.visible_entries)):
            return None
            
        entry = self.visible_entries[row]
        cached_row, background_color = self._get_cached_row(entry)
        
        if role == Qt.DisplayRole:
            return cached_row[col]
            
        elif role == Qt.UserRole:
            # Return the raw value for filtering/sorting
            column_name = self.visible_columns[col]
            if column_name == self.SOURCE_FILE_COLUMN:
                return entry.file_path
            return entry.fields.get(column_name)
            
        elif role == Qt.BackgroundRole:
            return background_color
            
        return None
        
    def _get_file_color(self, file_path: str):
        """Get the background color for a file path."""
        if file_path in self.file_colors:
            color = self.file_colors[file_path]
            # Return a very light version of the color for background
            red = int(color.red() + (255 - color.red()) * COLOR_LIGHTEN_FACTOR)
            green = int(color.green() + (255 - color.green()) * COLOR_LIGHTEN_FACTOR)
            blue = int(color.blue() + (255 - color.blue()) * COLOR_LIGHTEN_FACTOR)
            return QColor(red, green, blue)
        return None
    
    def update_file_colors(self, file_colors: Dict[str, QColor]):
        """Update file colors and clear the cache."""
        self.file_colors = file_colors
        self.beginResetModel()
        self._invalidate_cache()
        self.endResetModel()
    
    def update_column_configuration(self, visible_columns: List[str]):
        """Update which columns are visible and their order."""
        # Validate that all column names exist in schema or are virtual columns
        valid_columns = []
        schema_field_names = {field['name'] for field in self.schema.fields}
        virtual_columns = {self.SOURCE_FILE_COLUMN}
        allowed_columns = schema_field_names | virtual_columns
        
        for column_name in visible_columns:
            if column_name in allowed_columns:
                valid_columns.append(column_name)
        
        if valid_columns != self.visible_columns:
            self.beginResetModel()
            self.visible_columns = valid_columns
            self._invalidate_cache()
            self.endResetModel()
    
    def get_column_configuration(self) -> List[str]:
        """Return the current visible columns configuration."""
        return self.visible_columns.copy()
