# LogMerge

A GUI application for viewing and analyzing multiple log files with advanced filtering and merging capabilities.

## Features

- Multi-file log viewing with real-time updates
- Plugin-based parsing system for different log formats
- Advanced filtering and search capabilities with multiple filter types:
  - Discrete value filters (enums, categorical data)
  - Numeric range filters (int, float)
  - Text pattern matching (regex support)
  - DateTime range filters (epoch, strptime)
  - Float timestamp range filters (raw numeric timestamps)
- Color-coded file identification
- Live log monitoring with follow mode
- Configurable column display and ordering
- Empty datetime filter initialization (no misleading defaults)

## Installation

### Prerequisites

- Python 3.10 or higher
- Make

### Setup

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/faisal-shah/pylogmerge.git
    cd pylogmerge
    ```

2.  **Build the project:**
    ```bash
    make
    ```
    This command will set up a virtual environment, install dependencies, and build the distribution package. The resulting `.whl` file will be located in the `dist/` directory.

3. **Install the package:**
   After building, install the package using pip. Make sure to activate your virtual environment if you are using one.
   ```bash
   pip install dist/*.whl
   ```

## Usage

To run the application, use the following command:

```bash
logmerge
```

The application will start, and you will first be prompted to select a log parsing plugin. After selecting a plugin, you can begin adding log files.

### Command-line Options

-   `--log-level <LEVEL>`: Set the logging level. Choices are DEBUG, INFO, WARNING, ERROR, CRITICAL. Default is WARNING.

## Architecture Overview

LogMerge follows a multi-threaded, event-driven architecture designed for real-time log monitoring and efficient display updates. Understanding this architecture is crucial for contributors and advanced users.

### High-Level Data Flow

```
Log Files → File Monitor Thread → Shared Buffer → UI Thread → Table Display
    ↓              ↓                    ↓           ↓           ↓
Polling         Parsing            Batching    Draining    Rendering
(1Hz)          (Plugin)           (100 items)   (2Hz)      (On-demand)
```

### Core Components

#### 1. **File Monitoring System** (`file_monitoring.py`)
- **Thread**: Runs in a separate `LogParsingWorker` thread
- **Polling Frequency**: 1 second (configurable via `DEFAULT_POLL_INTERVAL_SECONDS`)
- **Operation**: 
  - Monitors file size and modification time for each added log file
  - Maintains file handles and tracks last read position (`FileMonitorState`)
  - Reads only new lines since last poll using `file.readlines()`
  - Processes new lines through the selected plugin

#### 2. **Plugin-Based Parsing** (`plugin_utils.py`)
- **Input**: Raw log line (string)
- **Processing**: Each line is passed to the plugin's parsing function
- **Output**: Returns a `LogEntry` named tuple containing:
  - `file_path`: Source file
  - `line_number`: Line number in file
  - `timestamp`: Parsed timestamp (datetime for `epoch`/`strptime` types, float for `float_timestamp` type)
  - `fields`: Dictionary of parsed field values (raw enum values, not display names)
  - `raw_line`: Original line text
- **Error Handling**: Unparseable lines are dropped and logged

#### 3. **Shared Buffer System** (`data_structures.py`)
- **Type**: Thread-safe `deque` with maximum size (10M entries default)
- **Purpose**: Decouples file monitoring thread from UI thread
- **Batching**: Worker thread adds entries when batch reaches 100 items OR at end of each polling cycle
- **Location**: See `file_monitoring.py:118-127` - uses `DEFAULT_BATCH_SIZE = 100`
- **Thread Safety**: All operations protected by threading locks

#### 4. **UI Update Cycle** (`main_window.py`)
- **Timer**: QTimer triggers buffer drain every 500ms (`BUFFER_DRAIN_INTERVAL_MS` - half the file polling interval)
- **Process**:
  1. Drain all entries from shared buffer
  2. Add entries to table model using binary search insertion
  3. Force Qt event processing with `QApplication.processEvents()`
  4. Handle auto-scroll in follow mode
- **Performance**: Only processes Qt events when entries are available

#### 5. **Display Management** (`widgets/log_table.py`)
- **Model**: Custom `QAbstractTableModel` with smart caching
- **Filtering**: Shows only entries from checked files, with advanced field filtering
- **Sorting**: Entries maintained in chronological order via binary search
- **Caching**: Cached datetime formatting, file colors, and enum display mappings for performance
- **Memory**: Efficient filtering without data duplication
- **Enum Display**: Uses pre-built display maps for O(1) enum value to friendly name lookup

### Timing and Performance Characteristics

| Component | Frequency | Purpose |
|-----------|-----------|---------|
| File Polling | 1 Hz | Check for file changes (balance between responsiveness and system load) |
| Buffer Draining | 2 Hz | Update UI with new log entries (half the file polling rate for balanced responsiveness) |
| Batch Size | UP TO 100 entries | Optimize memory allocation and UI update efficiency (flushes at 100 OR end of polling cycle) |
| Buffer Size | 10M entries | Prevent memory exhaustion during high-volume logging |

### Thread Architecture

```
Main Thread (UI)                    Worker Thread (File Monitor)
     │                                        │
     ├─ QTimer (500ms)                       ├─ Polling Loop (1000ms)
     ├─ Buffer Drain                         ├─ File Change Detection
     ├─ Table Updates                        ├─ Line-by-Line Reading
     ├─ User Interactions                    ├─ Plugin Parsing
     └─ UI Rendering                         └─ Buffer Population
             │                                        │
             └────── SharedLogBuffer ←────────────────┘
                    (Thread-Safe Queue)
```

### Plugin System Details

Plugins must define a `SCHEMA` dictionary containing:
- **Field definitions**: Name, type, and parsing rules for each log field
- **Supported field types**: 
  - `string`: Text fields
  - `int`, `float`: Numeric fields  
  - `epoch`: Unix timestamp (seconds since epoch)
  - `strptime`: DateTime with custom format string
  - `float_timestamp`: Raw float timestamp (not converted to datetime)
  - `enum`: Enumerated values with raw value storage and display mapping
- **Regex pattern**: For line parsing (optional if custom parser provided)
- **Timestamp field**: Which field contains the chronological timestamp
- **Enum display maps**: Pre-built mappings from raw values to friendly display names

Optional `parse_raw_line()` function enables custom parsing logic beyond regex.

**Important**: Plugins should return raw enum values in the `fields` dictionary, not display names. The display layer handles friendly name mapping automatically.

### Key Design Decisions

1. **Polling vs. File Watching**: Uses polling for cross-platform compatibility and simplicity
2. **Binary Search Insertion**: Maintains chronological order efficiently (O(log n))
3. **Shared Buffer**: Prevents UI blocking during high-volume log processing
4. **Caching Strategy**: Multiple cache layers (datetime strings, colors, filtered entries, enum display maps)
5. **Follow Mode**: Smart auto-scroll that respects user manual scrolling
6. **Timestamp Flexibility**: Supports both datetime objects and raw float timestamps for different use cases
7. **Enum Architecture**: Raw value storage with display-time mapping for performance and consistency

## Plugins

LogMerge uses a plugin system to support various log formats. Built-in plugins include:

-   `dbglog_plugin`: For a generic debug log format.
-   `canking_plugin`: For CAN King log files.

You can create custom plugins by defining a Python file with a `SCHEMA` dictionary. The `SCHEMA` should describe the log file structure, including regex for parsing lines and field definitions. An optional `parse_raw_line` function can be provided for more complex parsing logic.

## License

This project is licensed under the terms of the LICENSE file.
