"""
Main Window

Contains the main application window class.
"""

import time

from PyQt5.QtWidgets import (
    QMainWindow,
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QSplitter,
    QTableView,
    QHeaderView,
    QAction,
    QApplication,
    QDialog,
    QMessageBox,
    QTabWidget,
    QMenu,
)
from PyQt5.QtCore import Qt, QTimer, QEvent

from .logging_config import get_logger
from .plugin_utils import LogParsingPlugin
from .data_structures import SharedLogBuffer
from .file_monitoring import LogParsingWorker
from .widgets import FilePickerPanel, FilterPanel, LogTableModel, FileListItemWidget
from .dialogs import ColumnConfigurationDialog
from .dialogs.simple_dialogs import show_plugin_options_and_select
from .constants import (
    WINDOW_TITLE,
    MAIN_WINDOW_DEFAULT_GEOMETRY,
    FOLLOW_ACTION_TEXT,
    COLUMN_CONFIG_ACTION_TEXT,
    BUFFER_DRAIN_INTERVAL_MS,
    READY_STATUS,
    SCHEMA_LOAD_ERROR_FORMAT,
    PROCESSING_ENTRIES_FORMAT,
    BUFFER_DRAINED_FORMAT,
    BUFFER_EMPTY_MESSAGE,
    NO_SHARED_BUFFER_MESSAGE,
    FILE_COUNT_STATUS_FORMAT,
    THREAD_SHUTDOWN_TIMEOUT_MS,
    THREAD_FORCE_TERMINATE_TIMEOUT_MS,
)


class MergedLogViewer(QMainWindow):
    """Main application window for the merged log viewer."""

    def __init__(self):
        super().__init__()
        self.logger = get_logger(__name__)
        self.schema = None
        self.log_table_model = None
        self.parsing_worker = None
        self.shared_buffer = None
        self.follow_mode = True  # Auto-scroll to bottom by default
        self.auto_scroll_disabled = False  # Track if user manually scrolled away

        # First, select schema before setting up UI
        if not self.select_schema():
            raise RuntimeError("Schema selection cancelled by user")

        self.setup_ui()

    def setup_ui(self):
        """Set up the main window UI."""
        self.setWindowTitle(WINDOW_TITLE)
        self.setGeometry(*MAIN_WINDOW_DEFAULT_GEOMETRY)

        # Create toolbar
        self.setup_toolbar()

        # Set up main layout
        self._setup_main_layout()

        # Initialize worker and timer
        self._initialize_background_processing()

        # Status bar
        self.statusBar().showMessage(READY_STATUS)

    def _setup_main_layout(self):
        """Set up the main window layout with panels and table view."""
        # Create central widget with horizontal splitter
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Create main splitter
        self.main_splitter = QSplitter(Qt.Horizontal)

        # Create sidebar with tabs (replaces ActivityBar + PanelContainer)
        self._setup_sidebar()

        # Create main table view area
        self._setup_table_view()

        # Add to main layout
        layout.addWidget(self.main_splitter, 1)
        central_widget.setLayout(layout)

    def _setup_sidebar(self):
        """Set up the sidebar with tabs containing panels."""
        # Create sidebar with tabs
        self.sidebar = QTabWidget()
        self.sidebar.setTabPosition(QTabWidget.West)
        self.sidebar.setFixedWidth(350)

        # Create and add panels as tabs
        self.file_picker_panel = FilePickerPanel()
        self.filter_panel = FilterPanel()

        # Add panels as tabs with emoji icons
        self.sidebar.addTab(self.file_picker_panel, "📁")
        self.sidebar.addTab(self.filter_panel, "🔍")

        # Set schema for filter panel if available
        if self.schema:
            print(f"DEBUG: Setting schema on filter panel: {self.schema.fields}")
            self.filter_panel.set_schema(self.schema)
            # Also update discrete values if there's already data in the log table
            if hasattr(self, "log_table_model"):
                self.filter_panel.update_discrete_values_from_data(self.log_table_model)
        else:
            print("DEBUG: No schema available to set on filter panel")

        # Connect panel signals
        self.file_picker_panel.files_changed.connect(self.on_files_changed)
        self.filter_panel.apply_clicked.connect(self.on_filters_applied)

        # Add sidebar to splitter
        self.main_splitter.addWidget(self.sidebar)

        # Set initial splitter sizes
        self.main_splitter.setSizes([350, 650])

    def _setup_table_view(self):
        """Set up the main log table view."""
        main_view_widget = QWidget()
        self.main_splitter.addWidget(main_view_widget)

        # Set up the main view layout
        main_view_layout = QVBoxLayout(main_view_widget)
        main_view_layout.setContentsMargins(0, 0, 0, 0)
        main_view_layout.setSpacing(0)

        # Table view
        self.log_table_view = QTableView()
        self.log_table_model = LogTableModel(self.schema)
        self.log_table_view.setModel(self.log_table_model)

        # Configure table view
        self.log_table_view.setAlternatingRowColors(True)
        self.log_table_view.setSelectionBehavior(QTableView.SelectRows)
        self.log_table_view.setSortingEnabled(True)

        # Setup initial column widths
        self.setup_initial_column_widths()

        # Connect double-click for auto-resize
        header = self.log_table_view.horizontalHeader()
        header.setContextMenuPolicy(Qt.CustomContextMenu)
        header.sectionDoubleClicked.connect(self.auto_resize_column)
        header.customContextMenuRequested.connect(self.show_header_context_menu)

        # Connect scroll bar signals for follow mode
        vertical_scrollbar = self.log_table_view.verticalScrollBar()
        vertical_scrollbar.valueChanged.connect(self.on_scroll_changed)
        vertical_scrollbar.rangeChanged.connect(self.on_scroll_range_changed)

        main_view_layout.addWidget(self.log_table_view)

    def _initialize_background_processing(self):
        """Initialize the background worker thread and buffer timer."""
        # Initialize shared buffer and worker
        self.shared_buffer = SharedLogBuffer()
        self.parsing_worker = LogParsingWorker(self.schema, self.shared_buffer, self)

        # Timer to drain shared buffer
        self.buffer_timer = QTimer()
        self.buffer_timer.timeout.connect(self.drain_log_buffer)
        self.buffer_timer.start(BUFFER_DRAIN_INTERVAL_MS)

        # Start the parsing worker
        self.parsing_worker.start()

    def setup_toolbar(self):
        """Set up the main toolbar with follow mode controls."""
        toolbar = self.addToolBar("Main")
        toolbar.setMovable(False)

        # Follow mode toggle action
        self.follow_action = QAction(FOLLOW_ACTION_TEXT, self)
        self.follow_action.setCheckable(True)
        self.follow_action.setChecked(self.follow_mode)
        self.follow_action.setToolTip("Automatically scroll to show latest log entries")
        self.follow_action.triggered.connect(self.toggle_follow_mode)
        toolbar.addAction(self.follow_action)

        toolbar.addSeparator()

        # Column configuration action
        self.column_config_action = QAction(COLUMN_CONFIG_ACTION_TEXT, self)
        self.column_config_action.setToolTip(
            "Configure which columns to display and their order"
        )
        self.column_config_action.triggered.connect(self.open_column_configuration)
        toolbar.addAction(self.column_config_action)

    def toggle_follow_mode(self):
        """Toggle follow mode on/off."""
        self.follow_mode = self.follow_action.isChecked()
        self.auto_scroll_disabled = False  # Reset manual scroll override

        if self.follow_mode:
            self.scroll_to_bottom()

    def on_scroll_changed(self, value: int) -> None:
        """Handle manual scrolling by the user."""
        if not self.follow_mode:
            return

        # Check if user manually scrolled away from the bottom
        scrollbar = self.log_table_view.verticalScrollBar()
        is_at_bottom = value >= scrollbar.maximum() - 1

        if not is_at_bottom and not self.auto_scroll_disabled:
            self.auto_scroll_disabled = True

    def on_scroll_range_changed(self, min_val: int, max_val: int) -> None:
        """Handle when the scroll range changes (new content added)."""
        if self.follow_mode and not self.auto_scroll_disabled:
            QTimer.singleShot(0, self.scroll_to_bottom)

    def scroll_to_bottom(self) -> None:
        """Scroll the table view to the bottom."""
        scrollbar = self.log_table_view.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def select_schema(self) -> bool:
        """Show schema selection dialog and load the selected schema."""
        # Select schema file using simple dialog
        schema_path = show_plugin_options_and_select(self)
        if not schema_path:
            return False

        try:
            # Load and create plugin from file
            self.schema = LogParsingPlugin.from_file(schema_path)

            # Set schema for filter panel
            if hasattr(self, "filter_panel"):
                self.filter_panel.set_schema(self.schema)
                # Also update discrete values if there's already data
                if hasattr(self, "log_table_model"):
                    self.filter_panel.update_discrete_values_from_data(
                        self.log_table_model
                    )

            return True

        except Exception as e:
            QMessageBox.critical(
                self, "Schema Error", SCHEMA_LOAD_ERROR_FORMAT.format(error=str(e))
            )
            return False

    def drain_log_buffer(self):
        """Drain entries from shared buffer and update table."""
        if not self.shared_buffer:
            self.logger.warning(NO_SHARED_BUFFER_MESSAGE)
            return

        start_time = time.perf_counter()
        entries = self.shared_buffer.drain_entries()

        if not entries:
            self.logger.debug(BUFFER_EMPTY_MESSAGE)
            return

        self.logger.debug(PROCESSING_ENTRIES_FORMAT.format(count=len(entries)))

        # Remember current scroll position for follow mode logic
        scrollbar = self.log_table_view.verticalScrollBar()
        was_at_bottom = scrollbar.value() >= scrollbar.maximum() - 1

        # Batch add to table model
        self.log_table_model.add_entries_batch(entries)

        # Update discrete filter values with new data (only if significant amount of new data)
        if (
            hasattr(self, "filter_panel") and len(entries) >= 10
        ):  # Only update for batches of 10+ entries
            self.filter_panel.update_discrete_values_from_data(self.log_table_model)

        QApplication.processEvents()

        # Handle follow mode scrolling
        if self.follow_mode and not self.auto_scroll_disabled:
            if was_at_bottom or scrollbar.maximum() == 0:
                self.scroll_to_bottom()
        elif self.follow_mode and self.auto_scroll_disabled and was_at_bottom:
            self.auto_scroll_disabled = False
            self.scroll_to_bottom()

        elapsed_time = time.perf_counter() - start_time
        self.logger.debug(
            BUFFER_DRAINED_FORMAT.format(count=len(entries), time=elapsed_time)
        )

    def on_files_changed(self):
        """Handle changes to the file list."""
        checked_files = self.file_picker_panel.get_checked_files()
        all_files = self.file_picker_panel.get_all_files()

        # Update table model to show only checked files
        self.log_table_model.update_checked_files(checked_files)

        # Update file colors for the table model
        self._update_file_colors()

        if self.parsing_worker:
            self.parsing_worker.update_file_list(all_files)

        # Update status message with file counts
        status_msg = FILE_COUNT_STATUS_FORMAT.format(
            total=len(all_files), selected=len(checked_files)
        )
        if not all_files:
            status_msg = READY_STATUS
        self.statusBar().showMessage(status_msg)

    def on_filters_applied(self):
        """Handle filter changes from the filter panel."""
        # Get the standardized filters from the filter panel
        field_filters = self.filter_panel.get_active_filters()

        # Apply filters to the table model
        self.log_table_model.apply_filters(field_filters)

        # Update status to show filter is active
        if field_filters:
            filter_count = len(field_filters)
            self.statusBar().showMessage(f"Filters applied: {filter_count} active")
        else:
            # No filters, show regular status
            checked_files = self.file_picker_panel.get_checked_files()
            all_files = self.file_picker_panel.get_all_files()
            status_msg = FILE_COUNT_STATUS_FORMAT.format(
                total=len(all_files), selected=len(checked_files)
            )
            if not all_files:
                status_msg = READY_STATUS
            self.statusBar().showMessage(status_msg)

    def _update_file_colors(self):
        """Update the file colors in the table model from the sidebar."""
        file_list = self.file_picker_panel.file_list
        file_colors = {}

        for i in range(file_list.count()):
            item = file_list.item(i)
            if item:
                widget = file_list.itemWidget(item)
                if isinstance(widget, FileListItemWidget):
                    file_colors[widget.file_path] = widget.get_color()

        if file_colors:
            self.log_table_model.update_file_colors(file_colors)

    def open_column_configuration(self) -> None:
        """Open the column configuration dialog."""
        current_config = self.log_table_model.get_column_configuration()
        dialog = ColumnConfigurationDialog(self.schema, current_config, self)

        if dialog.exec_() == QDialog.Accepted:
            new_config = dialog.get_column_configuration()
            self.log_table_model.update_column_configuration(new_config)

            self.setup_initial_column_widths()

    def setup_initial_column_widths(self) -> None:
        """Initialize column widths with uniform distribution."""
        header = self.log_table_view.horizontalHeader()
        column_count = self.log_table_model.columnCount()
        
        if column_count == 0:
            return
            
        # Set all columns to Interactive mode for user resizing
        for i in range(column_count):
            header.setSectionResizeMode(i, QHeaderView.Interactive)
        
        # Get available width and distribute uniformly
        # Account for scrollbar and margins (rough estimate)
        available_width = self.log_table_view.width() - 50
        if available_width > 0:
            uniform_width = max(100, available_width // column_count)  # Minimum 100px
            for i in range(column_count):
                header.resizeSection(i, uniform_width)

    def auto_resize_column(self, logical_index: int) -> None:
        """Auto-resize a column to fit its contents (double-click handler)."""
        self.log_table_view.resizeColumnToContents(logical_index)

    def auto_resize_all_columns(self) -> None:
        """Auto-resize all columns to fit their contents."""
        for i in range(self.log_table_model.columnCount()):
            self.log_table_view.resizeColumnToContents(i)

    def show_header_context_menu(self, position) -> None:
        """Show context menu for table header."""
        menu = QMenu(self)
        
        auto_resize_action = QAction("Auto-resize All Columns", self)
        auto_resize_action.triggered.connect(self.auto_resize_all_columns)
        menu.addAction(auto_resize_action)
        
        reset_widths_action = QAction("Reset Column Widths", self)
        reset_widths_action.triggered.connect(self.setup_initial_column_widths)
        menu.addAction(reset_widths_action)
        
        header = self.log_table_view.horizontalHeader()
        menu.exec_(header.mapToGlobal(position))

    def update_header_resize_modes(self) -> None:
        """Update table header resize modes - simplified to just call setup."""
        self.setup_initial_column_widths()

    def closeEvent(self, event: QEvent) -> None:
        """Handle application close event."""
        self.logger.info("Application closing...")

        if self.parsing_worker:
            self.parsing_worker.stop()
            if not self.parsing_worker.wait(THREAD_SHUTDOWN_TIMEOUT_MS):
                self.logger.warning(
                    "Worker thread did not shut down gracefully, terminating..."
                )
                self.parsing_worker.terminate()
                if not self.parsing_worker.wait(THREAD_FORCE_TERMINATE_TIMEOUT_MS):
                    self.logger.error("Failed to terminate worker thread")

        if self.buffer_timer:
            self.buffer_timer.stop()

        event.accept()
