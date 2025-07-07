"""
Column Configuration Dialog

Dialog for configuring which columns to display and their order.
"""

from typing import List

from PyQt5.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QDialogButtonBox,
)
from PyQt5.QtCore import Qt


class ColumnConfigurationDialog(QDialog):
    """Dialog for configuring which columns to display and their order."""

    def __init__(self, schema, visible_columns: List[str], parent=None):
        super().__init__(parent)
        self.schema = schema
        self.visible_columns = visible_columns.copy()  # Current configuration

        # Import here to avoid circular imports
        from ..widgets.log_table import LogTableModel

        # Build list of all possible columns (schema fields + virtual columns)
        all_columns = [LogTableModel.SOURCE_FILE_COLUMN] + [
            field["name"] for field in schema.fields
        ]
        self.available_columns = [
            col for col in all_columns if col not in visible_columns
        ]
        self.LogTableModel = LogTableModel  # Store reference for use in methods
        self.setup_ui()

    def setup_ui(self):
        """Set up the dialog UI with dual-list selection pattern."""
        self.setWindowTitle("Configure Columns")
        self.setModal(True)
        self.resize(600, 500)

        layout = QVBoxLayout()

        # Instructions
        instructions = QLabel(
            """
<b>Configure Visible Columns</b><br><br>
Select which columns to display in the log table and arrange their order.
Use the buttons to move columns between available and visible lists.
"""
        )
        instructions.setWordWrap(True)
        layout.addWidget(instructions)

        # Main dual-list area
        main_layout = QHBoxLayout()

        # Available columns (left side)
        left_layout = QVBoxLayout()
        left_layout.addWidget(QLabel("Available Columns:"))
        self.available_list = QListWidget()
        self.available_list.setSelectionMode(QListWidget.ExtendedSelection)
        self.available_list.itemDoubleClicked.connect(self.add_selected_columns)
        left_layout.addWidget(self.available_list)

        # Control buttons (center)
        button_layout = QVBoxLayout()
        button_layout.addStretch()

        self.add_button = QPushButton("Add >")
        self.add_button.setToolTip("Add selected columns to visible list")
        self.add_button.clicked.connect(self.add_selected_columns)
        button_layout.addWidget(self.add_button)

        self.add_all_button = QPushButton("Add All >>")
        self.add_all_button.setToolTip("Add all available columns to visible list")
        self.add_all_button.clicked.connect(self.add_all_columns)
        button_layout.addWidget(self.add_all_button)

        button_layout.addSpacing(20)

        self.remove_button = QPushButton("< Remove")
        self.remove_button.setToolTip("Remove selected columns from visible list")
        self.remove_button.clicked.connect(self.remove_selected_columns)
        button_layout.addWidget(self.remove_button)

        self.remove_all_button = QPushButton("<< Remove")
        self.remove_all_button.setToolTip("Remove all columns from visible list")
        self.remove_all_button.clicked.connect(self.remove_all_columns)
        button_layout.addWidget(self.remove_all_button)

        button_layout.addStretch()

        # Visible columns (right side)
        right_layout = QVBoxLayout()
        right_layout.addWidget(QLabel("Visible Columns (in display order):"))
        self.visible_list = QListWidget()
        self.visible_list.setSelectionMode(QListWidget.ExtendedSelection)
        self.visible_list.itemDoubleClicked.connect(self.remove_selected_columns)
        right_layout.addWidget(self.visible_list)

        # Ordering buttons for visible list
        order_layout = QHBoxLayout()

        self.move_up_button = QPushButton("Move Up")
        self.move_up_button.setToolTip("Move selected columns up in display order")
        self.move_up_button.clicked.connect(self.move_columns_up)
        order_layout.addWidget(self.move_up_button)

        self.move_down_button = QPushButton("Move Down")
        self.move_down_button.setToolTip("Move selected columns down in display order")
        self.move_down_button.clicked.connect(self.move_columns_down)
        order_layout.addWidget(self.move_down_button)

        order_layout.addStretch()
        right_layout.addLayout(order_layout)

        # Assemble main layout
        main_layout.addLayout(left_layout, 1)
        main_layout.addLayout(button_layout, 0)
        main_layout.addLayout(right_layout, 1)
        layout.addLayout(main_layout)

        # Dialog buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok
            | QDialogButtonBox.Cancel
            | QDialogButtonBox.RestoreDefaults
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        # Connect restore defaults button
        restore_button = button_box.button(QDialogButtonBox.RestoreDefaults)
        restore_button.clicked.connect(self.restore_defaults)
        restore_button.setToolTip("Reset to show all columns in default order")

        layout.addWidget(button_box)
        self.setLayout(layout)

        # Populate lists with current configuration
        self.populate_lists()

        # Connect selection change events to update button states
        self.available_list.itemSelectionChanged.connect(self.update_button_states)
        self.visible_list.itemSelectionChanged.connect(self.update_button_states)
        self.update_button_states()

    def populate_lists(self):
        """Populate the available and visible lists based on current configuration."""
        # Clear both lists
        self.available_list.clear()
        self.visible_list.clear()

        # Add available columns
        for column_name in self.available_columns:
            if column_name == self.LogTableModel.SOURCE_FILE_COLUMN:
                # Handle virtual column
                display_text = f"{column_name} (virtual)"
                item = QListWidgetItem(display_text)
                item.setData(Qt.UserRole, column_name)
                item.setToolTip("Virtual column showing the source filename")
                self.available_list.addItem(item)
            else:
                # Find the field to get its display information
                field = next(
                    (f for f in self.schema.fields if f["name"] == column_name), None
                )
                if field:
                    display_text = f"{column_name} ({field['type']})"
                    item = QListWidgetItem(display_text)
                    item.setData(Qt.UserRole, column_name)
                    item.setToolTip(f"Type: {field['type']}")
                    self.available_list.addItem(item)

        # Add visible columns in their current order
        for column_name in self.visible_columns:
            if column_name == self.LogTableModel.SOURCE_FILE_COLUMN:
                # Handle virtual column
                display_text = f"{column_name} (virtual)"
                item = QListWidgetItem(display_text)
                item.setData(Qt.UserRole, column_name)
                item.setToolTip("Virtual column showing the source filename")
                self.visible_list.addItem(item)
            else:
                # Find the field to get its display information
                field = next(
                    (f for f in self.schema.fields if f["name"] == column_name), None
                )
                if field:
                    display_text = f"{column_name} ({field['type']})"
                    item = QListWidgetItem(display_text)
                    item.setData(Qt.UserRole, column_name)
                    item.setToolTip(f"Type: {field['type']}")
                    self.visible_list.addItem(item)

    def add_selected_columns(self):
        """Move selected columns from available to visible list."""
        selected_items = self.available_list.selectedItems()
        if not selected_items:
            return

        # Get column names to move
        columns_to_move = [item.data(Qt.UserRole) for item in selected_items]

        # Update internal lists
        for column_name in columns_to_move:
            if column_name in self.available_columns:
                self.available_columns.remove(column_name)
                self.visible_columns.append(column_name)

        # Refresh display
        self.populate_lists()
        self.update_button_states()

    def add_all_columns(self):
        """Move all available columns to visible list."""
        # Move all available columns to visible
        self.visible_columns.extend(self.available_columns)
        self.available_columns.clear()

        # Refresh display
        self.populate_lists()
        self.update_button_states()

    def remove_selected_columns(self):
        """Move selected columns from visible to available list."""
        selected_items = self.visible_list.selectedItems()
        if not selected_items:
            return

        # Get column names to move
        columns_to_move = [item.data(Qt.UserRole) for item in selected_items]

        # Update internal lists
        for column_name in columns_to_move:
            if column_name in self.visible_columns:
                self.visible_columns.remove(column_name)
                self.available_columns.append(column_name)

        # Sort available columns alphabetically for easier browsing
        self.available_columns.sort()

        # Refresh display
        self.populate_lists()
        self.update_button_states()

    def remove_all_columns(self):
        """Move all visible columns to available list."""
        # Move all visible columns to available
        self.available_columns.extend(self.visible_columns)
        self.visible_columns.clear()

        # Sort available columns alphabetically
        self.available_columns.sort()

        # Refresh display
        self.populate_lists()
        self.update_button_states()

    def move_columns_up(self):
        """Move selected columns up in the visible list."""
        selected_items = self.visible_list.selectedItems()
        if not selected_items:
            return

        # Get selected rows (need to work with indices)
        selected_rows = sorted([self.visible_list.row(item) for item in selected_items])

        # Can't move up if first item is selected
        if selected_rows[0] == 0:
            return

        # Move each selected item up one position
        for row in selected_rows:
            column_name = self.visible_columns.pop(row)
            self.visible_columns.insert(row - 1, column_name)

        # Refresh display and maintain selection
        self.populate_lists()

        # Restore selection (shifted up by one)
        for row in selected_rows:
            if row > 0:
                self.visible_list.item(row - 1).setSelected(True)

        self.update_button_states()

    def move_columns_down(self):
        """Move selected columns down in the visible list."""
        selected_items = self.visible_list.selectedItems()
        if not selected_items:
            return

        # Get selected rows (need to work with indices)
        selected_rows = sorted(
            [self.visible_list.row(item) for item in selected_items], reverse=True
        )

        # Can't move down if last item is selected
        if selected_rows[0] == len(self.visible_columns) - 1:
            return

        # Move each selected item down one position (in reverse order)
        for row in selected_rows:
            column_name = self.visible_columns.pop(row)
            self.visible_columns.insert(row + 1, column_name)

        # Refresh display and maintain selection
        self.populate_lists()

        # Restore selection (shifted down by one)
        for row in reversed(selected_rows):
            if row < len(self.visible_columns) - 1:
                self.visible_list.item(row + 1).setSelected(True)

        self.update_button_states()

    def restore_defaults(self):
        """Restore default configuration (all columns in schema order)."""
        # Reset to show all columns in schema order including virtual columns
        self.visible_columns = [self.LogTableModel.SOURCE_FILE_COLUMN] + [
            field["name"] for field in self.schema.fields
        ]
        self.available_columns = []

        # Refresh display
        self.populate_lists()
        self.update_button_states()

    def update_button_states(self):
        """Update button enabled/disabled states based on current selections."""
        has_available_selection = len(self.available_list.selectedItems()) > 0
        has_visible_selection = len(self.visible_list.selectedItems()) > 0
        has_available_items = self.available_list.count() > 0
        has_visible_items = self.visible_list.count() > 0

        # Add/Remove buttons
        self.add_button.setEnabled(has_available_selection)
        self.add_all_button.setEnabled(has_available_items)
        self.remove_button.setEnabled(has_visible_selection)
        self.remove_all_button.setEnabled(has_visible_items)

        # Move buttons
        self.move_up_button.setEnabled(has_visible_selection and has_visible_items)
        self.move_down_button.setEnabled(has_visible_selection and has_visible_items)

    def get_column_configuration(self) -> List[str]:
        """Return the current visible columns configuration."""
        return self.visible_columns.copy()
