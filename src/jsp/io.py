"""Functions for handling STDIN and STDOUT operations."""

import json
import sys
from typing import Any

from rich.console import Console

console = Console()


def read_json(file_path: str | None = None) -> dict:
    """Read JSON from a file path or stdin if no path is given."""
    try:
        if file_path:
            with open(file_path) as f:
                return json.load(f)

        if not sys.stdin.isatty():
            return json.load(sys.stdin)
    except json.JSONDecodeError as e:
        source = file_path or "stdin"
        raise ValueError(f"Invalid JSON from {source}: {e}") from e

    raise ValueError("No input provided. Pass a file path or pipe JSON via stdin.")


def print_json(data: dict, pretty: bool = True) -> None:
    if pretty:
        console.print_json(json.dumps(data, indent=4))
    else:
        print(json.dumps(data))


def _traverse(data, key: str, stop_before_last: bool = False) -> tuple[Any, str] | Any:
    """Traverse data using dot notation. Returns (parent, last_key) if stop_before_last, else the value."""
    keys = key.split(".")
    traverse_keys = keys[:-1] if stop_before_last else keys
    current = data

    for k in traverse_keys:
        if isinstance(current, list) and k.isdigit():
            index = int(k)
            if index < len(current):
                current = current[index]
            else:
                raise KeyError(f"Index {index} out of range in '{key}'.")
        elif isinstance(current, dict) and k in current:
            current = current[k]
        else:
            raise KeyError(f"Key '{key}' not found in the data.")

    if stop_before_last:
        return current, keys[-1]
    return current


def filter_by_key(data: dict, key: str) -> dict:
    """Filter a dictionary by a key, supporting dot notation for nested access."""
    return {key: _traverse(data, key)}


def update_json(data: dict, key: str, value) -> dict:
    """Modify a dictionary with a new value at a specified key, supporting dot notation."""
    parent, last_key = _traverse(data, key, stop_before_last=True)

    if isinstance(parent, list) and last_key.isdigit():
        index = int(last_key)
        if index < len(parent):
            parent[index] = value
        else:
            raise KeyError(f"Index {index} out of range in '{key}'.")
    elif isinstance(parent, dict):
        parent[last_key] = value
    else:
        raise KeyError(f"Cannot set value at '{key}'.")

    return data
