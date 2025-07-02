"""
File Discovery Results Dialog

Dialog to show discovered files and allow user to confirm addition.
"""

from pathlib import Path
from typing import List

from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QListWidget, QListWidgetItem, QDialogButtonBox

from ..constants import (
    FILES_FOUND_DIALOG_TITLE, FILE_DISCOVERY_DIALOG_SIZE, FILES_FOUND_SUMMARY_FORMAT,
    SUMMARY_LABEL_STYLE, FILES_TO_ADD_LABEL, NO_FILES_STYLE, ADD_ALL_FILES_TEXT, CANCEL_TEXT
)


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
