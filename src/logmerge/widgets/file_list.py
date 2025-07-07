"""
File List Widgets

Contains widgets for displaying and managing the list of log files.
"""

from pathlib import Path

from PyQt5.QtWidgets import (
    QListWidget,
    QWidget,
    QHBoxLayout,
    QCheckBox,
    QLabel,
    QListWidgetItem,
)
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QColor

from ..constants import (
    DEFAULT_FILE_COLORS,
    FILE_ITEM_CONTENT_MARGINS,
    COLOR_INDICATOR_SIZE,
    COLOR_INDICATOR_STYLE_TEMPLATE,
)


class FileListWidget(QListWidget):
    """Custom list widget for displaying log files with checkboxes and color indicators."""

    checkbox_changed = pyqtSignal()  # Signal emitted when any checkbox state changes

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSelectionMode(
            QListWidget.ExtendedSelection
        )  # Allow Ctrl/Shift selection

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
        self.checkbox.setChecked(True)  # Default to checked
        self.checkbox.stateChanged.connect(self.checkbox_changed.emit)
        layout.addWidget(self.checkbox)

        # Color indicator
        self.color_label = QLabel()
        self.color_label.setFixedSize(*COLOR_INDICATOR_SIZE)
        self.color_label.setStyleSheet(
            COLOR_INDICATOR_STYLE_TEMPLATE.format(color=self.color.name())
        )
        layout.addWidget(self.color_label)

        # File name label
        file_name = Path(self.file_path).name
        self.file_label = QLabel(file_name)
        self.file_label.setToolTip(self.file_path)  # Show full path on hover
        layout.addWidget(self.file_label, 1)

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
        self.color_label.setStyleSheet(
            COLOR_INDICATOR_STYLE_TEMPLATE.format(color=color.name())
        )
