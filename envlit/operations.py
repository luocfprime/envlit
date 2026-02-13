"""
Atomic environment variable operations.
Each operation is a pure function: (current_value, op_config) -> new_value
"""

from typing import Any


def apply_operation(current_value: str | None, operation: dict[str, Any]) -> str | None:
    """
    Apply a single atomic operation to a value.

    Args:
        current_value: Current value of the variable (None if unset)
        operation: Operation dict with 'op' and optional 'value' keys

    Returns:
        New value after operation (None means unset)

    Raises:
        ValueError: If operation is invalid
    """
    op = operation.get("op")

    if op == "set":
        return str(operation["value"])

    elif op == "unset":
        return None

    elif op == "prepend":
        value = str(operation["value"])
        separator = operation.get("separator", ":")
        if current_value is None or current_value == "":
            return value
        return f"{value}{separator}{current_value}"

    elif op == "append":
        value = str(operation["value"])
        separator = operation.get("separator", ":")
        if current_value is None or current_value == "":
            return value
        return f"{current_value}{separator}{value}"

    elif op == "remove":
        value = str(operation["value"])
        separator = operation.get("separator", ":")
        if current_value is None or current_value == "":
            return None
        parts = [p for p in current_value.split(separator) if p and p != value]
        return separator.join(parts) if parts else None

    else:
        raise ValueError(f"Unknown operation: {op}")


def apply_operations(initial_value: str | None, operations: list[dict[str, Any]]) -> str | None:
    """
    Apply a pipeline of operations sequentially.

    Args:
        initial_value: Starting value (None if unset)
        operations: List of operation dicts

    Returns:
        Final value after all operations
    """
    current = initial_value
    for op in operations:
        current = apply_operation(current, op)
    return current


def validate_operation(operation: dict[str, Any]) -> None:
    """
    Validate an operation dictionary.

    Raises:
        ValueError: If operation is invalid
    """
    if not isinstance(operation, dict):
        raise TypeError(f"Operation must be a dict, got {type(operation)}")

    if "op" not in operation:
        raise ValueError("Operation must have 'op' field")

    op = operation["op"]
    valid_ops = ["set", "unset", "prepend", "append", "remove"]

    if op not in valid_ops:
        raise ValueError(f"Invalid operation '{op}'. Must be one of: {valid_ops}")

    # Operations that require 'value'
    if op in ["set", "prepend", "append", "remove"] and "value" not in operation:
        raise ValueError(f"Operation '{op}' requires 'value' field")

    # Operations that should NOT have 'value'
    if op == "unset" and "value" in operation:
        raise ValueError(f"Operation '{op}' should not have 'value' field")


def normalize_env_value(value: Any) -> list[dict[str, Any]]:
    """
    Normalize an environment value to a list of operations.

    Handles three formats:
    - String: Converted to [{"op": "set", "value": string}]
    - Dict: Converted to [dict] (single operation)
    - List of dicts: Returned as-is (pipeline of operations)

    Args:
        value: The value from the env section of config

    Returns:
        List of operation dictionaries

    Raises:
        ValueError: If value format is invalid
    """
    if value is None:
        # None/null means unset
        return [{"op": "unset"}]
    elif isinstance(value, str):
        # String shorthand for set operation
        return [{"op": "set", "value": value}]
    elif isinstance(value, dict):
        # Single operation
        return [value]
    elif isinstance(value, list):
        # Pipeline of operations
        if not all(isinstance(item, dict) for item in value):
            raise ValueError("List must contain only operation dictionaries")
        return value
    else:
        raise ValueError(f"Invalid env value type: {type(value).__name__}")
