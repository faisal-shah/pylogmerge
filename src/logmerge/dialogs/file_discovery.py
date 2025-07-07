"""
File Discovery Results Dialog

Dialog to show discovered files and allow user to confirm addition.
"""

from pathlib import Path
from typing import List

from PyQt5.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QDialogButtonBox,
)


class FileDiscoveryResultsDialog(QDialog):
    """Dialog to show discovered files and allow user to confirm addition."""

    def __init__(
        self, found_files: List[str], directory: str, regex_pattern: str, parent=None
    ):
        super().__init__(parent)
        self.found_files = found_files
        self.directory = directory
        self.regex_pattern = regex_pattern
        self.setup_ui()

    def setup_ui(self):
        """Set up the dialog UI."""
        self.setWindowTitle("Files Found")
        self.setModal(True)
        self.resize(600, 400)

        layout = QVBoxLayout()

        # Summary label
        summary_text = f"Found {len(self.found_files)} files matching pattern '{self.regex_pattern}' in directory '{self.directory}'"
        summary_label = QLabel(summary_text)
        summary_label.setWordWrap(True)
        summary_label.setStyleSheet("font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(summary_label)

        # File list
        if self.found_files:
            files_label = QLabel("Files to be added:")
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
            no_files_label.setStyleSheet("color: #666; font-style: italic;")
            layout.addWidget(no_files_label)

        # Buttons
        button_box = QDialogButtonBox()
        if self.found_files:
            add_button = button_box.addButton(
                "Add All Files", QDialogButtonBox.AcceptRole
            )
            add_button.setDefault(True)

        button_box.addButton("Cancel", QDialogButtonBox.RejectRole)

        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        self.setLayout(layout)
