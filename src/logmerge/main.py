#!/usr/bin/env python3
"""
Merged Log Viewer - Main Entry Point

A GUI application for viewing and analyzing multiple log files with advanced filtering
and merging capabilities.
"""

import sys
import argparse

from PyQt5.QtWidgets import QApplication, QMessageBox

from .logging_config import setup_logging, get_logger
from .main_window import MergedLogViewer


def main():
    """Main entry point for the application."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="Merged Log Viewer - A GUI for viewing and analyzing log files"
    )
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    parser.add_argument(
        "--log-file", type=str, help="Log to specified file instead of console"
    )
    args = parser.parse_args()

    # Setup logging
    log_level = "DEBUG" if args.debug else "INFO"
    setup_logging(log_level=log_level)

    logger = get_logger(__name__)
    logger.info("Starting Merged Log Viewer...")

    # Create QApplication
    app = QApplication(sys.argv)
    app.setApplicationName("Merged Log Viewer")
    app.setApplicationVersion("1.0.0")

    # Create and show main window
    try:
        main_window = MergedLogViewer()
        main_window.show()

        logger.info("Application started successfully")

        # Start the event loop
        sys.exit(app.exec_())

    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        QMessageBox.critical(
            None, "Application Error", f"Failed to start application:\n{str(e)}"
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
