"""
Basic tests for the logmerge package.
"""

import pytest
from pathlib import Path
import sys

# Add src to Python path for testing
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))


def test_package_import():
    """Test that the package can be imported."""
    import logmerge
    assert hasattr(logmerge, "__version__")
    assert logmerge.__version__ == "0.1.0"


def test_constants_import():
    """Test that constants module can be imported."""
    from logmerge import constants
    assert hasattr(constants, "COLOR_LIGHTEN_FACTOR")


def test_data_structures_import():
    """Test that data structures can be imported."""
    from logmerge.data_structures import LogEntry
    assert LogEntry is not None


def test_log_entry_creation():
    """Test basic LogEntry creation."""
    from logmerge.data_structures import LogEntry
    from datetime import datetime
    
    # Create a simple log entry
    entry = LogEntry(
        timestamp=datetime.now(),
        file_path="/test/file.log",
        fields={"message": "test log message", "level": "INFO"}
    )
    
    assert entry.file_path == "/test/file.log"
    assert entry.fields["message"] == "test log message"
    assert entry.fields["level"] == "INFO"
    assert isinstance(entry.timestamp, datetime)


def test_parsing_utils_import():
    """Test that parsing utilities can be imported."""
    from logmerge import parsing_utils
    assert parsing_utils is not None


def test_plugin_utils_import():
    """Test that plugin utilities can be imported."""
    from logmerge import plugin_utils
    assert plugin_utils is not None
