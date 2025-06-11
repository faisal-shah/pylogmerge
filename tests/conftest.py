"""
Test configuration and fixtures for the logmerge test suite.
"""

import pytest
import sys
from pathlib import Path

# Add src to Python path for testing
src_path = Path(__file__).parent.parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))


@pytest.fixture(scope="session")
def sample_log_data():
    """Provide sample log data for testing."""
    return [
        {
            "timestamp": "2025-01-01T10:00:00",
            "level": "INFO",
            "message": "Application started",
            "file": "app.log"
        },
        {
            "timestamp": "2025-01-01T10:01:00",
            "level": "ERROR",
            "message": "Database connection failed",
            "file": "error.log"
        },
        {
            "timestamp": "2025-01-01T10:02:00",
            "level": "DEBUG",
            "message": "Processing request",
            "file": "debug.log"
        }
    ]


@pytest.fixture
def temp_log_file(tmp_path):
    """Create a temporary log file for testing."""
    log_file = tmp_path / "test.log"
    log_content = """
2025-01-01 10:00:00 INFO Application started
2025-01-01 10:01:00 ERROR Database connection failed
2025-01-01 10:02:00 DEBUG Processing request
""".strip()
    log_file.write_text(log_content)
    return log_file
