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
