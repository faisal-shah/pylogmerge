#!/usr/bin/env python3
"""
Live Log File Generator

Continuously appends log entries to existing log files according to a plugin schema.
Perfect for testing live monitoring functionality of the merged log viewer.
Creates realistic log entries with proper timestamp progression and structured data.
"""

import argparse
import importlib.util
import json
import os
import random
import re
import signal
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Tuple


class LiveLogGenerator:
    def __init__(self, plugin_path: str, root_dir: str, num_files: int, max_depth: int, 
                 min_interval: float = 1.0, max_interval: float = 5.0, seed: int = None):
        self.plugin_path = plugin_path
        self.root_dir = Path(root_dir)
        self.num_files = num_files
        self.max_depth = max_depth
        self.min_interval = min_interval
        self.max_interval = max_interval
        self.running = True
        
        if seed is not None:
            random.seed(seed)
        
        self.schema = self._load_schema_from_plugin()
        self.fields = self.schema['fields']
        self.regex_pattern = self.schema.get('regex', '')
        
        # Track log files and their state
        self.log_files = []
        self.file_handles = {}
        self.next_log_times = {}
        
        # Common words for generating realistic log messages
        self.message_words = [
            'Started', 'Completed', 'Processing', 'Failed', 'Success', 'Error',
            'Request', 'Response', 'Connection', 'Database', 'Query', 'Update',
            'Insert', 'Delete', 'Fetch', 'Cache', 'Session', 'User', 'Admin',
            'Login', 'Logout', 'Authentication', 'Authorization', 'Validation',
            'Configuration', 'Service', 'API', 'Endpoint', 'Handler', 'Controller'
        ]
        
        self.action_words = [
            'initiated', 'completed', 'failed', 'successful', 'timeout', 'retry',
            'validated', 'processed', 'received', 'sent', 'created', 'updated',
            'deleted', 'retrieved', 'cached', 'expired', 'scheduled', 'executed'
        ]

    def _load_schema_from_plugin(self) -> Dict[str, Any]:
        """Load and validate the schema from a plugin file."""
        try:
            # Load the plugin module
            plugin_path = Path(self.plugin_path)
            if not plugin_path.exists():
                raise FileNotFoundError(f"Plugin file not found: {self.plugin_path}")
            
            # Import the plugin module
            spec = importlib.util.spec_from_file_location("plugin", plugin_path)
            if spec is None or spec.loader is None:
                raise ValueError(f"Could not load plugin spec from {self.plugin_path}")
            
            plugin_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(plugin_module)
            
            # Extract the SCHEMA
            if not hasattr(plugin_module, 'SCHEMA'):
                raise ValueError(f"Plugin {self.plugin_path} does not have a SCHEMA attribute")
            
            schema = plugin_module.SCHEMA
            
            # Validate required keys
            required_keys = ['fields']
            for key in required_keys:
                if key not in schema:
                    raise ValueError(f"Schema missing required key: {key}")
            
            print(f"Loaded schema from plugin: {self.plugin_path}")
            print(f"  - Fields: {len(schema['fields'])}")
            print(f"  - Timestamp field: {schema.get('timestamp_field', 'None')}")
            print(f"  - Has regex: {'Yes' if 'regex' in schema else 'No'}")
            
            return schema
            
        except Exception as e:
            raise ValueError(f"Error loading plugin {self.plugin_path}: {str(e)}")

    def _load_schema(self) -> Dict[str, Any]:
        """Load and validate the JSON schema. (DEPRECATED - use _load_schema_from_plugin)"""
        try:
            with open(self.schema_path, 'r') as f:
                schema = json.load(f)
            
            required_keys = ['regex', 'fields']
            for key in required_keys:
                if key not in schema:
                    raise ValueError(f"Schema missing required key: {key}")
            
            return schema
        except FileNotFoundError:
            raise FileNotFoundError(f"Schema file not found: {self.schema_path}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in schema file: {e}")

    def _discover_log_files(self) -> List[Path]:
        """Discover existing log files in the directory structure."""
        log_files = []
        
        if not self.root_dir.exists():
            print(f"Warning: Directory {self.root_dir} does not exist. Creating it...")
            self.root_dir.mkdir(parents=True, exist_ok=True)
            return log_files
        
        # Find existing .log files
        for file_path in self.root_dir.rglob("*.log"):
            if file_path.is_file():
                log_files.append(file_path)
        
        return sorted(log_files)

    def _create_missing_log_files(self, existing_files: List[Path]) -> List[Path]:
        """Create additional log files if we don't have enough."""
        if len(existing_files) >= self.num_files:
            return existing_files[:self.num_files]
        
        files_needed = self.num_files - len(existing_files)
        print(f"Found {len(existing_files)} existing log files, creating {files_needed} more...")
        
        # Create directory structure if needed
        directories = self._create_directory_structure()
        
        # Create additional files
        for i in range(files_needed):
            # Choose random directory
            target_dir = random.choice(directories)
            
            # Generate filename
            file_types = ['application', 'system', 'access', 'error', 'debug', 'audit']
            file_type = random.choice(file_types)
            timestamp_str = datetime.now().strftime('%Y%m%d')
            filename = f"{file_type}_{timestamp_str}_{i:03d}.log"
            
            file_path = target_dir / filename
            
            # Create empty file
            file_path.touch()
            existing_files.append(file_path)
            print(f"Created: {file_path}")
        
        return existing_files

    def _create_directory_structure(self) -> List[Path]:
        """Create random directory structure and return list of directories."""
        directories = [self.root_dir]
        
        # Create the root directory
        self.root_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate random subdirectories
        for _ in range(random.randint(1, max(2, self.num_files // 3))):
            depth = random.randint(1, self.max_depth)
            current_path = self.root_dir
            
            for level in range(depth):
                dir_names = ['logs', 'data', 'output', 'archive', 'temp', 'backup', 
                           'system', 'application', 'service', 'daily', 'weekly']
                dir_name = f"{random.choice(dir_names)}_{level}_{random.randint(1, 99):02d}"
                current_path = current_path / dir_name
                current_path.mkdir(parents=True, exist_ok=True)
                
                if current_path not in directories:
                    directories.append(current_path)
        
        return directories

    def _generate_field_value(self, field: Dict[str, Any], current_time: datetime) -> Tuple[str, Any]:
        """Generate a value for a specific field based on its type."""
        field_type = field['type']
        field_name = field['name']
        
        if field_type == 'epoch':
            # Generate Unix timestamp with microseconds for epoch type
            unix_timestamp = current_time.timestamp()
            # Add some random microseconds for realism
            microseconds = random.randint(0, 999999)
            formatted_timestamp = f"{int(unix_timestamp)}.{microseconds:06d}"
            return formatted_timestamp, current_time
                
        elif field_type == 'enum':
            enum_values = field['enum_values']
            chosen = random.choice(enum_values)
            return str(chosen['value']), chosen['name']
            
        elif field_type == 'int':
            if field.get('is_discrete', False):
                # Generate from a limited set of values for discrete fields
                discrete_values = [1, 2, 5, 10, 20, 50, 100, 200, 404, 500]
                value = random.choice(discrete_values)
            else:
                value = random.randint(1, 10000)
            return str(value), value
            
        elif field_type == 'float':
            if field.get('is_discrete', False):
                # Generate from a limited set of values for discrete fields
                discrete_values = [0.1, 0.5, 1.0, 1.5, 2.0, 5.0, 10.0]
                value = random.choice(discrete_values)
            else:
                value = random.uniform(0.1, 999.9)
            return f"{value:.2f}", value
            
        elif field_type == 'string':
            if field.get('is_discrete', False):
                # Generate from a limited set of values for discrete fields
                if field_name == 'module':
                    modules = [
                        "auth", "database", "cache", "api", "controller", "service",
                        "validator", "logger", "config", "scheduler", "worker",
                        "handler", "middleware", "router", "session", "security"
                    ]
                    value = random.choice(modules)
                else:
                    messages = [
                        "User login successful",
                        "Database connection established", 
                        "Cache miss - fetching from database",
                        "Request processed successfully",
                        "Session expired",
                        "Invalid credentials provided",
                        "File upload completed",
                        "Service unavailable",
                        "Configuration loaded",
                        "Backup process started"
                    ]
                    value = random.choice(messages)
            else:
                # Generate varied messages
                action = random.choice(self.action_words)
                subject = random.choice(self.message_words)
                value = f"{subject} {action}"
                
                # Sometimes add more detail
                if random.random() < 0.3:
                    detail = random.choice(['for user_123', 'in 45ms', 'with errors', 
                                         'successfully', 'after retry', 'from cache'])
                    value += f" {detail}"
            
            return value, value
        
        else:
            raise ValueError(f"Unknown field type: {field_type}")

    def _generate_log_line(self, current_time: datetime) -> str:
        """Generate a single log line according to the schema."""
        field_values = []
        
        # Generate values for each field in schema order
        for field in self.fields:
            str_value, parsed_value = self._generate_field_value(field, current_time)
            field_values.append(str_value)
        
        # Create simple space-separated log line
        # For complex formats that need special formatting, use custom parsing functions in plugins
        return ' '.join(field_values)

    def _schedule_next_log(self, file_path: Path):
        """Schedule the next log entry for a file."""
        current_time = time.time()
        interval = random.uniform(self.min_interval, self.max_interval)
        self.next_log_times[file_path] = current_time + interval

    def _write_log_entry(self, file_path: Path):
        """Write a single log entry to a file."""
        try:
            current_time = datetime.now()
            log_line = self._generate_log_line(current_time)
            
            # Open file in append mode if not already open
            if file_path not in self.file_handles:
                self.file_handles[file_path] = open(file_path, 'a', encoding='utf-8')
            
            # Write log entry
            self.file_handles[file_path].write(log_line + '\n')
            self.file_handles[file_path].flush()  # Ensure immediate write
            
            print(f"[{current_time.strftime('%H:%M:%S')}] {file_path.name}: {log_line}")
            
        except Exception as e:
            print(f"Error writing to {file_path}: {e}")

    def _close_all_files(self):
        """Close all open file handles."""
        for handle in self.file_handles.values():
            try:
                handle.close()
            except:
                pass
        self.file_handles.clear()

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully."""
        print(f"\nReceived signal {signum}. Shutting down gracefully...")
        self.running = False

    def generate(self):
        """Start the live log generation process."""
        print(f"Starting live log generation in {self.root_dir}")
        print(f"Log interval: {self.min_interval}s - {self.max_interval}s")
        print(f"Target files: {self.num_files}")
        print(f"Using plugin: {self.plugin_path}")
        print("Press Ctrl+C to stop...\n")
        
        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        try:
            # Discover existing log files
            existing_files = self._discover_log_files()
            
            # Create additional files if needed
            self.log_files = self._create_missing_log_files(existing_files)
            
            if not self.log_files:
                print("No log files to write to. Exiting.")
                return
            
            print(f"Monitoring {len(self.log_files)} log files:")
            for file_path in self.log_files:
                print(f"  - {file_path}")
                self._schedule_next_log(file_path)
            
            print("\nStarting live generation...\n")
            
            # Main generation loop
            while self.running:
                current_time = time.time()
                
                # Check each file to see if it's time to write a log entry
                for file_path in self.log_files:
                    if current_time >= self.next_log_times.get(file_path, 0):
                        self._write_log_entry(file_path)
                        self._schedule_next_log(file_path)
                
                # Sleep for a short interval to avoid busy waiting
                time.sleep(0.1)
                
        except KeyboardInterrupt:
            print("\nKeyboard interrupt received. Shutting down...")
        except Exception as e:
            print(f"Error during generation: {e}")
        finally:
            self._close_all_files()
            print("Live log generation stopped.")


def main():
    parser = argparse.ArgumentParser(description='Generate live log files for testing')
    parser.add_argument('--plugin', required=True, help='Path to plugin Python file')
    parser.add_argument('--root-dir', required=True, help='Root directory for log files')
    parser.add_argument('--num-files', type=int, required=True, help='Number of log files to maintain')
    parser.add_argument('--max-depth', type=int, required=True, help='Maximum directory nesting depth')
    parser.add_argument('--min-interval', type=float, default=1.0, help='Minimum seconds between log entries (default: 1.0)')
    parser.add_argument('--max-interval', type=float, default=5.0, help='Maximum seconds between log entries (default: 5.0)')
    parser.add_argument('--seed', type=int, help='Random seed for reproducible generation')
    
    args = parser.parse_args()
    
    # Validate intervals
    if args.min_interval <= 0:
        print("Error: min-interval must be greater than 0")
        return 1
    
    if args.max_interval <= args.min_interval:
        print("Error: max-interval must be greater than min-interval")
        return 1
    
    try:
        generator = LiveLogGenerator(
            plugin_path=args.plugin,
            root_dir=args.root_dir,
            num_files=args.num_files,
            max_depth=args.max_depth,
            min_interval=args.min_interval,
            max_interval=args.max_interval,
            seed=args.seed
        )
        generator.generate()
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
