"""
Filter Panel Widget

Provides filtering UI for log entries based on schema field types.
Dynamically creates appropriate filter widgets for each field in the schema.
"""

from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QCheckBox,
    QLineEdit,
    QSpinBox,
    QDoubleSpinBox,
    QListWidget,
    QListWidgetItem,
    QDateTimeEdit,
    QScrollArea,
    QSizePolicy,
    QPushButton,
)
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QDoubleValidator

from ..constants import (
    PANEL_MIN_WIDTH,
    PANEL_MAX_WIDTH,
    SIDEBAR_CONTENT_MARGINS,
    TITLE_LABEL_STYLE,
    FILTERS_TITLE,
)


class FilterWidget(QWidget):
    """Base class for individual field filter widgets."""

    def __init__(self, field_name: str, field_schema: dict, parent=None):
        super().__init__(parent)
        self.field_name = field_name
        self.field_schema = field_schema
        self.enabled = False
        self.setup_ui()

    def setup_ui(self):
        """Set up the basic filter UI structure."""
        layout = QVBoxLayout()
        layout.setContentsMargins(2, 0, 2, 0)  # Zero top/bottom margins
        layout.setSpacing(0)  # Zero spacing between header and filter widget

        # Header with field name and enable checkbox
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(2)  # Tight spacing between checkbox and label

        self.enable_cb = QCheckBox()
        self.enable_cb.setChecked(False)
        self.enable_cb.toggled.connect(self.on_enabled_changed)

        field_label = QLabel(self.field_name)

        header_layout.addWidget(self.enable_cb)
        header_layout.addWidget(field_label)
        header_layout.addStretch()

        # Create header widget with fixed height to minimize space
        header_widget = QWidget()
        header_widget.setLayout(header_layout)
        header_widget.setFixedHeight(16)  # Very compact header
        header_widget.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)

        layout.addWidget(header_widget)

        # Filter-specific widget (implemented by subclasses)
        self.filter_widget = self.create_filter_widget()
        self.filter_widget.setEnabled(False)
        layout.addWidget(self.filter_widget)

        # Add subtle styling to make filter widgets more distinct
        self.setStyleSheet(
            """
            FilterWidget {
                background-color: #fafafa;
                border: 1px solid #e0e0e0;
                border-radius: 3px;
                padding: 3px;
                margin: 1px;
            }
        """
        )

        self.setLayout(layout)

    def create_filter_widget(self) -> QWidget:
        """Create the filter-specific widget. Implemented by subclasses."""
        raise NotImplementedError

    def on_enabled_changed(self, enabled: bool):
        """Handle filter enable/disable."""
        self.enabled = enabled
        self.filter_widget.setEnabled(enabled)

    def get_filter_value(self):
        """Get the current filter value. Implemented by subclasses."""
        raise NotImplementedError

    def is_filter_active(self) -> bool:
        """Check if this filter is active."""
        return self.enabled


class DiscreteFilterWidget(FilterWidget):
    """Filter widget for discrete values (enum, is_discrete fields)."""

    def __init__(
        self, field_name: str, field_schema: dict, values: list = None, parent=None
    ):
        self.values = values or []
        self._is_handling_change = False  # Flag to prevent recursion in on_item_changed
        super().__init__(field_name, field_schema, parent)

    def create_filter_widget(self) -> QWidget:
        """Create a list widget with checkboxes for discrete values."""
        self.list_widget = QListWidget()
        self.list_widget.setMaximumHeight(100)  # Reduced from 120
        self.list_widget.setMinimumHeight(40)  # Reduced from 60
        self.list_widget.setSelectionMode(
            QListWidget.ExtendedSelection
        )  # Enable multi-selection

        # Set very tight spacing and size policy for list items
        self.list_widget.setSpacing(0)  # Remove item spacing entirely
        self.list_widget.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)

        # Make list items more compact with tighter styling
        self.list_widget.setStyleSheet(
            """
            QListWidget {
                border: 1px solid #ccc;
                margin: 0px;
                padding: 0px;
            }
            QListWidget::item {
                padding: 1px 2px;
                margin: 0px;
                border: none;
                height: 16px;
                color: black;
                background-color: transparent;
            }
            QListWidget::item:selected {
                background-color: #e3f2fd;
                color: black;
                border: 1px solid #2196f3;
            }
            QListWidget::item:hover {
                background-color: #f5f5f5;
                color: black;
            }
            QListWidget::item:selected:hover {
                background-color: #bbdefb;
                color: black;
                border: 1px solid #1976d2;
            }
        """
        )

        # Populate with values - sort with None at the top for easy access
        sorted_values = []
        if None in self.values:
            sorted_values.append(None)
        
        # Sort the non-None values, handling both enum dictionaries and simple values
        non_none_values = [v for v in self.values if v is not None]
        if non_none_values:
            if isinstance(non_none_values[0], dict):
                # For enum values (dictionaries), sort by the 'value' key
                sorted_values.extend(sorted(non_none_values, key=lambda x: str(x.get('value', ''))))
            else:
                # For simple values (is_discrete fields), sort normally
                sorted_values.extend(sorted(non_none_values))
        
        for value in sorted_values:
            if isinstance(value, dict):  # enum format
                display_text = f"{value['value']} ({value['name']})"
                item_value = value["value"]
            else:  # simple value
                # Handle None/empty values with user-friendly display
                if value is None:
                    display_text = "(empty)"
                    item_value = None
                else:
                    display_text = str(value)
                    item_value = value

            item = QListWidgetItem(display_text)
            item.setData(Qt.UserRole, item_value)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Checked)  # Default to all selected
            self.list_widget.addItem(item)

        # Connect signal for checkbox changes. Rely on default QListWidget selection behavior.
        self.list_widget.itemChanged.connect(self.on_item_changed)

        return self.list_widget

    def on_item_changed(self, item):
        """Handle checkbox changes. If multiple items are selected, apply the change to all."""
        # Prevent recursion if we are already handling a change
        if self._is_handling_change:
            return

        selected_items = self.list_widget.selectedItems()

        # If more than one item is selected and the item that changed is one of them,
        # apply the new check state to all selected items.
        if len(selected_items) > 1 and item in selected_items:
            self._is_handling_change = True
            new_state = item.checkState()
            try:
                for selected_item in selected_items:
                    if selected_item.checkState() != new_state:
                        selected_item.setCheckState(new_state)
            finally:
                # Ensure the flag is reset even if an error occurs
                self._is_handling_change = False

    def get_filter_value(self):
        """Get list of selected values."""
        if not self.enabled:
            return None

        selected_values = []
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.checkState() == Qt.Checked:
                selected_values.append(item.data(Qt.UserRole))

        return selected_values

    def set_available_values(self, values: list):
        """Update the available values (for dynamic discrete fields)."""
        self.values = values
        self.list_widget.clear()

        # Sort values with None at the top for easy access
        sorted_values = []
        if None in values:
            sorted_values.append(None)
        sorted_values.extend(sorted([v for v in values if v is not None]))

        for value in sorted_values:
            # Handle None/empty values with user-friendly display
            if value is None:
                display_text = "(empty)"
                item_value = None
            else:
                display_text = str(value)
                item_value = value
                
            item = QListWidgetItem(display_text)
            item.setData(Qt.UserRole, item_value)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Checked)
            self.list_widget.addItem(item)


class NumericRangeFilterWidget(FilterWidget):
    """Filter widget for numeric ranges (int, float fields)."""

    def create_filter_widget(self) -> QWidget:
        """Create min/max numeric input widgets."""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)

        # Min value
        min_layout = QHBoxLayout()
        min_layout.addWidget(QLabel("Min:"))

        if self.field_schema.get("type") == "int":
            self.min_input = QSpinBox()
            self.min_input.setRange(-2147483648, 2147483647)
            self.max_input = QSpinBox()
            self.max_input.setRange(-2147483648, 2147483647)
        else:  # float
            self.min_input = QDoubleSpinBox()
            self.min_input.setRange(-1e10, 1e10)
            self.max_input = QDoubleSpinBox()
            self.max_input.setRange(-1e10, 1e10)

        self.min_input.setSpecialValueText("(no limit)")
        self.min_input.setValue(self.min_input.minimum())
        min_layout.addWidget(self.min_input)

        # Max value
        max_layout = QHBoxLayout()
        max_layout.addWidget(QLabel("Max:"))
        self.max_input.setSpecialValueText("(no limit)")
        self.max_input.setValue(self.max_input.maximum())
        max_layout.addWidget(self.max_input)

        layout.addLayout(min_layout)
        layout.addLayout(max_layout)

        widget.setLayout(layout)
        return widget

    def get_filter_value(self):
        """Get the min/max range values."""
        if not self.enabled:
            return None

        min_val = (
            self.min_input.value()
            if self.min_input.value() != self.min_input.minimum()
            else None
        )
        max_val = (
            self.max_input.value()
            if self.max_input.value() != self.max_input.maximum()
            else None
        )

        return {"min": min_val, "max": max_val}


class TextFilterWidget(FilterWidget):
    """Filter widget for text pattern matching."""

    def create_filter_widget(self) -> QWidget:
        """Create text input with regex support."""
        self.text_input = QLineEdit()
        self.text_input.setPlaceholderText("Enter text or regex pattern...")
        return self.text_input

    def get_filter_value(self):
        """Get the text pattern."""
        if not self.enabled:
            return None
        return self.text_input.text().strip()


class DateTimeRangeFilterWidget(FilterWidget):
    """Filter widget for date/time ranges."""

    def create_filter_widget(self) -> QWidget:
        """Create from/to datetime inputs."""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)

        # From datetime
        from_layout = QHBoxLayout()
        from_layout.addWidget(QLabel("From:"))
        self.from_input = QDateTimeEdit()
        self.from_input.setCalendarPopup(True)
        self.from_input.clear()  # Start empty
        from_layout.addWidget(self.from_input)

        # To datetime
        to_layout = QHBoxLayout()
        to_layout.addWidget(QLabel("To:"))
        self.to_input = QDateTimeEdit()
        self.to_input.setCalendarPopup(True)
        self.to_input.clear()  # Start empty
        to_layout.addWidget(self.to_input)

        layout.addLayout(from_layout)
        layout.addLayout(to_layout)

        widget.setLayout(layout)
        return widget

    def get_filter_value(self):
        """Get the datetime range. Validate whatever is currently in the fields."""
        if not self.enabled:
            return None

        from_dt = self.from_input.dateTime().toPyDateTime()
        to_dt = self.to_input.dateTime().toPyDateTime()

        # Simple validation: both must be valid dates
        if from_dt and to_dt:
            return {"from": from_dt, "to": to_dt}

        return None


class FloatTimestampRangeFilterWidget(FilterWidget):
    """Filter widget for float timestamp ranges."""

    def create_filter_widget(self) -> QWidget:
        """Create from/to float timestamp inputs."""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)

        # From timestamp
        from_layout = QHBoxLayout()
        from_layout.addWidget(QLabel("From:"))
        self.from_input = QLineEdit()
        self.from_input.setPlaceholderText("0.000000")
        self.from_input.setValidator(QDoubleValidator())
        from_layout.addWidget(self.from_input)

        # To timestamp
        to_layout = QHBoxLayout()
        to_layout.addWidget(QLabel("To:"))
        self.to_input = QLineEdit()
        self.to_input.setPlaceholderText("999999.999999")
        self.to_input.setValidator(QDoubleValidator())
        to_layout.addWidget(self.to_input)

        layout.addLayout(from_layout)
        layout.addLayout(to_layout)

        widget.setLayout(layout)
        return widget

    def get_filter_value(self):
        """Get the float timestamp range."""
        if not self.enabled:
            return None

        from_text = self.from_input.text().strip()
        to_text = self.to_input.text().strip()

        result = {}
        if from_text:
            try:
                result["from"] = float(from_text)
            except ValueError:
                pass  # Ignore invalid input

        if to_text:
            try:
                result["to"] = float(to_text)
            except ValueError:
                pass  # Ignore invalid input

        return result if result else None


class FilterPanel(QWidget):
    """Panel containing all field filters based on schema."""

    apply_clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.schema = None
        self.filter_widgets = []
        self.setup_ui()

    def setup_ui(self):
        """Set up the filter panel UI."""
        self.setMinimumWidth(PANEL_MIN_WIDTH)
        self.setMaximumWidth(PANEL_MAX_WIDTH)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(*SIDEBAR_CONTENT_MARGINS)

        # Title
        title_label = QLabel(FILTERS_TITLE)
        title_label.setStyleSheet(TITLE_LABEL_STYLE)
        layout.addWidget(title_label)

        # Scroll area for filters
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.filter_container = QWidget()
        self.filter_layout = QVBoxLayout()
        self.filter_layout.setContentsMargins(0, 0, 0, 0)
        self.filter_layout.setSpacing(0)  # Remove spacing between filter widgets

        self.filter_container.setLayout(self.filter_layout)
        scroll_area.setWidget(self.filter_container)

        layout.addWidget(scroll_area)

        # Add Apply button at the bottom
        self.apply_button = QPushButton("Apply Filters")
        self.apply_button.clicked.connect(self.apply_clicked.emit)
        layout.addWidget(self.apply_button)

    def set_schema(self, schema):
        """Set the schema and create filter widgets accordingly."""
        self.schema = schema
        self.clear_filters()

        if not schema:
            return

        for i, field in enumerate(schema.fields):
            filter_widget = self.create_filter_for_field(field)
            if filter_widget:
                self.filter_widgets.append(filter_widget)
                self.filter_layout.addWidget(filter_widget)

                # Add spacing between filter widgets (except for the last one)
                if i < len(schema.fields) - 1:
                    # Create a spacer widget with more vertical space
                    spacer_widget = QWidget()
                    spacer_widget.setFixedHeight(
                        15
                    )  # Increased from 8px to 15px for better separation
                    self.filter_layout.addWidget(spacer_widget)

        # Add stretch at the end
        self.filter_layout.addStretch()

    def create_filter_for_field(self, field_schema: dict) -> FilterWidget:
        """Create appropriate filter widget based on field schema."""
        field_name = field_schema.get("name", "")
        field_type = field_schema.get("type", "")

        # Skip source file field (handled by file picker)
        if field_name == "source_file":
            return None

        # Discrete filters (enum or is_discrete)
        if field_type == "enum":
            enum_values = field_schema.get("enum_values", [])
            return DiscreteFilterWidget(field_name, field_schema, enum_values)
        elif field_schema.get("is_discrete"):
            # For discrete fields, we'll populate values dynamically
            return DiscreteFilterWidget(field_name, field_schema, [])

        # Numeric range filters
        elif field_type in ["int", "float"]:
            return NumericRangeFilterWidget(field_name, field_schema)

        # Text pattern filters
        elif field_type == "string":
            return TextFilterWidget(field_name, field_schema)

        # Date/time range filters
        elif field_type in ["epoch", "strptime"]:
            return DateTimeRangeFilterWidget(field_name, field_schema)

        # Float timestamp range filters
        elif field_type == "float_timestamp":
            return FloatTimestampRangeFilterWidget(field_name, field_schema)

        return None

    def clear_filters(self):
        """Clear all existing filter widgets."""
        for widget in self.filter_widgets:
            widget.setParent(None)
            widget.deleteLater()

        self.filter_widgets.clear()

    def update_discrete_values(self, field_name: str, values: list):
        """Update available values for a discrete field."""
        for widget in self.filter_widgets:
            if (
                isinstance(widget, DiscreteFilterWidget)
                and widget.field_name == field_name
            ):
                widget.set_available_values(values)
                break

    def get_active_filters(self) -> dict:
        """Get all currently active filters in standardized format."""
        field_filters = {}

        for widget in self.filter_widgets:
            if widget.is_filter_active():
                field_name = widget.field_name
                filter_value = widget.get_filter_value()

                if filter_value is None:
                    continue

                # Convert to standardized format based on widget type
                if isinstance(widget, DiscreteFilterWidget):
                    # Convert list to set for faster lookups
                    field_filters[field_name] = {
                        "type": "discrete",
                        "selected": set(filter_value) if filter_value else set(),
                    }
                elif isinstance(widget, NumericRangeFilterWidget):
                    field_filters[field_name] = {
                        "type": "numeric_range",
                        "min": filter_value.get("min"),
                        "max": filter_value.get("max"),
                    }
                elif isinstance(widget, TextFilterWidget):
                    field_filters[field_name] = {
                        "type": "text",
                        "pattern": filter_value,
                    }
                elif isinstance(widget, DateTimeRangeFilterWidget):
                    field_filters[field_name] = {
                        "type": "datetime_range",
                        "from": filter_value.get("from"),
                        "to": filter_value.get("to"),
                    }
                elif isinstance(widget, FloatTimestampRangeFilterWidget):
                    field_filters[field_name] = {
                        "type": "float_timestamp_range",
                        "from": filter_value.get("from"),
                        "to": filter_value.get("to"),
                    }

        return field_filters

    def update_discrete_values_from_data(self, log_table_model):
        """Update discrete filter values by scanning actual log data."""
        if not log_table_model:
            return

        for widget in self.filter_widgets:
            if (
                isinstance(widget, DiscreteFilterWidget)
                and widget.field_schema.get("is_discrete")
            ):
                # Get unique values from the log data
                unique_values = log_table_model.get_unique_field_values(
                    widget.field_name
                )

                # Always update if we have values (removed the count comparison that was preventing updates)
                if unique_values:
                    widget.set_available_values(unique_values)
