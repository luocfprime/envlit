"""
Tests for PATH manipulation operations.
"""

from envlit.path_ops import apply_path_operations


class TestPathOperations:
    """Test suite for PATH operations."""

    def test_prepend_single_value(self):
        """Test prepending a single value to PATH."""
        original = "/usr/bin:/bin"
        operations = [{"op": "prepend", "value": "/custom/bin"}]
        result = apply_path_operations(original, operations)
        assert result == "/custom/bin:/usr/bin:/bin"

    def test_append_single_value(self):
        """Test appending a single value to PATH."""
        original = "/usr/bin:/bin"
        operations = [{"op": "append", "value": "/custom/bin"}]
        result = apply_path_operations(original, operations)
        assert result == "/usr/bin:/bin:/custom/bin"

    def test_remove_value(self):
        """Test removing a value from PATH."""
        original = "/usr/bin:/bad/path:/bin"
        operations = [{"op": "remove", "value": "/bad/path"}]
        result = apply_path_operations(original, operations)
        assert result == "/usr/bin:/bin"

    def test_remove_nonexistent_value(self):
        """Test removing a value that doesn't exist (should be no-op)."""
        original = "/usr/bin:/bin"
        operations = [{"op": "remove", "value": "/nonexistent"}]
        result = apply_path_operations(original, operations)
        assert result == "/usr/bin:/bin"

    def test_pipeline_operations(self):
        """Test multiple operations in sequence."""
        original = "/usr/bin:/bad/path:/bin"
        operations = [
            {"op": "remove", "value": "/bad/path"},
            {"op": "prepend", "value": "./bin"},
            {"op": "prepend", "value": "/home/user/.local/bin"},
        ]
        result = apply_path_operations(original, operations)
        assert result == "/home/user/.local/bin:./bin:/usr/bin:/bin"

    def test_custom_separator(self):
        """Test operations with a custom separator."""
        original = "/usr/bin;/bin"
        operations = [{"op": "prepend", "value": "/custom/bin", "separator": ";"}]
        result = apply_path_operations(original, operations, default_separator=";")
        assert result == "/custom/bin;/usr/bin;/bin"

    def test_empty_original_path(self):
        """Test operations on an empty PATH."""
        operations = [{"op": "prepend", "value": "/custom/bin"}]
        result = apply_path_operations("", operations)
        assert result == "/custom/bin"

    def test_none_original_path(self):
        """Test operations on None PATH (unset)."""
        operations = [{"op": "prepend", "value": "/custom/bin"}]
        result = apply_path_operations(None, operations)
        assert result == "/custom/bin"

    def test_prepend_to_empty_path(self):
        """Test prepending when PATH is empty."""
        operations = [
            {"op": "prepend", "value": "/first"},
            {"op": "prepend", "value": "/second"},
        ]
        result = apply_path_operations("", operations)
        assert result == "/second:/first"

    def test_append_to_empty_path(self):
        """Test appending when PATH is empty."""
        operations = [
            {"op": "append", "value": "/first"},
            {"op": "append", "value": "/second"},
        ]
        result = apply_path_operations("", operations)
        assert result == "/first:/second"

    def test_remove_all_occurrences(self):
        """Test that remove operation removes all occurrences."""
        original = "/dup:/usr/bin:/dup:/bin:/dup"
        operations = [{"op": "remove", "value": "/dup"}]
        result = apply_path_operations(original, operations)
        assert result == "/usr/bin:/bin"

    def test_no_operations(self):
        """Test with no operations (should return original)."""
        original = "/usr/bin:/bin"
        result = apply_path_operations(original, [])
        assert result == "/usr/bin:/bin"

    def test_mixed_separators_normalization(self):
        """Test that operations respect the specified separator."""
        original = "/usr/bin:/bin"
        operations = [
            {"op": "prepend", "value": "/custom", "separator": ":"},
        ]
        result = apply_path_operations(original, operations)
        assert result == "/custom:/usr/bin:/bin"

    def test_single_operation_dict(self):
        """Test that a single operation (not in a list) can be handled."""
        original = "/usr/bin:/bin"
        operation = {"op": "prepend", "value": "/custom/bin"}
        result = apply_path_operations(original, [operation])
        assert result == "/custom/bin:/usr/bin:/bin"
