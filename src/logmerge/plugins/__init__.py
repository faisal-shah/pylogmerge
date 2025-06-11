"""
LogMerge Plugins - Built-in parsing plugins for common log formats

This package contains built-in plugins for parsing various log file formats.
Each plugin defines a SCHEMA with field definitions and optional custom parsing functions.

Available plugins:
- dbglog_plugin: Debug log format with level, timestamp, module, and message fields
- canking_plugin: CAN King log format for CAN bus message analysis

Example:
    Using a plugin:
    >>> from logmerge.plugins.dbglog_plugin import SCHEMA
    >>> from logmerge import LogParsingPlugin
    >>> plugin = LogParsingPlugin(SCHEMA.get('fields'), SCHEMA.get('parse_function'))
"""

# Note: Plugins are imported dynamically by the main application
# This avoids import issues and allows for flexible plugin discovery
__all__ = []
