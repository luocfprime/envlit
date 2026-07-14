"""
Tests for CLI commands: find_config_file, load error paths, doctor.
"""

import os
import subprocess

import pytest
from click.testing import CliRunner

from envlit.cli import cli, find_config_file
from envlit.script_generator import generate_unload_script

# ---------------------------------------------------------------------------
# find_config_file
# ---------------------------------------------------------------------------


class TestFindConfigFile:
    def test_no_envlit_dir(self, tmp_path):
        assert find_config_file(search_dir=tmp_path) is None

    def test_envlit_dir_exists_but_empty(self, tmp_path):
        (tmp_path / ".envlit").mkdir()
        assert find_config_file(search_dir=tmp_path) is None

    def test_default_profile_yaml(self, tmp_path):
        d = tmp_path / ".envlit"
        d.mkdir()
        f = d / "default.yaml"
        f.write_text("env: {}")
        assert find_config_file(search_dir=tmp_path) == f

    def test_default_profile_yml_fallback(self, tmp_path):
        d = tmp_path / ".envlit"
        d.mkdir()
        f = d / "default.yml"
        f.write_text("env: {}")
        assert find_config_file(search_dir=tmp_path) == f

    def test_yaml_preferred_over_yml(self, tmp_path):
        d = tmp_path / ".envlit"
        d.mkdir()
        yaml_f = d / "default.yaml"
        yml_f = d / "default.yml"
        yaml_f.write_text("env: {}")
        yml_f.write_text("env: {}")
        assert find_config_file(search_dir=tmp_path) == yaml_f

    def test_named_profile(self, tmp_path):
        d = tmp_path / ".envlit"
        d.mkdir()
        f = d / "dev.yaml"
        f.write_text("env: {}")
        assert find_config_file(profile="dev", search_dir=tmp_path) == f

    def test_named_profile_not_found(self, tmp_path):
        d = tmp_path / ".envlit"
        d.mkdir()
        (d / "default.yaml").write_text("env: {}")
        assert find_config_file(profile="prod", search_dir=tmp_path) is None

    def test_no_profile_falls_back_to_default(self, tmp_path):
        d = tmp_path / ".envlit"
        d.mkdir()
        f = d / "default.yaml"
        f.write_text("env: {}")
        assert find_config_file(profile=None, search_dir=tmp_path) == f


# ---------------------------------------------------------------------------
# load — error paths
# ---------------------------------------------------------------------------


class TestLoadErrors:
    @pytest.fixture
    def runner(self):
        return CliRunner()

    def test_no_config_file_found(self, runner, tmp_path):
        """load fails gracefully when no .envlit dir exists."""
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(cli, ["load"])
        assert result.exit_code != 0
        assert "No config file found" in result.output

    def test_no_config_for_profile(self, runner, tmp_path):
        """load fails with helpful message when named profile missing."""
        envlit_dir = tmp_path / ".envlit"
        envlit_dir.mkdir()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(cli, ["load", "nonexistent"])
        assert result.exit_code != 0
        assert "nonexistent" in result.output

    def test_invalid_yaml(self, runner, tmp_path):
        """load fails gracefully on malformed YAML."""
        bad = tmp_path / "bad.yaml"
        bad.write_text("env: {unclosed")
        result = runner.invoke(cli, ["load", "--config", str(bad)])
        assert result.exit_code != 0

    def test_config_not_a_dict(self, runner, tmp_path):
        """load fails when YAML root is not a mapping."""
        bad = tmp_path / "list.yaml"
        bad.write_text("- item1\n- item2\n")
        result = runner.invoke(cli, ["load", "--config", str(bad)])
        assert result.exit_code != 0
        # Error may surface from DynamicFlagCommand.parse_args or load() body
        assert result.output  # some error message is emitted

    def test_valid_config_succeeds(self, runner, tmp_path):
        """load succeeds and emits a sourceable script for a valid config."""
        cfg = tmp_path / "ok.yaml"
        cfg.write_text("env:\n  FOO:\n    op: set\n    value: bar\n")
        result = runner.invoke(cli, ["load", "--config", str(cfg)])
        assert result.exit_code == 0
        assert 'export FOO="bar"' in result.output


class TestDotenvCLI:
    @pytest.fixture
    def runner(self):
        return CliRunner()

    def test_override_warning_uses_stderr_and_stdout_remains_sourceable(self, runner, tmp_path):
        dotenv_file = tmp_path / ".env"
        dotenv_file.write_text("SHARED=dotenv-secret\n")
        config_file = tmp_path / "default.yaml"
        config_file.write_text('dotenv: "./.env"\nenv:\n  SHARED: yaml-secret\n')

        result = runner.invoke(cli, ["load", "--config", str(config_file)])

        assert result.exit_code == 0
        assert result.stdout.startswith("#!/bin/bash")
        assert 'export SHARED="yaml-secret"' in result.stdout
        assert "ConfigOverrideWarning" not in result.stdout
        assert "ConfigOverrideWarning" in result.stderr
        assert "SHARED" in result.stderr
        assert "dotenv-secret" not in result.stderr
        assert "yaml-secret" not in result.stderr

    @pytest.mark.parametrize("dotenv_content", [None, 'BROKEN="unterminated\n'])
    def test_missing_or_malformed_dotenv_emits_no_script(self, runner, tmp_path, dotenv_content):
        if dotenv_content is not None:
            (tmp_path / ".env").write_text(dotenv_content)
        config_file = tmp_path / "default.yaml"
        config_file.write_text('dotenv: "./.env"\n')

        result = runner.invoke(cli, ["load", "--config", str(config_file)])

        assert result.exit_code != 0
        assert "#!/bin/bash" not in result.stdout
        assert str(config_file.resolve()) in result.stderr
        assert str((tmp_path / ".env").resolve()) in result.stderr

    def test_invalid_dotenv_variable_emits_no_script(self, runner, tmp_path):
        (tmp_path / ".env").write_text("BAD-NAME=value\n")
        config_file = tmp_path / "default.yaml"
        config_file.write_text('dotenv: "./.env"\n')

        result = runner.invoke(cli, ["load", "--config", str(config_file)])

        assert result.exit_code != 0
        assert "#!/bin/bash" not in result.stdout
        assert "BAD-NAME" in result.stderr

    def test_dotenv_generated_script_loads_and_restores_environment(self, runner, tmp_path):
        (tmp_path / ".env").write_text("RESTORE_ME=loaded\nNEW_FROM_DOTENV=new\n")
        config_file = tmp_path / "default.yaml"
        config_file.write_text('dotenv: "./.env"\n')
        result = runner.invoke(cli, ["load", "--config", str(config_file)])
        assert result.exit_code == 0

        load_script = tmp_path / "load.sh"
        unload_script = tmp_path / "unload.sh"
        load_script.write_text(result.stdout)
        unload_script.write_text(generate_unload_script({}))
        environment = os.environ.copy()
        environment["RESTORE_ME"] = "before"
        environment.pop("NEW_FROM_DOTENV", None)

        completed = subprocess.run(  # noqa: S603 - fixed executable and generated local fixtures
            [
                "/bin/bash",
                "-c",
                'set -e; source "$1"; '
                'test "$RESTORE_ME" = loaded; test "$NEW_FROM_DOTENV" = new; '
                'source "$2"; test "$RESTORE_ME" = before; test -z "${NEW_FROM_DOTENV+x}"',
                "bash",
                str(load_script),
                str(unload_script),
            ],
            env=environment,
            capture_output=True,
            text=True,
            check=False,
        )

        assert completed.returncode == 0, completed.stderr


# ---------------------------------------------------------------------------
# doctor
# ---------------------------------------------------------------------------


class TestDoctor:
    @pytest.fixture
    def runner(self):
        return CliRunner()

    def test_doctor_runs(self, runner):
        result = runner.invoke(cli, ["doctor"])
        assert result.exit_code == 0

    def test_doctor_shows_shell_info(self, runner, monkeypatch):
        monkeypatch.setenv("SHELL", "/bin/zsh")
        result = runner.invoke(cli, ["doctor"])
        assert "/bin/zsh" in result.output

    def test_doctor_no_envlit_dir(self, runner, tmp_path):
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(cli, ["doctor"])
        assert result.exit_code == 0
        assert "No .envlit directory" in result.output

    def test_doctor_with_envlit_dir_and_configs(self, runner, tmp_path, monkeypatch):
        envlit_dir = tmp_path / ".envlit"
        envlit_dir.mkdir()
        (envlit_dir / "default.yaml").write_text("env: {}")
        (envlit_dir / "dev.yaml").write_text("env: {}")
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(cli, ["doctor"])
        assert result.exit_code == 0
        assert "2 config file" in result.output

    def test_doctor_suggests_init(self, runner):
        result = runner.invoke(cli, ["doctor"])
        assert result.exit_code == 0
        assert "envlit init" in result.output
