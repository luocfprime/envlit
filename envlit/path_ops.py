"""
PATH manipulation operations.
Supports prepend, append, and remove operations on PATH-like variables.
"""

from typing import Any


def apply_path_operations(
    original: str | None,
    operations: list[dict[str, Any]],
    default_separator: str = ":",
) -> str:
    """
    Apply a series of operations to a PATH-like variable.

    Args:
        original: The original PATH value (can be None for unset).
        operations: List of operation dictionaries with keys:
            - op: "prepend", "append", or "remove"
            - value: The path value to add/remove
            - separator: Optional custom separator (default: ":")
        default_separator: Default separator to use if not specified in operation.

    Returns:
        The modified PATH string.
    """
    # Handle None or empty original
    if original is None:
        original = ""

    # Split the path into components
    current_paths = [p for p in original.split(default_separator) if p] if original else []

    for operation in operations:
        op_type = operation.get("op")
        value = operation.get("value", "")

        if op_type == "prepend":
            # Add to the beginning
            current_paths.insert(0, value)
        elif op_type == "append":
            # Add to the end
            current_paths.append(value)
        elif op_type == "remove":
            # Remove all occurrences of the value
            current_paths = [p for p in current_paths if p != value]

    # Join back with the separator
    return default_separator.join(current_paths)
