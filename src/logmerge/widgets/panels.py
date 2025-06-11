"""
Panel Widgets

Contains panel components for the activity bar system, including the base panel
class and specific panel implementations.
"""

from pathlib import Path
from typing import List, Optional

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QListWidget,
    QMessageBox, QDialog
)
from PyQt5.QtCore import pyqtSignal, Qt

from ..constants import (
    PANEL_MIN_WIDTH, PANEL_MAX_WIDTH, SIDEBAR_CONTENT_MARGINS,
    LOG_FILES_TITLE, TITLE_LABEL_STYLE, SELECT_ALL_TEXT, DESELECT_ALL_TEXT,
    ADD_BUTTON_EMOJI, REMOVE_BUTTON_EMOJI, ADD_FILES_TOOLTIP, REMOVE_FILES_TOOLTIP,
    DUPLICATE_FILE_MESSAGE_SINGLE, DUPLICATE_FILES_MESSAGE_MULTIPLE,
    DUPLICATE_FILES_DIALOG_TITLE, REMOVE_FILES_DIALOG_TITLE,
    REMOVE_MULTIPLE_FILES_CONFIRM
)
from .file_list import FileListWidget, FileListItemWidget


class BasePanel(QWidget):
    """Abstract base class for activity bar panels."""
    
    def __init__(self, panel_name: str, parent=None):
        super().__init__(parent)
        self.panel_name = panel_name
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the panel UI - to be implemented by subclasses."""
        raise NotImplementedError("Subclasses must implement setup_ui()")
    
    def get_panel_name(self) -> str:
        """Return the panel name."""
        return self.panel_name


class FilePickerPanel(BasePanel):
    """Panel for file picker functionality - contains all file management controls."""
    
    files_changed = pyqtSignal()  # Signal emitted when file list changes
    
    def __init__(self, parent=None):
        super().__init__("files", parent)
    
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
        layout.addWidget(self.file_list, 1)
        
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
        
        # Enable keyboard shortcuts
        self.file_list.keyPressEvent = self.handle_key_press
        
        # Set panel background
        self.setStyleSheet("""
            FilePickerPanel {
                background-color: #fafafa;
                border-right: 1px solid #ddd;
            }
        """)
    
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


class PanelContainer(QWidget):
    """Container widget that manages showing/hiding panels."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_panel = None
        self.panels = {}
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the panel container."""
        # Use a layout that allows us to show/hide panels
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        
        # Initially hidden
        self.hide()
    
    def add_panel(self, panel: BasePanel):
        """Add a panel to the container."""
        panel_name = panel.get_panel_name()
        self.panels[panel_name] = panel
        # Don't add to layout yet - we'll show/hide as needed
        panel.setParent(self)
        panel.hide()
    
    def show_panel(self, panel_name: str):
        """Show the specified panel and hide others."""
        if panel_name not in self.panels:
            return
        
        # Hide current panel if any
        if self.current_panel:
            self.current_panel.hide()
            self.layout.removeWidget(self.current_panel)
        
        # Show new panel
        new_panel = self.panels[panel_name]
        self.layout.addWidget(new_panel)
        new_panel.show()
        self.current_panel = new_panel
        
        # Show the container itself and ensure it has proper width
        self.show()
        
        # Request minimum width from the panel being shown
        if hasattr(new_panel, 'minimumWidth'):
            self.setMinimumWidth(new_panel.minimumWidth())
    
    def hide_panel(self):
        """Hide the currently visible panel."""
        if self.current_panel:
            self.current_panel.hide()
            self.layout.removeWidget(self.current_panel)
            self.current_panel = None
        
        # Hide the container itself
        self.hide()
        self.setMinimumWidth(0)
    
    def get_current_panel_name(self) -> Optional[str]:
        """Return the name of the currently visible panel, or None."""
        if self.current_panel:
            return self.current_panel.get_panel_name()
        return None
