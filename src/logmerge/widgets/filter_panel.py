"""
Filter Panel Widget

Provides filtering UI for log entries based on schema field types.
Dynamically creates appropriate filter widgets for each field in the schema.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QCheckBox, 
    QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox, QListWidget,
    QListWidgetItem, QDateTimeEdit, QScrollArea, QFrame, QApplication
)
from PyQt5.QtCore import pyqtSignal, QDateTime, Qt
from PyQt5.QtGui import QFont

from ..constants import (
    PANEL_MIN_WIDTH, PANEL_MAX_WIDTH, SIDEBAR_CONTENT_MARGINS, 
    TITLE_LABEL_STYLE, FILTERS_TITLE
)
from .panels import BasePanel


class FilterWidget(QWidget):
    """Base class for individual field filter widgets."""
    
    filter_changed = pyqtSignal()
    
    def __init__(self, field_name: str, field_schema: dict, parent=None):
        super().__init__(parent)
        self.field_name = field_name
        self.field_schema = field_schema
        self.enabled = False
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the basic filter UI structure."""
        layout = QVBoxLayout()
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(4)
        
        # Header with field name and enable checkbox
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        self.enable_cb = QCheckBox()
        self.enable_cb.setChecked(False)
        self.enable_cb.toggled.connect(self.on_enabled_changed)
        
        field_label = QLabel(self.field_name)
        field_label.setFont(QFont("", 9, QFont.Bold))
        
        header_layout.addWidget(self.enable_cb)
        header_layout.addWidget(field_label)
        header_layout.addStretch()
        
        layout.addLayout(header_layout)
        
        # Filter-specific widget (implemented by subclasses)
        self.filter_widget = self.create_filter_widget()
        self.filter_widget.setEnabled(False)
        layout.addWidget(self.filter_widget)
        
        # Separator line
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        layout.addWidget(line)
        
        self.setLayout(layout)
    
    def create_filter_widget(self) -> QWidget:
        """Create the filter-specific widget. Implemented by subclasses."""
        raise NotImplementedError
    
    def on_enabled_changed(self, enabled: bool):
        """Handle filter enable/disable."""
        self.enabled = enabled
        self.filter_widget.setEnabled(enabled)
        self.filter_changed.emit()
    
    def get_filter_value(self):
        """Get the current filter value. Implemented by subclasses."""
        raise NotImplementedError
    
    def is_filter_active(self) -> bool:
        """Check if this filter is active."""
        return self.enabled


class DiscreteFilterWidget(FilterWidget):
    """Filter widget for discrete values (enum, is_discrete fields)."""
    
    def __init__(self, field_name: str, field_schema: dict, values: list = None, parent=None):
        self.values = values or []
        self.last_clicked_index = -1  # For shift+click range selection
        super().__init__(field_name, field_schema, parent)
    
    def create_filter_widget(self) -> QWidget:
        """Create a list widget with checkboxes for discrete values."""
        self.list_widget = QListWidget()
        self.list_widget.setMaximumHeight(120)
        self.list_widget.setSelectionMode(QListWidget.ExtendedSelection)  # Enable multi-selection
        
        # Populate with values
        for value in self.values:
            if isinstance(value, dict):  # enum format
                display_text = f"{value['value']} ({value['name']})"
                item_value = value['value']
            else:  # simple value
                display_text = str(value)
                item_value = value
            
            item = QListWidgetItem(display_text)
            item.setData(Qt.UserRole, item_value)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Checked)  # Default to all selected
            self.list_widget.addItem(item)
        
        # Connect signals for multi-selection checkbox toggling
        self.list_widget.itemChanged.connect(self.on_item_changed)
        self.list_widget.itemClicked.connect(self.on_item_clicked)
        
        return self.list_widget
    
    def on_item_clicked(self, item):
        """Handle item clicks for multi-selection and range selection."""
        current_index = self.list_widget.row(item)
        modifiers = QApplication.keyboardModifiers()
        
        # Handle Shift+click for range selection
        if modifiers & Qt.ShiftModifier and self.last_clicked_index >= 0:
            start_index = min(self.last_clicked_index, current_index)
            end_index = max(self.last_clicked_index, current_index)
            
            # Select range
            for i in range(start_index, end_index + 1):
                self.list_widget.item(i).setSelected(True)
        
        # Handle Ctrl+click for individual selection (Qt handles this automatically)
        # Update last clicked index
        self.last_clicked_index = current_index
    
    def on_item_changed(self, item):
        """Handle checkbox changes - apply to all selected items if multiple are selected."""
        selected_items = self.list_widget.selectedItems()
        
        # If multiple items are selected, apply the same check state to all selected items
        if len(selected_items) > 1 and item in selected_items:
            new_state = item.checkState()
            
            # Temporarily disconnect the signal to avoid recursive calls
            self.list_widget.itemChanged.disconnect(self.on_item_changed)
            
            try:
                # Apply the same state to all selected items
                for selected_item in selected_items:
                    if selected_item != item:  # Don't change the item that triggered this
                        selected_item.setCheckState(new_state)
            finally:
                # Reconnect the signal
                self.list_widget.itemChanged.connect(self.on_item_changed)
        
        # Emit filter changed signal
        self.filter_changed.emit()
    
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
        
        for value in values:
            item = QListWidgetItem(str(value))
            item.setData(Qt.UserRole, value)
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
        
        self.min_input.valueChanged.connect(lambda: self.filter_changed.emit())
        self.max_input.valueChanged.connect(lambda: self.filter_changed.emit())
        
        widget.setLayout(layout)
        return widget
    
    def get_filter_value(self):
        """Get the min/max range values."""
        if not self.enabled:
            return None
        
        min_val = self.min_input.value() if self.min_input.value() != self.min_input.minimum() else None
        max_val = self.max_input.value() if self.max_input.value() != self.max_input.maximum() else None
        
        return {"min": min_val, "max": max_val}


class TextFilterWidget(FilterWidget):
    """Filter widget for text pattern matching."""
    
    def create_filter_widget(self) -> QWidget:
        """Create text input with regex support."""
        self.text_input = QLineEdit()
        self.text_input.setPlaceholderText("Enter text or regex pattern...")
        self.text_input.textChanged.connect(lambda: self.filter_changed.emit())
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
        self.from_input.setDateTime(QDateTime.currentDateTime().addDays(-30))
        from_layout.addWidget(self.from_input)
        
        # To datetime
        to_layout = QHBoxLayout()
        to_layout.addWidget(QLabel("To:"))
        self.to_input = QDateTimeEdit()
        self.to_input.setCalendarPopup(True)
        self.to_input.setDateTime(QDateTime.currentDateTime())
        to_layout.addWidget(self.to_input)
        
        layout.addLayout(from_layout)
        layout.addLayout(to_layout)
        
        self.from_input.dateTimeChanged.connect(lambda: self.filter_changed.emit())
        self.to_input.dateTimeChanged.connect(lambda: self.filter_changed.emit())
        
        widget.setLayout(layout)
        return widget
    
    def get_filter_value(self):
        """Get the datetime range."""
        if not self.enabled:
            return None
        
        return {
            "from": self.from_input.dateTime().toPyDateTime(),
            "to": self.to_input.dateTime().toPyDateTime()
        }


class FilterPanel(BasePanel):
    """Panel containing all field filters based on schema."""
    
    def __init__(self, parent=None):
        super().__init__("filters", parent)
        self.schema = None
        self.filter_widgets = []
    
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
        self.filter_layout.setSpacing(0)
        
        self.filter_container.setLayout(self.filter_layout)
        scroll_area.setWidget(self.filter_container)
        
        layout.addWidget(scroll_area)
    
    def set_schema(self, schema):
        """Set the schema and create filter widgets accordingly."""
        print(f"DEBUG: FilterPanel.set_schema called with schema: {schema}")
        self.schema = schema
        self.clear_filters()
        
        if not schema or not hasattr(schema, 'fields'):
            print("DEBUG: No schema or no fields attribute in schema")
            return
        
        print(f"DEBUG: Processing {len(schema.fields)} fields")
        for field in schema.fields:
            filter_widget = self.create_filter_for_field(field)
            if filter_widget:
                print(f"DEBUG: Created filter widget for field: {field.get('name', 'unknown')}")
                self.filter_widgets.append(filter_widget)
                self.filter_layout.addWidget(filter_widget)
            else:
                print(f"DEBUG: No filter widget created for field: {field.get('name', 'unknown')}")
        
        # Add stretch at the end
        self.filter_layout.addStretch()
        print(f"DEBUG: Total filter widgets created: {len(self.filter_widgets)}")
    
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
            if (isinstance(widget, DiscreteFilterWidget) and 
                widget.field_name == field_name):
                widget.set_available_values(values)
                break
    
    def get_active_filters(self) -> dict:
        """Get all currently active filters."""
        active_filters = {}
        for widget in self.filter_widgets:
            if widget.is_filter_active():
                active_filters[widget.field_name] = widget.get_filter_value()
        return active_filters
    
    def update_discrete_values_from_data(self, log_table_model):
        """Update discrete filter values by scanning actual log data."""
        if not log_table_model:
            return
            
        for widget in self.filter_widgets:
            if (isinstance(widget, DiscreteFilterWidget) and 
                hasattr(widget.field_schema, 'get') and
                widget.field_schema.get('is_discrete')):
                
                # Get unique values from the log data
                unique_values = log_table_model.get_unique_field_values(widget.field_name)
                
                # Only update if we have new values (avoid unnecessary UI updates)
                if unique_values and len(unique_values) != widget.list_widget.count():
                    widget.set_available_values(unique_values)
