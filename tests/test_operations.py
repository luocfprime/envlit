"""
Tests for atomic environment variable operations.
"""

import pytest

from envlit.operations import (
    apply_operation,
    apply_operations,
    normalize_env_value,
    validate_operation,
)


class TestApplyOperation:
    """Test individual atomic operations."""

    def test_set_operation_with_none(self):
        """Test set operation on unset variable."""
        result = apply_operation(None, {"op": "set", "value": "hello"})
        assert result == "hello"

    def test_set_operation_replaces_existing(self):
        """Test set operation replaces existing value."""
        result = apply_operation("old", {"op": "set", "value": "new"})
        assert result == "new"

    def test_unset_operation(self):
        """Test unset operation returns None."""
        result = apply_operation("value", {"op": "unset"})
        assert result is None

    def test_unset_on_none(self):
        """Test unset on already unset variable."""
        result = apply_operation(None, {"op": "unset"})
        assert result is None

    def test_prepend_to_none(self):
        """Test prepend to unset variable."""
        result = apply_operation(None, {"op": "prepend", "value": "/new/path"})
        assert result == "/new/path"

    def test_prepend_to_empty(self):
        """Test prepend to empty string."""
        result = apply_operation("", {"op": "prepend", "value": "/new/path"})
        assert result == "/new/path"

    def test_prepend_to_existing(self):
        """Test prepend to existing value."""
        result = apply_operation("/usr/bin:/bin", {"op": "prepend", "value": "/usr/local/bin"})
        assert result == "/usr/local/bin:/usr/bin:/bin"

    def test_prepend_custom_separator(self):
        """Test prepend with custom separator."""
        result = apply_operation("b,c", {"op": "prepend", "value": "a", "separator": ","})
        assert result == "a,b,c"

    def test_append_to_none(self):
        """Test append to unset variable."""
        result = apply_operation(None, {"op": "append", "value": "/new/path"})
        assert result == "/new/path"

    def test_append_to_empty(self):
        """Test append to empty string."""
        result = apply_operation("", {"op": "append", "value": "/new/path"})
        assert result == "/new/path"

    def test_append_to_existing(self):
        """Test append to existing value."""
        result = apply_operation("/usr/bin:/bin", {"op": "append", "value": "/opt/bin"})
        assert result == "/usr/bin:/bin:/opt/bin"

    def test_append_custom_separator(self):
        """Test append with custom separator."""
        result = apply_operation("a,b", {"op": "append", "value": "c", "separator": ","})
        assert result == "a,b,c"

    def test_remove_from_none(self):
        """Test remove from unset variable."""
        result = apply_operation(None, {"op": "remove", "value": "/some/path"})
        assert result is None

    def test_remove_from_empty(self):
        """Test remove from empty string."""
        result = apply_operation("", {"op": "remove", "value": "/some/path"})
        assert result is None

    def test_remove_single_occurrence(self):
        """Test remove single occurrence."""
        result = apply_operation("/usr/bin:/old:/bin", {"op": "remove", "value": "/old"})
        assert result == "/usr/bin:/bin"

    def test_remove_multiple_occurrences(self):
        """Test remove all occurrences."""
        result = apply_operation("/usr/bin:/old:/bin:/old", {"op": "remove", "value": "/old"})
        assert result == "/usr/bin:/bin"

    def test_remove_only_element(self):
        """Test remove when it's the only element."""
        result = apply_operation("/only", {"op": "remove", "value": "/only"})
        assert result is None

    def test_remove_nonexistent(self):
        """Test remove element that doesn't exist."""
        result = apply_operation("/usr/bin:/bin", {"op": "remove", "value": "/not/there"})
        assert result == "/usr/bin:/bin"

    def test_remove_custom_separator(self):
        """Test remove with custom separator."""
        result = apply_operation("a,b,c,b", {"op": "remove", "value": "b", "separator": ","})
        assert result == "a,c"

    def test_unknown_operation_raises_error(self):
        """Test unknown operation raises ValueError."""
        with pytest.raises(ValueError, match="Unknown operation: invalid"):
            apply_operation("value", {"op": "invalid"})


class TestApplyOperations:
    """Test pipeline of operations."""

    def test_empty_operations_list(self):
        """Test empty operations list returns initial value."""
        result = apply_operations("initial", [])
        assert result == "initial"

    def test_single_operation(self):
        """Test single operation in list."""
        result = apply_operations(None, [{"op": "set", "value": "hello"}])
        assert result == "hello"

    def test_sequential_path_operations(self):
        """Test PATH-style operations in sequence."""
        operations = [
            {"op": "remove", "value": "/old/path"},
            {"op": "prepend", "value": "/new/path"},
            {"op": "append", "value": "/opt/path"},
        ]
        initial = "/usr/bin:/old/path:/bin"
        result = apply_operations(initial, operations)
        assert result == "/new/path:/usr/bin:/bin:/opt/path"

    def test_set_then_prepend(self):
        """Test set followed by prepend."""
        operations = [
            {"op": "set", "value": "/base"},
            {"op": "prepend", "value": "/prefix"},
        ]
        result = apply_operations("/original", operations)
        assert result == "/prefix:/base"

    def test_unset_then_set(self):
        """Test unset followed by set."""
        operations = [
            {"op": "unset"},
            {"op": "set", "value": "new"},
        ]
        result = apply_operations("old", operations)
        assert result == "new"

    def test_complex_pipeline(self):
        """Test complex pipeline of operations."""
        operations = [
            {"op": "remove", "value": "/bad"},
            {"op": "remove", "value": "/ugly"},
            {"op": "prepend", "value": "/good"},
            {"op": "append", "value": "/better"},
        ]
        initial = "/usr/bin:/bad:/local/bin:/ugly:/bin"
        result = apply_operations(initial, operations)
        assert result == "/good:/usr/bin:/local/bin:/bin:/better"


class TestValidateOperation:
    """Test operation validation."""

    def test_valid_set_operation(self):
        """Test valid set operation passes validation."""
        validate_operation({"op": "set", "value": "test"})
        # Should not raise

    def test_valid_unset_operation(self):
        """Test valid unset operation passes validation."""
        validate_operation({"op": "unset"})
        # Should not raise

    def test_valid_prepend_operation(self):
        """Test valid prepend operation passes validation."""
        validate_operation({"op": "prepend", "value": "/path"})
        # Should not raise

    def test_valid_append_operation(self):
        """Test valid append operation passes validation."""
        validate_operation({"op": "append", "value": "/path"})
        # Should not raise

    def test_valid_remove_operation(self):
        """Test valid remove operation passes validation."""
        validate_operation({"op": "remove", "value": "/path"})
        # Should not raise

    def test_non_dict_raises_error(self):
        """Test non-dict operation raises error."""
        with pytest.raises(TypeError, match="Operation must be a dict"):
            validate_operation("not a dict")

    def test_missing_op_field_raises_error(self):
        """Test missing 'op' field raises error."""
        with pytest.raises(ValueError, match="Operation must have 'op' field"):
            validate_operation({"value": "test"})

    def test_invalid_op_type_raises_error(self):
        """Test invalid operation type raises error."""
        with pytest.raises(ValueError, match="Invalid operation 'invalid'"):
            validate_operation({"op": "invalid"})

    def test_set_without_value_raises_error(self):
        """Test set operation without value raises error."""
        with pytest.raises(ValueError, match="Operation 'set' requires 'value' field"):
            validate_operation({"op": "set"})

    def test_prepend_without_value_raises_error(self):
        """Test prepend operation without value raises error."""
        with pytest.raises(ValueError, match="Operation 'prepend' requires 'value' field"):
            validate_operation({"op": "prepend"})

    def test_append_without_value_raises_error(self):
        """Test append operation without value raises error."""
        with pytest.raises(ValueError, match="Operation 'append' requires 'value' field"):
            validate_operation({"op": "append"})

    def test_remove_without_value_raises_error(self):
        """Test remove operation without value raises error."""
        with pytest.raises(ValueError, match="Operation 'remove' requires 'value' field"):
            validate_operation({"op": "remove"})

    def test_unset_with_value_raises_error(self):
        """Test unset operation with value raises error."""
        with pytest.raises(ValueError, match="Operation 'unset' should not have 'value' field"):
            validate_operation({"op": "unset", "value": "test"})


class TestNormalizeEnvValue:
    """Test environment value normalization."""

    def test_none_to_unset(self):
        """Test None is normalized to unset operation."""
        result = normalize_env_value(None)
        assert result == [{"op": "unset"}]

    def test_string_to_set(self):
        """Test string is normalized to set operation."""
        result = normalize_env_value("hello")
        assert result == [{"op": "set", "value": "hello"}]

    def test_dict_to_single_operation(self):
        """Test dict is normalized to single-item list."""
        result = normalize_env_value({"op": "prepend", "value": "/path"})
        assert result == [{"op": "prepend", "value": "/path"}]

    def test_list_of_dicts_unchanged(self):
        """Test list of dicts passes through unchanged."""
        operations = [
            {"op": "remove", "value": "/old"},
            {"op": "prepend", "value": "/new"},
        ]
        result = normalize_env_value(operations)
        assert result == operations

    def test_invalid_type_raises_error(self):
        """Test invalid type raises error."""
        with pytest.raises(ValueError, match="Invalid env value type"):
            normalize_env_value(123)

    def test_list_with_non_dict_raises_error(self):
        """Test list with non-dict items raises error."""
        with pytest.raises(ValueError, match="List must contain only operation dictionaries"):
            normalize_env_value([{"op": "set", "value": "a"}, "invalid"])

    def test_empty_string_to_set(self):
        """Test empty string is normalized to set operation."""
        result = normalize_env_value("")
        assert result == [{"op": "set", "value": ""}]


class TestIntegrationScenarios:
    """Test real-world usage scenarios."""

    def test_path_modification_scenario(self):
        """Test typical PATH modification workflow."""
        # Start with system PATH
        initial = "/usr/bin:/bin:/usr/sbin:/sbin"

        # User wants to: remove old tool, add new tool to front, add opt to end
        operations = [
            {"op": "remove", "value": "/usr/sbin"},
            {"op": "prepend", "value": "./venv/bin"},
            {"op": "append", "value": "/opt/homebrew/bin"},
        ]

        result = apply_operations(initial, operations)
        assert result == "./venv/bin:/usr/bin:/bin:/sbin:/opt/homebrew/bin"

    def test_pythonpath_scenario(self):
        """Test PYTHONPATH modification."""
        # Start with no PYTHONPATH
        operations = [
            {"op": "prepend", "value": "./src"},
            {"op": "append", "value": "./lib"},
        ]

        result = apply_operations(None, operations)
        assert result == "./src:./lib"

    def test_simple_variable_set(self):
        """Test simple environment variable set."""
        operations = normalize_env_value("Development")
        result = apply_operations(None, operations)
        assert result == "Development"

    def test_variable_unset(self):
        """Test unsetting a variable."""
        operations = normalize_env_value(None)
        result = apply_operations("old_value", operations)
        assert result is None

    def test_explicit_set_operation(self):
        """Test explicit set operation (dict syntax)."""
        operations = normalize_env_value({"op": "set", "value": "Production"})
        result = apply_operations(None, operations)
        assert result == "Production"

    def test_single_prepend_operation(self):
        """Test single prepend operation (not in list)."""
        operations = normalize_env_value({"op": "prepend", "value": "./venv/bin"})
        result = apply_operations("/usr/bin:/bin", operations)
        assert result == "./venv/bin:/usr/bin:/bin"
