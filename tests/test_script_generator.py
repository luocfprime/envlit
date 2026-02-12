"""
Tests for script generation functionality.
"""

from envlit.script_generator import generate_load_script, generate_unload_script


class TestScriptGenerator:
    """Test script generation from config."""

    def test_simple_script_generation(self):
        """Test generating a simple load script."""
        config = {
            "env": {
                "MY_VAR": "simple_value",
                "ANOTHER_VAR": "another_value",
            },
            "flags": {},
            "hooks": {},
        }

        script = generate_load_script(config)

        assert "envlit-internal-track begin" in script
        assert "envlit-internal-track end" in script
        assert 'export MY_VAR="simple_value"' in script
        assert 'export ANOTHER_VAR="another_value"' in script

    def test_script_with_variable_references(self):
        """Test that variable references are NOT expanded (shell will handle it)."""
        config = {
            "env": {
                "PROJECT_ROOT": "${HOME}/projects/myapp",
                "PYTHONPATH": "${PROJECT_ROOT}/src",
            },
            "flags": {},
            "hooks": {},
        }

        script = generate_load_script(config)

        # Should preserve ${HOME} and ${PROJECT_ROOT} for shell expansion
        assert 'export PROJECT_ROOT="${HOME}/projects/myapp"' in script
        assert 'export PYTHONPATH="${PROJECT_ROOT}/src"' in script

    def test_script_with_path_operations(self):
        """Test generating script with PATH operations."""
        config = {
            "env": {
                "PATH": [
                    {"op": "prepend", "value": "${HOME}/.local/bin"},
                    {"op": "remove", "value": "/bad/path"},
                ]
            },
            "flags": {},
            "hooks": {},
        }

        script = generate_load_script(config)

        # Should generate PATH manipulation using path_ops
        assert "PATH" in script
        assert "${HOME}/.local/bin" in script

    def test_script_with_hooks(self):
        """Test generating script with pre/post hooks."""
        config = {
            "env": {"MY_VAR": "value"},
            "flags": {},
            "hooks": {
                "pre_load": [{"name": "Check VPN", "script": "echo 'Checking VPN...'"}],
                "post_load": [{"name": "Notify", "script": "echo 'Environment loaded!'"}],
            },
        }

        script = generate_load_script(config)

        # Hooks should be in the right order
        lines = script.split("\n")
        begin_idx = next(i for i, line in enumerate(lines) if "envlit-internal-track begin" in line)
        check_vpn_idx = next(i for i, line in enumerate(lines) if "Checking VPN" in line)
        export_idx = next(i for i, line in enumerate(lines) if 'export MY_VAR="value"' in line)
        notify_idx = next(i for i, line in enumerate(lines) if "Environment loaded" in line)
        end_idx = next(i for i, line in enumerate(lines) if "envlit-internal-track end" in line)

        # Order: begin -> pre_load -> exports -> post_load -> end
        assert begin_idx < check_vpn_idx < export_idx < notify_idx < end_idx

    def test_script_with_unset_variable(self):
        """Test generating script that unsets a variable."""
        config = {
            "env": {
                "UNSET_ME": None,  # null means unset
            },
            "flags": {},
            "hooks": {},
        }

        script = generate_load_script(config)

        assert "unset UNSET_ME" in script

    def test_script_with_empty_string_variable(self):
        """Test generating script that sets variable to empty string."""
        config = {
            "env": {
                "EMPTY_VAR": "",
            },
            "flags": {},
            "hooks": {},
        }

        script = generate_load_script(config)

        assert 'export EMPTY_VAR=""' in script

    def test_unload_script_generation(self):
        """Test generating unload script."""
        config = {
            "env": {},
            "flags": {},
            "hooks": {
                "pre_unload": [{"name": "Cleanup", "script": "echo 'Cleaning up...'"}],
                "post_unload": [{"name": "Done", "script": "echo 'Done!'"}],
            },
        }

        script = generate_unload_script(config)

        # Should contain pre_unload hooks and restoration logic
        assert "Cleaning up" in script
        assert "Done!" in script

    def test_script_with_special_characters(self):
        """Test generating script with special shell characters."""
        config = {
            "env": {
                "SPECIAL": "value with spaces",
                "QUOTED": 'value with "quotes"',
                "DOLLAR": "value with $dollar",
            },
            "flags": {},
            "hooks": {},
        }

        script = generate_load_script(config)

        # Should properly escape/quote values
        assert 'export SPECIAL="value with spaces"' in script
        # Quotes should be escaped or handled properly
        assert "QUOTED" in script
        # Dollar sign should be handled (not expanded by Python)
        assert "DOLLAR" in script


class TestEscapeShellValue:
    """Test cases for escape_shell_value function."""

    def test_simple_string(self):
        """Test escaping simple string without special characters."""
        from envlit.script_generator import escape_shell_value

        result = escape_shell_value("simple_value")
        assert result == "simple_value"

    def test_string_with_spaces(self):
        """Test escaping string with spaces."""
        from envlit.script_generator import escape_shell_value

        result = escape_shell_value("value with spaces")
        assert result == "value with spaces"

    def test_string_with_double_quotes(self):
        """Test escaping string with double quotes."""
        from envlit.script_generator import escape_shell_value

        result = escape_shell_value('value with "quotes"')
        assert result == 'value with \\"quotes\\"'

    def test_string_with_backslash(self):
        """Test escaping string with backslashes."""
        from envlit.script_generator import escape_shell_value

        result = escape_shell_value("path\\to\\file")
        assert result == "path\\\\to\\\\file"

    def test_string_with_backticks(self):
        """Test escaping string with backticks."""
        from envlit.script_generator import escape_shell_value

        result = escape_shell_value("value with `command`")
        assert result == "value with \\`command\\`"

    def test_string_with_newline(self):
        """Test escaping string with newlines."""
        from envlit.script_generator import escape_shell_value

        result = escape_shell_value("line1\nline2")
        assert result == "line1\\nline2"

    def test_preserve_simple_variable(self):
        """Test that simple $VAR references are preserved."""
        from envlit.script_generator import escape_shell_value

        result = escape_shell_value("${HOME}/projects")
        assert result == "${HOME}/projects"

        result = escape_shell_value("$HOME/projects")
        assert result == "$HOME/projects"

    def test_preserve_variable_with_default(self):
        """Test that ${VAR:-default} syntax is preserved."""
        from envlit.script_generator import escape_shell_value

        result = escape_shell_value("${VAR:-default_value}")
        assert result == "${VAR:-default_value}"

    def test_preserve_variable_with_substring(self):
        """Test that ${VAR:0:5} substring syntax is preserved."""
        from envlit.script_generator import escape_shell_value

        result = escape_shell_value("${PATH:0:10}")
        assert result == "${PATH:0:10}"

    def test_preserve_variable_with_substitution(self):
        """Test that ${VAR/old/new} substitution syntax is preserved."""
        from envlit.script_generator import escape_shell_value

        result = escape_shell_value("${PATH/old/new}")
        assert result == "${PATH/old/new}"

    def test_mixed_variables_and_special_chars(self):
        """Test string with both variables and special characters."""
        from envlit.script_generator import escape_shell_value

        result = escape_shell_value('${HOME}/path with "quotes"')
        assert result == '${HOME}/path with \\"quotes\\"'

    def test_multiple_variables(self):
        """Test string with multiple variable references."""
        from envlit.script_generator import escape_shell_value

        result = escape_shell_value("${HOME}/projects/${PROJECT_NAME}/src")
        assert result == "${HOME}/projects/${PROJECT_NAME}/src"

    def test_dollar_sign_not_part_of_variable(self):
        """Test that $ not part of a variable is escaped."""
        from envlit.script_generator import escape_shell_value

        result = escape_shell_value("price is $100")
        assert result == "price is \\$100"

    def test_complex_parameter_expansion(self):
        """Test complex parameter expansion patterns."""
        from envlit.script_generator import escape_shell_value

        # Default value with quotes - quotes inside ${} are preserved as-is
        result = escape_shell_value('${VAR:-"default with quotes"}')
        assert result == '${VAR:-"default with quotes"}'

        # Alternative value
        result = escape_shell_value("${VAR:+alternative}")
        assert result == "${VAR:+alternative}"

        # Length
        result = escape_shell_value("${#VAR}")
        assert result == "${#VAR}"

    def test_combined_escaping(self):
        """Test string with multiple types of special characters."""
        from envlit.script_generator import escape_shell_value

        result = escape_shell_value('${HOME}/path\\with "quotes" and `backticks` and $100')
        assert result == '${HOME}/path\\\\with \\"quotes\\" and \\`backticks\\` and \\$100'
