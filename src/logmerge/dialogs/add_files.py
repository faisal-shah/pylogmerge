"""
Add Files Dialog

Dialog with tabs for selecting individual files or directory + regex.
"""

import re
from pathlib import Path
from typing import List

from PyQt5.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QTabWidget,
    QWidget,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QLineEdit,
    QCheckBox,
    QDialogButtonBox,
    QFileDialog,
    QMessageBox,
)
from PyQt5.QtCore import Qt

from .file_discovery import FileDiscoveryResultsDialog


class AddFilesDialog(QDialog):
    """Dialog with tabs for selecting individual files or directory + regex."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.selected_files = []
        self.setup_ui()

    def setup_ui(self):
        """Set up the tabbed dialog UI."""
        self.setWindowTitle("Add Log Files")
        self.setModal(True)
        self.resize(500, 400)

        layout = QVBoxLayout()

        # Create tab widget
        self.tab_widget = QTabWidget()

        # Tab 1: Select Files
        self.files_tab = self.create_files_tab()
        self.tab_widget.addTab(self.files_tab, "Select Files")

        # Tab 2: Directory + Regex
        self.directory_tab = self.create_directory_tab()
        self.tab_widget.addTab(self.directory_tab, "Directory + Regex")

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
        instructions = QLabel("Select individual log files to add to the viewer.")
        instructions.setWordWrap(True)
        layout.addWidget(instructions)

        # File selection area
        self.selected_files_list = QListWidget()
        layout.addWidget(self.selected_files_list)

        # Buttons
        button_layout = QHBoxLayout()

        self.browse_files_btn = QPushButton("Browse Files...")
        self.browse_files_btn.clicked.connect(self.browse_individual_files)
        button_layout.addWidget(self.browse_files_btn)

        self.clear_files_btn = QPushButton("Clear")
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
        instructions = QLabel(
            "Select a directory and specify a regex pattern to match log files."
        )
        instructions.setWordWrap(True)
        layout.addWidget(instructions)

        # Directory selection
        dir_layout = QHBoxLayout()
        dir_layout.addWidget(QLabel("Directory:"))
        self.directory_edit = QLineEdit()
        self.directory_edit.setReadOnly(True)
        self.directory_edit.setPlaceholderText(
            "Click 'Browse' to select a directory..."
        )
        dir_layout.addWidget(self.directory_edit)

        self.browse_dir_btn = QPushButton("Browse...")
        self.browse_dir_btn.clicked.connect(self.browse_directory)
        dir_layout.addWidget(self.browse_dir_btn)
        layout.addLayout(dir_layout)

        # Regex pattern
        regex_layout = QHBoxLayout()
        regex_layout.addWidget(QLabel("Regex Pattern:"))
        self.regex_edit = QLineEdit()
        self.regex_edit.setText(".*\\.log$")  # Default pattern
        self.regex_edit.setPlaceholderText("Enter regex pattern (e.g., .*\\.log$)")
        self.regex_edit.textChanged.connect(self.validate_regex)
        regex_layout.addWidget(self.regex_edit)
        layout.addLayout(regex_layout)

        # Regex validation message
        self.regex_status_label = QLabel("")
        self.regex_status_label.setStyleSheet("color: green;")
        layout.addWidget(self.regex_status_label)

        # Recursive option
        self.recursive_checkbox = QCheckBox("Search subdirectories recursively")
        self.recursive_checkbox.setChecked(True)  # Default to recursive
        layout.addWidget(self.recursive_checkbox)

        # Preview button
        self.preview_btn = QPushButton("Preview Matching Files...")
        self.preview_btn.clicked.connect(self.preview_directory_files)
        self.preview_btn.setEnabled(False)  # Enabled when directory is selected
        layout.addWidget(self.preview_btn)

        # Examples
        examples_label = QLabel(
            """
<b>Regex Examples:</b><br>
• <code>.*\\.log$</code> - All .log files<br>
• <code>.*/error.*\\.log$</code> - Log files containing 'error' in any subdirectory<br>
• <code>^daily/.*</code> - Files only in 'daily' directory<br>
• <code>.*\\.(log|txt)$</code> - All .log and .txt files
"""
        )
        examples_label.setWordWrap(True)
        examples_label.setStyleSheet("color: #666; font-size: 10px; margin-top: 10px;")
        layout.addWidget(examples_label)

        layout.addStretch()
        tab.setLayout(layout)
        return tab

    def browse_individual_files(self):
        """Browse for individual files."""
        file_dialog = QFileDialog()
        file_dialog.setFileMode(QFileDialog.ExistingFiles)
        file_dialog.setNameFilter("Log files (*.log *.txt);;All files (*)")
        file_dialog.setViewMode(QFileDialog.Detail)

        if file_dialog.exec_() == QFileDialog.Accepted:
            files = file_dialog.selectedFiles()
            for file_path in files:
                # Check for duplicates in the current selection
                if file_path not in [
                    self.selected_files_list.item(i).data(Qt.UserRole)
                    for i in range(self.selected_files_list.count())
                ]:
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
            self.regex_status_label.setText("Enter a regex pattern")
            self.regex_status_label.setStyleSheet("color: orange;")
            self.regex_edit.setStyleSheet("")
            return False

        try:
            re.compile(pattern, re.IGNORECASE)
            self.regex_status_label.setText("✓ Valid regex pattern")
            self.regex_status_label.setStyleSheet("color: green;")
            self.regex_edit.setStyleSheet("")
            return True
        except re.error as e:
            self.regex_status_label.setText(f"✗ Invalid regex: {str(e)}")
            self.regex_status_label.setStyleSheet("color: red;")
            self.regex_edit.setStyleSheet("border: 1px solid red;")
            return False

    def find_matching_files(
        self, directory: str, pattern: str, recursive: bool
    ) -> List[str]:
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
            QMessageBox.warning(
                self,
                "Search Error",
                "Error searching for files: {error}".format(error=str(e)),
            )
            return []

    def preview_directory_files(self):
        """Preview files that would be matched by the directory + regex."""
        directory = self.directory_edit.text().strip()
        pattern = self.regex_edit.text().strip()
        recursive = self.recursive_checkbox.isChecked()

        if not directory:
            QMessageBox.warning(
                self, "No Directory", "Please select a directory first."
            )
            return

        if not self.validate_regex():
            QMessageBox.warning(
                self, "Invalid Regex", "Please enter a valid regex pattern."
            )
            return

        # Find matching files
        matching_files = self.find_matching_files(directory, pattern, recursive)

        # Show results dialog
        results_dialog = FileDiscoveryResultsDialog(
            matching_files, directory, pattern, self
        )
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
                QMessageBox.warning(
                    self, "No Directory", "Please select a directory first."
                )
                return

            if not self.validate_regex():
                QMessageBox.warning(
                    self, "Invalid Regex", "Please enter a valid regex pattern."
                )
                return

            # Find matching files
            matching_files = self.find_matching_files(directory, pattern, recursive)

            if not matching_files:
                QMessageBox.information(
                    self,
                    "No Files Found",
                    "No files found matching the specified pattern.",
                )
                return

            # Show results and get confirmation
            results_dialog = FileDiscoveryResultsDialog(
                matching_files, directory, pattern, self
            )
            if results_dialog.exec_() == QDialog.Accepted:
                self.selected_files = matching_files
            else:
                return

        self.accept()
