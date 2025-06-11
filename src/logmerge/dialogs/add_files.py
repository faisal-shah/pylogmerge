"""
Add Files Dialog

Dialog with tabs for selecting individual files or directory + regex.
"""

import re
from pathlib import Path
from typing import List

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget, QLabel, 
    QListWidget, QListWidgetItem, QPushButton, QLineEdit, QCheckBox,
    QDialogButtonBox, QFileDialog, QMessageBox
)
from PyQt5.QtCore import Qt

from .file_discovery import FileDiscoveryResultsDialog
from ..constants import (
    ADD_FILES_DIALOG_TITLE, ADD_FILES_DIALOG_SIZE, SELECT_FILES_TAB, DIRECTORY_REGEX_TAB,
    FILES_TAB_INSTRUCTIONS, BROWSE_FILES_TEXT, CLEAR_BUTTON_TEXT, DIRECTORY_TAB_INSTRUCTIONS,
    DIRECTORY_LABEL, DIRECTORY_PLACEHOLDER, BROWSE_BUTTON_TEXT, REGEX_PATTERN_LABEL,
    DEFAULT_REGEX_PATTERN, REGEX_PLACEHOLDER, DEFAULT_RECURSIVE_SEARCH, PREVIEW_FILES_TEXT,
    REGEX_EXAMPLES_HTML, INFO_LABEL_STYLE, LOG_FILE_FILTER, ENTER_REGEX_MESSAGE,
    REGEX_WARNING_STYLE, VALID_REGEX_MESSAGE, REGEX_VALID_STYLE, INVALID_REGEX_MESSAGE_FORMAT,
    REGEX_ERROR_STYLE, REGEX_INPUT_ERROR_STYLE, SEARCH_ERROR_DIALOG_TITLE, SEARCH_ERROR_MESSAGE_FORMAT,
    NO_DIRECTORY_DIALOG_TITLE, NO_DIRECTORY_MESSAGE, INVALID_REGEX_DIALOG_TITLE,
    INVALID_REGEX_MESSAGE, NO_FILES_FOUND_DIALOG_TITLE, NO_FILES_FOUND_MESSAGE
)


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
                return
                
        self.accept()
