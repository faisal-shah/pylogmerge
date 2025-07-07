"""
Panel Widgets

Contains panel components for the activity bar system, including the base panel
class and specific panel implementations.
"""

from pathlib import Path
from typing import List

from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QListWidget,
    QMessageBox,
    QDialog,
)
from PyQt5.QtCore import pyqtSignal, Qt

from ..constants import (
    PANEL_MIN_WIDTH,
    PANEL_MAX_WIDTH,
    SIDEBAR_CONTENT_MARGINS,
    LOG_FILES_TITLE,
    TITLE_LABEL_STYLE,
)
from .file_list import FileListWidget, FileListItemWidget


class FilePickerPanel(QWidget):
    """Panel for file picker functionality - contains all file management controls."""

    files_changed = pyqtSignal()  # Signal emitted when file list changes

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        """Set up the file picker panel UI."""
        self.setMinimumWidth(PANEL_MIN_WIDTH)
        self.setMaximumWidth(PANEL_MAX_WIDTH)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(*SIDEBAR_CONTENT_MARGINS)

        # Title
        title_label = QLabel(LOG_FILES_TITLE)
        title_label.setStyleSheet(TITLE_LABEL_STYLE)
        layout.addWidget(title_label)

        # Select All / Deselect All buttons
        button_layout = QHBoxLayout()

        self.select_all_btn = QPushButton("Select All")
        self.select_all_btn.clicked.connect(self.select_all_files)
        button_layout.addWidget(self.select_all_btn)

        self.deselect_all_btn = QPushButton("Deselect All")
        self.deselect_all_btn.clicked.connect(self.deselect_all_files)
        button_layout.addWidget(self.deselect_all_btn)

        layout.addLayout(button_layout)

        # File list
        self.file_list = FileListWidget()
        self.file_list.checkbox_changed.connect(self.files_changed.emit)
        layout.addWidget(self.file_list, 1)

        # Add/Remove buttons
        control_layout = QHBoxLayout()

        self.add_btn = QPushButton("➕")
        self.add_btn.setToolTip("Add log files or directory")
        self.add_btn.clicked.connect(self.add_files)
        control_layout.addWidget(self.add_btn)

        self.remove_btn = QPushButton("➖")
        self.remove_btn.setToolTip("Remove selected files")
        self.remove_btn.clicked.connect(self.remove_selected_files)
        control_layout.addWidget(self.remove_btn)

        control_layout.addStretch()  # Push buttons to the left

        layout.addLayout(control_layout)

        # Enable keyboard shortcuts
        self.file_list.keyPressEvent = self.handle_key_press

        # Set panel background
        self.setStyleSheet(
            """
            FilePickerPanel {
                background-color: #fafafa;
                border-right: 1px solid #ddd;
            }
        """
        )

    def handle_key_press(self, event):
        """Handle keyboard events for the file list."""
        if event.key() == Qt.Key_Delete:
            self.remove_selected_files()
        else:
            # Call the original keyPressEvent
            QListWidget.keyPressEvent(self.file_list, event)

    def add_files(self):
        """Open tabbed dialog to add log files."""
        # Import here to avoid circular imports
        from ..dialogs import AddFilesDialog

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
                    message = f"File '{skipped_files[0]}' is already in the list."
                else:
                    message = f"{len(skipped_files)} files were already in the list and skipped."

                QMessageBox.information(self, "Duplicate Files", message)

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
                "Remove Files",
                f"Remove {len(selected_items)} selected files?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
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
