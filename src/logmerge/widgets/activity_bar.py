"""
Activity Bar Widget

VS Code-style permanent left activity bar with toggleable icon buttons.
"""

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton
from PyQt5.QtCore import pyqtSignal

from ..constants import (
    ACTIVITY_BAR_WIDTH, ACTIVITY_BAR_SPACING, ACTIVITY_BAR_BUTTON_SIZE,
    FILES_ACTIVITY_BUTTON_TEXT, FILES_ACTIVITY_TOOLTIP,
    FILTERS_ACTIVITY_BUTTON_TEXT, FILTERS_ACTIVITY_TOOLTIP,
    ACTIVITY_BUTTON_ACTIVE_STYLE, ACTIVITY_BUTTON_INACTIVE_STYLE
)


class ActivityBar(QWidget):
    """VS Code-style permanent left activity bar with toggleable icon buttons."""
    
    # Signals for button state changes
    files_button_clicked = pyqtSignal(bool)  # True = active, False = inactive
    filter_button_clicked = pyqtSignal(bool)  # True = active, False = inactive
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.active_button = None  # Track which button is currently active
        self.setup_ui()
        
    def setup_ui(self):
        """Set up the activity bar UI with icon buttons."""
        # Set fixed width for the activity bar
        self.setFixedWidth(ACTIVITY_BAR_WIDTH)
        self.setMinimumHeight(100)  # Minimum height to contain buttons
        
        # Main vertical layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(ACTIVITY_BAR_SPACING, ACTIVITY_BAR_SPACING, 
                                ACTIVITY_BAR_SPACING, ACTIVITY_BAR_SPACING)
        layout.setSpacing(ACTIVITY_BAR_SPACING)
        
        # Files button (📁)
        self.files_button = QPushButton(FILES_ACTIVITY_BUTTON_TEXT)
        self.files_button.setToolTip(FILES_ACTIVITY_TOOLTIP)
        self.files_button.setFixedSize(ACTIVITY_BAR_BUTTON_SIZE, ACTIVITY_BAR_BUTTON_SIZE)
        self.files_button.setStyleSheet(ACTIVITY_BUTTON_INACTIVE_STYLE)
        self.files_button.clicked.connect(self.on_files_button_clicked)
        layout.addWidget(self.files_button)
        
        # Filter button (🔍)
        self.filter_button = QPushButton(FILTERS_ACTIVITY_BUTTON_TEXT)
        self.filter_button.setToolTip(FILTERS_ACTIVITY_TOOLTIP)
        self.filter_button.setFixedSize(ACTIVITY_BAR_BUTTON_SIZE, ACTIVITY_BAR_BUTTON_SIZE)
        self.filter_button.setStyleSheet(ACTIVITY_BUTTON_INACTIVE_STYLE)
        self.filter_button.clicked.connect(self.on_filter_button_clicked)
        layout.addWidget(self.filter_button)
        
        # Add stretch to push buttons to the top
        layout.addStretch()
        
        # Set background color for the activity bar
        self.setStyleSheet("""
            ActivityBar {
                background-color: #2d2d30;
                border-right: 1px solid #3e3e42;
            }
        """)
    
    def on_files_button_clicked(self):
        """Handle files button click."""
        if self.active_button == 'files':
            # Clicking active button deactivates it
            self.set_active_button(None)
        else:
            # Activate files button
            self.set_active_button('files')
    
    def on_filter_button_clicked(self):
        """Handle filter button click."""
        if self.active_button == 'filters':
            # Clicking active button deactivates it
            self.set_active_button(None)
        else:
            # Activate filter button
            self.set_active_button('filters')
    
    def set_active_button(self, button_name):
        """Set which button is active and update styles accordingly."""
        # Update internal state
        previous_button = self.active_button
        self.active_button = button_name
        
        # Update button styles
        if button_name == 'files':
            self.files_button.setStyleSheet(ACTIVITY_BUTTON_ACTIVE_STYLE)
            self.filter_button.setStyleSheet(ACTIVITY_BUTTON_INACTIVE_STYLE)
        elif button_name == 'filters':
            self.files_button.setStyleSheet(ACTIVITY_BUTTON_INACTIVE_STYLE)
            self.filter_button.setStyleSheet(ACTIVITY_BUTTON_ACTIVE_STYLE)
        else:  # None - deactivate all
            self.files_button.setStyleSheet(ACTIVITY_BUTTON_INACTIVE_STYLE)
            self.filter_button.setStyleSheet(ACTIVITY_BUTTON_INACTIVE_STYLE)
        
        # Emit signals for state changes
        if previous_button != button_name:
            # Emit deactivation signal for previous button
            if previous_button == 'files':
                self.files_button_clicked.emit(False)
            elif previous_button == 'filters':
                self.filter_button_clicked.emit(False)
            
            # Emit activation signal for new button
            if button_name == 'files':
                self.files_button_clicked.emit(True)
            elif button_name == 'filters':
                self.filter_button_clicked.emit(True)
    
    def get_active_button(self):
        """Return the name of the currently active button or None."""
        return self.active_button
