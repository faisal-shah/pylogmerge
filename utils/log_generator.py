#!/usr/bin/env python3
"""
Synthetic Log File Generator

Generates log files according to a plugin schema for testing the merged log viewer.
Creates realistic log entries with proper timestamp progression and structured data.
"""

import argparse
import importlib.util
import os
import random
import re
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Tuple


class LogGenerator:
    def __init__(self, plugin_path: str, root_dir: str, num_files: int, max_depth: int, seed: int = None):
        self.plugin_path = plugin_path
        self.root_dir = Path(root_dir)
        self.num_files = num_files
        self.max_depth = max_depth
        
        if seed is not None:
            random.seed(seed)
        
        self.schema = self._load_schema_from_plugin()
        self.fields = self.schema['fields']
        self.regex_pattern = self.schema.get('regex', '')
        
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

    def _generate_field_value(self, field: Dict[str, Any], base_time: datetime, 
                            line_offset: float) -> Tuple[str, Any]:
        """Generate a value for a specific field based on its type."""
        field_type = field['type']
        field_name = field['name']
        
        if field_type == 'epoch':
            # Use base_time + offset for natural progression
            dt = base_time + timedelta(seconds=line_offset)
            # Generate Unix timestamp with microseconds for epoch type
            unix_timestamp = dt.timestamp()
            # Add some random microseconds for realism
            microseconds = random.randint(0, 999999)
            formatted_timestamp = f"{int(unix_timestamp)}.{microseconds:06d}"
            return formatted_timestamp, dt
                
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

    def _generate_log_line(self, base_time: datetime, line_offset: float) -> str:
        """Generate a single log line according to the schema."""
        field_values = {}
        
        # Generate values for each field
        for field in self.fields:
            str_value, parsed_value = self._generate_field_value(field, base_time, line_offset)
            field_values[field['name']] = str_value
        
        # Try to construct the log line by replacing named groups in a template
        # This is a simplified approach - in reality, we'd need to reverse-engineer
        # the exact format from the regex, but for generation purposes, we'll use
        # a reasonable default format
        
        # Extract field order from regex named groups
        pattern = re.compile(self.regex_pattern)
        group_names = pattern.groupindex.keys()
        
        # Create log line with fields in the order they appear in the regex
        line_parts = []
        for group_name in group_names:
            if group_name in field_values:
                line_parts.append(field_values[group_name])
        
        # If we couldn't parse the regex properly, fall back to schema order
        if not line_parts:
            line_parts = [field_values[field['name']] for field in self.fields]
        
        return ' '.join(line_parts)

    def _generate_log_file(self, file_path: Path, base_time: datetime, 
                          lines_per_file: int) -> None:
        """Generate a single log file with realistic content."""
        with open(file_path, 'w') as f:
            for i in range(lines_per_file):
                # Add some randomness to timing between lines (0-60 seconds)
                line_offset = i * random.uniform(0.1, 60.0)
                log_line = self._generate_log_line(base_time, line_offset)
                f.write(log_line + '\n')

    def generate(self) -> None:
        """Generate all log files according to the configuration."""
        print(f"Generating {self.num_files} log files in {self.root_dir}")
        print(f"Maximum directory depth: {self.max_depth}")
        print(f"Using plugin: {self.plugin_path}")
        
        # Create directory structure
        directories = self._create_directory_structure()
        print(f"Created {len(directories)} directories")
        
        # Generate log files
        base_time = datetime.now() - timedelta(days=7)  # Start a week ago
        lines_per_file = random.randint(50, 500)  # Vary file sizes
        
        for i in range(self.num_files):
            # Choose random directory
            target_dir = random.choice(directories)
            
            # Generate filename
            file_types = ['application', 'system', 'access', 'error', 'debug', 'audit']
            file_type = random.choice(file_types)
            timestamp_str = (base_time + timedelta(days=i)).strftime('%Y%m%d')
            filename = f"{file_type}_{timestamp_str}_{i:03d}.log"
            
            file_path = target_dir / filename
            
            # Vary the base time for each file to create realistic timestamps
            file_base_time = base_time + timedelta(days=random.uniform(0, 6))
            
            # Vary lines per file
            current_lines = random.randint(20, 200)
            
            self._generate_log_file(file_path, file_base_time, current_lines)
            print(f"Generated: {file_path} ({current_lines} lines)")
        
        print(f"\nLog generation complete!")
        print(f"Files created in: {self.root_dir}")


def main():
    parser = argparse.ArgumentParser(description='Generate synthetic log files for testing')
    parser.add_argument('--plugin', required=True, help='Path to plugin Python file')
    parser.add_argument('--root-dir', required=True, help='Root directory for log files')
    parser.add_argument('--num-files', type=int, required=True, help='Number of log files to generate')
    parser.add_argument('--max-depth', type=int, required=True, help='Maximum directory nesting depth')
    parser.add_argument('--seed', type=int, help='Random seed for reproducible generation')
    
    args = parser.parse_args()
    
    try:
        generator = LogGenerator(
            plugin_path=args.plugin,
            root_dir=args.root_dir,
            num_files=args.num_files,
            max_depth=args.max_depth,
            seed=args.seed
        )
        generator.generate()
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0


if __name__ == '__main__':
    exit(main())
