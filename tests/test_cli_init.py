"""
Tests for envlit init command.
"""

import pytest
from click.testing import CliRunner

from envlit.cli import cli


@pytest.fixture
def runner():
    """Create a Click CLI test runner."""
    return CliRunner()


def test_init_default(runner, monkeypatch):
    """Test init command with default options."""
    # monkeypatch sets the env var for the duration of this test function
    monkeypatch.setenv("SHELL", "/bin/bash")

    result = runner.invoke(cli, ["init"])

    assert result.exit_code == 0
    output = result.output

    # Check for shell integration comment
    assert "# envlit shell integration" in output
    assert "# Generated for bash" in output

    # Check for default function names
    assert "el() {" in output
    assert "local tmp_script" in output
    assert "mktemp" in output
    assert 'envlit load "$@"' in output
    assert 'source "$tmp_script"' in output
    assert 'rm -f "$tmp_script"' in output

    assert "eul() {" in output
    assert 'envlit unload "$@"' in output


def test_init_custom_aliases(runner):
    """Test init command with custom alias names."""
    result = runner.invoke(cli, ["init", "--alias-load", "envload", "--alias-unload", "envunload"])

    assert result.exit_code == 0
    output = result.output

    # Check for custom function names
    assert "envload() {" in output
    assert "envunload() {" in output


def test_init_bash_shell(runner):
    """Test init command with bash shell specified."""
    result = runner.invoke(cli, ["init", "--shell", "bash"])

    assert result.exit_code == 0
    output = result.output

    assert "# Generated for bash" in output
    assert "el() {" in output
    assert "eul() {" in output


def test_init_zsh_shell(runner):
    """Test init command with zsh shell specified."""
    result = runner.invoke(cli, ["init", "--shell", "zsh"])

    assert result.exit_code == 0
    output = result.output

    assert "# Generated for zsh" in output
    assert "el() {" in output
    assert "eul() {" in output


def test_init_auto_detect_bash(runner, monkeypatch):
    """Test init command auto-detects bash from SHELL env var."""
    monkeypatch.setenv("SHELL", "/usr/bin/bash")

    result = runner.invoke(cli, ["init", "--shell", "auto"])

    assert result.exit_code == 0
    assert "# Generated for bash" in result.output


def test_init_auto_detect_zsh(runner, monkeypatch):
    """Test init command auto-detects zsh from SHELL env var."""
    monkeypatch.setenv("SHELL", "/bin/zsh")

    result = runner.invoke(cli, ["init", "--shell", "auto"])

    assert result.exit_code == 0
    assert "# Generated for zsh" in result.output


def test_init_auto_detect_unknown_defaults_bash(runner, monkeypatch):
    """Test init command defaults to bash when shell cannot be detected."""
    # monkeypatch.setenv safely overrides or sets the variable
    # without clearing the rest of os.environ
    monkeypatch.setenv("SHELL", "/bin/fish")

    result = runner.invoke(cli, ["init", "--shell", "auto"])

    assert result.exit_code == 0
    assert "# Generated for bash" in result.output


def test_init_output_structure(runner):
    """Test that init output has proper structure."""
    result = runner.invoke(cli, ["init"])

    assert result.exit_code == 0
    lines = result.output.split("\n")

    # Should have comments, empty lines, and function definitions
    assert any(line.startswith("#") for line in lines)
    assert any(line == "" for line in lines)
    assert any("{" in line for line in lines)
    assert any("}" in line for line in lines)


def test_init_functions_pass_arguments(runner):
    """Test that generated functions pass through arguments."""
    result = runner.invoke(cli, ["init"])

    assert result.exit_code == 0
    output = result.output

    # Both functions should pass arguments with "$@"
    assert '"$@"' in output
    assert output.count('"$@"') == 2  # Once for load, once for unload


def test_init_uses_temp_files(runner):
    """Test that generated functions use temporary files for better compatibility."""
    result = runner.invoke(cli, ["init"])

    assert result.exit_code == 0
    output = result.output

    # Check for temp file usage pattern
    assert "local tmp_script" in output
    assert "mktemp" in output
    assert 'source "$tmp_script"' in output
    assert 'rm -f "$tmp_script"' in output

    # Should have two temp file blocks (load and unload)
    assert output.count("local tmp_script") == 2
    assert output.count("mktemp") == 2
    assert output.count('rm -f "$tmp_script"') == 2


def test_init_includes_error_handling(runner):
    """Test that generated functions include error handling."""
    result = runner.invoke(cli, ["init"])

    assert result.exit_code == 0
    output = result.output

    # Check for if-then-else error handling
    assert "if envlit load" in output
    assert "if envlit unload" in output
    assert "else" in output
    assert "Error: Failed to generate" in output
