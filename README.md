# LogMerge

A GUI application for viewing and analyzing multiple log files with advanced filtering and merging capabilities.

## Features

- Multi-file log viewing with real-time updates
- Plugin-based parsing system for different log formats
- Advanced filtering and search capabilities
- Color-coded file identification
- Live log monitoring with follow mode
- Configurable column display and ordering

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

## Plugins

LogMerge uses a plugin system to support various log formats. Built-in plugins include:

-   `dbglog_plugin`: For a generic debug log format.
-   `canking_plugin`: For CAN King log files.

You can create custom plugins by defining a Python file with a `SCHEMA` dictionary. The `SCHEMA` should describe the log file structure, including regex for parsing lines and field definitions. An optional `parse_raw_line` function can be provided for more complex parsing logic.

## License

This project is licensed under the terms of the LICENSE file.
