# LogMerge

A GUI application for viewing and analyzing multiple log files with advanced filtering and merging capabilities.

## Features

- Merges and displays multiple log files in a single view, ordered chronologically by timestamp.
- Live log monitoring with auto-scrolling to follow the latest entries.
- Add log files individually or discover them recursively in directories with regex filtering for filenames.
- Plugin-based parsing system to support different log formats.
- Advanced filtering and search capabilities supporting discrete values, numeric ranges, text patterns (with regex), and time-based queries.
- Color-coded file identification for easy visual distinction.
- Configurable column display and ordering.

## Future Work

The following features are being considered for future releases:

- **Advanced Schema Handling**: Enhance support for multiple log formats within a single session. This is a complex feature, as it raises the question of how to merge and display logs with different columns. A potential approach could be to fall back to a common denominator schema (e.g., only `timestamp` and a raw `message` field) when multiple schemas are present. This could involve manually assigning plugins per file or automatically detecting the appropriate schema by analyzing file content.
- **Compressed File Support**: Add transparent decompression for log files in common archive formats like `.gz` and `.zip`.
- **Automatic Log Rotation Handling**: Implement more robust file monitoring that can detect and automatically follow log rotation patterns (e.g., `app.log` -> `app.log.1`).
- **Session Management and Data Export**: Develop features for saving and loading application sessions (including loaded files, filters, and UI state) and exporting the merged log view to formats like CSV or plain text.

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


## Writing a Plugin

LogMerge can be extended to support any text-based log format by creating a custom plugin. A plugin is a Python file placed in the `src/logmerge/plugins/` directory that provides a `SCHEMA` dictionary and an optional `parse_raw_line` function to handle parsing logic.

### The `SCHEMA` Dictionary

The `SCHEMA` is the core of the plugin, defining the structure of your log files. It tells LogMerge which fields to expect, their data types, and how to extract them from a log line.

Here is a breakdown of the keys in the `SCHEMA` dictionary:

-   `'fields'`: A list of dictionaries, where each dictionary defines a column in the log table.
    -   `'name'`: The name of the field (e.g., `'Timestamp'`, `'Level'`, `'Message'`).
    -   `'type'`: The data type of the field. Supported types are:
        -   `string`: Plain text.
        -   `int`, `float`: Numeric values.
        -   `epoch`: A Unix timestamp (seconds since epoch).
        -   `strptime`: A date/time string that requires a `strptime_format` key.
        -   `float_timestamp`: A high-precision floating-point timestamp.
        -   `enum`: A field with a fixed set of possible values. Requires an `enum_values` key within the same field definition.
        -   `'is_discrete'` (optional, for `string` type): A boolean indicating how to filter the field. If `True`, the UI will provide a dropdown with all unique values seen for this field (similar to an `enum`). If `False` or omitted, a free-text search box will be used.
    -   `'strptime_format'` (required for `strptime` type): The format string to parse the date/time (e.g., `'%Y-%m-%d %H:%M:%S,%f'`).
    -   `'enum_values'` (required for `enum` type): A list of dictionaries, each mapping a raw value to a display name.
        -   `'value'`: The raw value as it appears in the log file.
        -   `'name'`: The human-readable name for display in the UI.

-   `'regex'`: A regular expression with **named capture groups** that correspond to the `name` of each field. This is the primary method for parsing lines.

-   `'timestamp_field'`: The `name` of the field that contains the primary timestamp. This is a **mandatory** field, as all log entries must have a timestamp for chronological merging and sorting.

#### Example `SCHEMA`

```python
# Example for a log line: "2023-10-27 10:30:00.123 | INFO | 0 | User logged in"
SCHEMA = {
    'fields': [
        {'name': 'Timestamp', 'type': 'strptime', 'strptime_format': '%Y-%m-%d %H:%M:%S.%f'},
        {
            'name': 'Level',
            'type': 'enum',
            'enum_values': [
                {'value': 'INFO', 'name': 'Information'},
                {'value': 'WARN', 'name': 'Warning'},
                {'value': 'ERROR', 'name': 'Error'},
            ]
        },
        {'name': 'Code', 'type': 'int'},
        {'name': 'Message', 'type': 'string'},
    ],
    'regex': r'^(?P<Timestamp>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3}) \| (?P<Level>\w+) \| (?P<Code>\d+) \| (?P<Message>.*)$',
    'timestamp_field': 'Timestamp',
}
```

### Parsing Logic: Regex vs. Custom Function

You have two options for parsing log lines:

1.  **Regex (Default)**: If your `SCHEMA` contains a `'regex'` key, LogMerge's built-in parser will use it to extract data. The named capture groups in your regex **must** match the field names defined in `'fields'`. This is the simplest and most common method.

2.  **Custom `parse_raw_line()` Function (Optional)**: For more complex formats where a single regex is insufficient (e.g., multi-line entries, conditional parsing, non-text formats), you can define a `parse_raw_line(line: str) -> dict | None` function in your plugin file.

    -   This function receives the raw log line as a string.
    -   You are responsible for all parsing logic inside this function.
    -   It must return a dictionary where keys are the field names and values are the parsed data in the correct type.
    -   If a line cannot be parsed, the function should return `None`.
    -   If this function exists, the `'regex'` key in the `SCHEMA` will be ignored.

#### Example `parse_raw_line`

```python
# A simple custom parser that splits a CSV-like line
# from log: "1672531200.5,DEBUG,Login successful"
def parse_raw_line(line: str) -> dict | None:
    parts = line.strip().split(',')
    if len(parts) != 3:
        return None
    
    try:
        return {
            "Timestamp": float(parts[0]),
            "Level": parts[1],
            "Message": parts[2],
        }
    except (ValueError, IndexError):
        return None

# The SCHEMA would still define fields, but not the regex
SCHEMA = {
    'fields': [
        {'name': 'Timestamp', 'type': 'float_timestamp'},
        {'name': 'Level', 'type': 'string'},
        {'name': 'Message', 'type': 'string'},
    ],
    'timestamp_field': 'Timestamp',
    # No 'regex' needed here
}
```

**Important**: When returning data from `parse_raw_line`, ensure the values for `enum` fields are the raw values found in the log file, not the display names. The UI handles the mapping automatically.

## Built-in Plugins

LogMerge includes several plugins to support common log formats out of the box:

-   `syslog_plugin`: For standard syslog messages (RFC 3164).
-   `dbglog_plugin`: For a generic debug log format.
-   `canking_plugin`: For CAN King log files.

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

### Key Design Decisions

1. **Polling vs. File Watching**: Uses polling for cross-platform compatibility and simplicity
2. **Binary Search Insertion**: Maintains chronological order efficiently (O(log n))
3. **Shared Buffer**: Prevents UI blocking during high-volume log processing
4. **Caching Strategy**: Multiple cache layers (datetime strings, colors, filtered entries, enum display maps)
5. **Follow Mode**: Smart auto-scroll that respects user manual scrolling
6. **Timestamp Flexibility**: Supports both datetime objects and raw float timestamps for different use cases
7. **Enum Architecture**: Raw value storage with display-time mapping for performance and consistency

## License

This project is licensed under the terms of the LICENSE file.
