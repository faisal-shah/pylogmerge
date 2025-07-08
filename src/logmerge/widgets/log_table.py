"""
Log Table Model

Contains the table model for displaying log entries in the main table view.
"""

import re
from pathlib import Path
from typing import List, Dict, Union
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
        self.field_filters = {}  # Field-based filters in standardized format
        self.visible_entries = []
        self.entry_display_cache = (
            {}
        )  # Single entry-level cache: entry_id -> formatted_data_dict
        self.file_colors = {}  # File path to color mapping
        # Column configuration - include virtual Source File column first, then schema columns
        self.visible_columns = [self.SOURCE_FILE_COLUMN] + [
            field["name"] for field in schema.fields
        ]

    def _invalidate_cache(self):
        """Simple cache invalidation - clear everything and rebuild visible entries."""
        self.entry_display_cache.clear()
        self._rebuild_visible_entries()

    def update_checked_files(self, checked_files: List[str]):
        """Update which files should be displayed efficiently."""
        self.checked_files = set(checked_files)
        self.beginResetModel()
        self._rebuild_visible_entries()  # Re-filter, but don't rebuild the whole cache
        self.endResetModel()

    def _rebuild_visible_entries(self):
        """Filter log entries by both file selection AND field filters."""
        self.visible_entries = [
            entry
            for entry in self.log_entries
            if entry.file_path in self.checked_files
            and self._matches_field_filters(entry)
        ]

    def _matches_field_filters(self, entry: LogEntry) -> bool:
        """Check if a log entry matches all active field filters."""
        if not self.field_filters:
            return True  # No field filters active, so entry matches

        for field_name, filter_criteria in self.field_filters.items():
            entry_value = entry.fields.get(field_name)
            filter_type = filter_criteria.get("type")

            # Apply filter based on type
            if filter_type == "discrete":
                selected_values = filter_criteria.get("selected", set())
                if entry_value not in selected_values:
                    return False

            elif filter_type == "numeric_range":
                min_val = filter_criteria.get("min")
                max_val = filter_criteria.get("max")
                if min_val is not None and (
                    entry_value is None or entry_value < min_val
                ):
                    return False
                if max_val is not None and (
                    entry_value is None or entry_value > max_val
                ):
                    return False

            elif filter_type == "text":
                pattern = filter_criteria.get("pattern", "")
                if pattern and entry_value is not None:
                    try:
                        if not re.search(pattern, str(entry_value), re.IGNORECASE):
                            return False
                    except re.error:
                        # If regex is invalid, fall back to simple string matching
                        if pattern.lower() not in str(entry_value).lower():
                            return False
                elif pattern:  # Pattern exists but entry_value is None
                    return False

            elif filter_type == "datetime_range":
                from_dt = filter_criteria.get("from")
                to_dt = filter_criteria.get("to")
                if from_dt is not None and (
                    entry_value is None or entry_value < from_dt
                ):
                    return False
                if to_dt is not None and (entry_value is None or entry_value > to_dt):
                    return False

            elif filter_type == "float_timestamp_range":
                from_val = filter_criteria.get("from")
                to_val = filter_criteria.get("to")
                if from_val is not None and (
                    entry_value is None or entry_value < from_val
                ):
                    return False
                if to_val is not None and (entry_value is None or entry_value > to_val):
                    return False

        return True  # All filters passed

    def _get_field_schema(self, field_name: str) -> dict:
        """Get the schema definition for a specific field."""
        if not self.schema:
            return None

        for field in self.schema.fields:
            if field.get("name") == field_name:
                return field
        return None

    def _get_cached_entry_data(self, entry: LogEntry) -> dict:
        """Get or build cached display data for an entry."""
        entry_id = id(entry)

        if entry_id not in self.entry_display_cache:
            # Pre-compute ALL expensive operations once
            cached_data = {
                "filename": Path(entry.file_path).name,  # Expensive path operation
                "file_color": self._get_file_color(
                    entry.file_path
                ),  # Color calculation
                "formatted_fields": {},
            }

            # Pre-format all fields that need formatting
            for field_name in self.visible_columns:
                if field_name == self.SOURCE_FILE_COLUMN:
                    cached_data["formatted_fields"][field_name] = cached_data[
                        "filename"
                    ]
                else:
                    raw_value = entry.fields.get(field_name)
                    if isinstance(raw_value, datetime):
                        cached_data["formatted_fields"][
                            field_name
                        ] = raw_value.strftime("%Y-%m-%d %H:%M:%S")
                    elif isinstance(raw_value, float):
                        # Format float timestamps to 6 decimal places (microseconds)
                        cached_data["formatted_fields"][field_name] = f"{raw_value:.6f}"
                    elif raw_value is None:
                        cached_data["formatted_fields"][field_name] = ""
                    else:
                        # Check if this field is an enum and has display mapping
                        if field_name in self.schema.enum_display_maps:
                            # Use pre-built enum display map - O(1) lookup!
                            enum_display_map = self.schema.enum_display_maps[field_name]
                            display_value = enum_display_map.get(
                                raw_value, str(raw_value)
                            )
                            cached_data["formatted_fields"][field_name] = display_value
                        else:
                            cached_data["formatted_fields"][field_name] = str(raw_value)

            self.entry_display_cache[entry_id] = cached_data

        return self.entry_display_cache[entry_id]

    def apply_filters(self, field_filters: dict):
        """Apply field filters and rebuild visible entries."""
        self.field_filters = field_filters
        self.beginResetModel()
        self._rebuild_visible_entries()
        self.endResetModel()

    def add_log_entry(self, entry: LogEntry):
        """Add a new log entry using binary search for optimal insertion."""
        # Use binary search to find insertion position
        insert_index = self._binary_search_insert_position(entry.timestamp)

        # Add to log entries
        self.log_entries.insert(insert_index, entry)

        # If entry is visible (passes both file and field filters), update visible entries and notify model
        if entry.file_path in self.checked_files and self._matches_field_filters(entry):
            visible_insert_index = self._binary_search_visible_insert_position(
                entry.timestamp
            )
            self.beginInsertRows(
                QModelIndex(), visible_insert_index, visible_insert_index
            )
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

    def _binary_search_insert_position(self, timestamp: Union[datetime, float]) -> int:
        """Find the position where a timestamp should be inserted to maintain sort order."""
        left, right = 0, len(self.log_entries)

        while left < right:
            mid = (left + right) // 2
            if self.log_entries[mid].timestamp <= timestamp:
                left = mid + 1
            else:
                right = mid

        return left

    def _binary_search_visible_insert_position(
        self, timestamp: Union[datetime, float]
    ) -> int:
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
                # Include None/empty values - they are valid filter options
                unique_values.add(value)

        # Return sorted list with None values at the top for easy access
        sorted_values = []
        if None in unique_values:
            sorted_values.append(None)
        sorted_values.extend(sorted([v for v in unique_values if v is not None]))
        
        return sorted_values

    def clear_entries(self):
        """Clear all log entries."""
        self.beginResetModel()
        self.log_entries.clear()
        self.visible_entries.clear()
        self.entry_display_cache.clear()
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
        """Ultra-fast data method using pre-computed cache."""
        row = index.row()
        col = index.column()

        if not (0 <= row < len(self.visible_entries)):
            return None

        entry = self.visible_entries[row]
        cached_data = self._get_cached_entry_data(entry)

        if role == Qt.DisplayRole:
            column_name = self.visible_columns[col]
            return cached_data["formatted_fields"][column_name]

        elif role == Qt.UserRole:
            # Return the raw value for filtering/sorting
            column_name = self.visible_columns[col]
            if column_name == self.SOURCE_FILE_COLUMN:
                return entry.file_path
            return entry.fields.get(column_name)

        elif role == Qt.BackgroundRole:
            return cached_data["file_color"]

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
        schema_field_names = {field["name"] for field in self.schema.fields}
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
