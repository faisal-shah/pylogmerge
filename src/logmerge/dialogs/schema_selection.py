"""
Schema Selection Dialog

Dialog for selecting a log schema/plugin file.
"""

from pathlib import Path
from typing import List, Dict

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QListWidget, QListWidgetItem,
    QLineEdit, QPushButton, QDialogButtonBox, QFileDialog
)
from PyQt5.QtCore import Qt

from ..logging_config import get_logger
from ..constants import (
    SCHEMA_DIALOG_TITLE, SCHEMA_DIALOG_SIZE, SCHEMA_INSTRUCTIONS,
    PREINSTALLED_PLUGINS_LABEL, SCHEMA_PATH_PLACEHOLDER, BROWSE_BUTTON_TEXT,
    PYTHON_FILE_FILTER
)


class SchemaSelectionDialog(QDialog):
    """Dialog for selecting a log schema file."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = get_logger(__name__)
        self.selected_schema_path = None
        self.preinstalled_plugins = self.discover_preinstalled_plugins()
        self.setup_ui()
        
    def discover_preinstalled_plugins(self) -> List[Dict[str, str]]:
        """Discover preinstalled plugins in the logmerge.plugins package."""
        plugin_list = []
        
        try:
            # Get the plugins directory path
            from .. import plugins
            plugins_path = Path(plugins.__file__).parent
            
            # Find all Python files in the plugins directory (except __init__.py)
            for plugin_file in plugins_path.glob("*.py"):
                if plugin_file.name != "__init__.py":
                    plugin_info = {
                        'name': plugin_file.stem.replace('_plugin', '').replace('_', ' ').title(),
                        'path': str(plugin_file),
                        'description': f"Plugin for {plugin_file.stem.replace('_plugin', '').replace('_', ' ')} format"
                    }
                    plugin_list.append(plugin_info)
                    
        except Exception as e:
            self.logger.warning(f"Could not discover preinstalled plugins: {e}")
            
        return plugin_list
        
    def setup_ui(self):
        """Set up the dialog UI."""
        self.setWindowTitle(SCHEMA_DIALOG_TITLE)
        self.setModal(True)
        self.resize(*SCHEMA_DIALOG_SIZE)
        
        layout = QVBoxLayout()
        
        # Instructions
        instructions = QLabel(SCHEMA_INSTRUCTIONS)
        instructions.setWordWrap(True)
        layout.addWidget(instructions)
        
        # Pre-installed plugins section
        if self.preinstalled_plugins:
            plugins_label = QLabel(PREINSTALLED_PLUGINS_LABEL)
            plugins_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
            layout.addWidget(plugins_label)
            
            # Plugin list
            self.plugin_list = QListWidget()
            self.plugin_list.setSelectionMode(QListWidget.SingleSelection)
            
            for plugin in self.preinstalled_plugins:
                item = QListWidgetItem(plugin['name'])
                item.setData(Qt.UserRole, plugin['path'])
                item.setToolTip(f"{plugin['description']}\n\nPath: {plugin['path']}")
                self.plugin_list.addItem(item)
            
            self.plugin_list.itemSelectionChanged.connect(self.on_plugin_selection_changed)
            self.plugin_list.itemDoubleClicked.connect(self.on_plugin_double_clicked)
            layout.addWidget(self.plugin_list)
        else:
            # Fallback to file browser if no preinstalled plugins found
            warning_label = QLabel("No preinstalled plugins found. Please browse for a plugin file.")
            warning_label.setStyleSheet("color: orange; font-weight: bold;")
            layout.addWidget(warning_label)
            
            # Schema file selection
            file_layout = QHBoxLayout()
            self.schema_path_edit = QLineEdit()
            self.schema_path_edit.setReadOnly(True)
            self.schema_path_edit.setPlaceholderText(SCHEMA_PATH_PLACEHOLDER)
            file_layout.addWidget(self.schema_path_edit)
            
            browse_btn = QPushButton(BROWSE_BUTTON_TEXT)
            browse_btn.clicked.connect(self.browse_schema_file)
            file_layout.addWidget(browse_btn)
            layout.addLayout(file_layout)
        
        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        
        # Add Browse button on the left side
        if self.preinstalled_plugins:
            browse_button = button_box.addButton("Browse...", QDialogButtonBox.ActionRole)
            browse_button.clicked.connect(self.browse_schema_file)
        
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        self.ok_button = button_box.button(QDialogButtonBox.Ok)
        self.ok_button.setEnabled(False)
        layout.addWidget(button_box)
        
        self.setLayout(layout)
        
    def on_plugin_selection_changed(self):
        """Handle plugin selection change."""
        selected_items = self.plugin_list.selectedItems()
        if not selected_items:
            self.ok_button.setEnabled(False)
            return
            
        item = selected_items[0]
        plugin_path = item.data(Qt.UserRole)
        
        # Set selected plugin path and enable OK
        self.selected_schema_path = plugin_path
        self.ok_button.setEnabled(True)
            
    def on_plugin_double_clicked(self, item):
        """Handle double-click on plugin item."""
        plugin_path = item.data(Qt.UserRole)
        
        # Accept the selection for preinstalled plugins
        self.selected_schema_path = plugin_path
        self.accept()
        
    def browse_schema_file(self):
        """Browse for plugin file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "Select Log Plugin File", 
            "", 
            PYTHON_FILE_FILTER
        )
        
        if file_path:
            # Set the selected plugin path and immediately accept the dialog
            self.selected_schema_path = file_path
            self.accept()  # Close the dialog and proceed
            
            # If we have the text edit (fallback mode), update it
            if hasattr(self, 'schema_path_edit'):
                self.schema_path_edit.setText(Path(file_path).name)
