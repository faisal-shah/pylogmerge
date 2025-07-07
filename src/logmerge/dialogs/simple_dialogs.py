"""
Simple dialog functions replacing complex dialog classes.

This module provides simplified dialog functionality using built-in Qt dialogs
instead of complex custom widget hierarchies.
"""

from pathlib import Path
from typing import Optional, List, Dict
from PyQt5.QtWidgets import QFileDialog, QInputDialog, QMessageBox
from PyQt5.QtCore import QDir

from ..logging_config import get_logger


def list_available_plugins() -> List[Dict[str, str]]:
    """Get list of available plugins for informational purposes."""
    plugin_list = []
    logger = get_logger(__name__)

    try:
        from .. import plugins

        plugins_path = Path(plugins.__file__).parent

        for plugin_file in plugins_path.glob("*.py"):
            if plugin_file.name != "__init__.py":
                plugin_list.append(
                    {
                        "name": plugin_file.stem.replace("_plugin", "")
                        .replace("_", " ")
                        .title(),
                        "path": str(plugin_file),
                    }
                )
    except Exception as e:
        logger.warning(f"Could not discover preinstalled plugins: {e}")

    return plugin_list


def select_schema_file(parent=None) -> Optional[str]:
    """Simple schema file selection using file browser."""
    # Start in plugins directory if it exists
    start_dir = ""
    try:
        from .. import plugins

        start_dir = str(Path(plugins.__file__).parent)
    except (ImportError, AttributeError):
        start_dir = QDir.homePath()

    file_path, _ = QFileDialog.getOpenFileName(
        parent,
        "Select Log Schema Plugin",
        start_dir,
        "Python files (*.py);;All files (*.*)",
    )

    return file_path if file_path else None


def show_plugin_options_and_select(parent=None) -> Optional[str]:
    """Show available plugins and let user choose or browse."""
    plugins = list_available_plugins()

    if not plugins:
        # No plugins found, go straight to file browser
        QMessageBox.information(
            parent,
            "No Plugins Found",
            "No preinstalled plugins found. Please select a plugin file.",
        )
        return select_schema_file(parent)

    # Build options list
    options = [f"{p['name']} (built-in)" for p in plugins]
    options.append("Browse for file...")

    choice, ok = QInputDialog.getItem(
        parent, "Select Log Schema", "Choose a log schema plugin:", options, 0, False
    )

    if not ok:
        return None

    if choice == "Browse for file...":
        return select_schema_file(parent)
    else:
        # Find the selected plugin
        selected_name = choice.replace(" (built-in)", "")
        for plugin in plugins:
            if plugin["name"] == selected_name:
                return plugin["path"]

    return None
