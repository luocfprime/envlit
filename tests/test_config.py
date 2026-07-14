"""
Tests for configuration parsing and management.
"""

from pathlib import Path

import pytest
import yaml

import envlit.config as config_module
from envlit.config import load_config


class TestConfigParsing:
    """Test suite for configuration parsing."""

    def test_simple_config(self, tmp_path):
        """Test loading a simple config without inheritance."""
        config_file = tmp_path / "simple.yaml"
        config_file.write_text("""
env:
  PROJECT_MODE: "Debug"
  LOG_LEVEL: "INFO"
""")
        config = load_config(str(config_file))
        assert config["env"]["PROJECT_MODE"] == "Debug"
        assert config["env"]["LOG_LEVEL"] == "INFO"

    def test_config_with_flags(self, tmp_path):
        """Test config with smart flags."""
        config_file = tmp_path / "flags.yaml"
        config_file.write_text("""
flags:
  cuda:
    flag: ["--cuda", "-g"]
    default: "0"
    target: "CUDA_VISIBLE_DEVICES"
  backend:
    flag: "--backend"
    default: "torch"
    target: "ML_COMPUTE_BACKEND"
    map:
      torch: "PYTORCH_V2_OPTIMIZED"
      tf: "TENSORFLOW_LEGACY"
""")
        config = load_config(str(config_file))
        assert "cuda" in config["flags"]
        assert config["flags"]["cuda"]["default"] == "0"
        assert config["flags"]["backend"]["map"]["torch"] == "PYTORCH_V2_OPTIMIZED"

    def test_config_with_path_operations(self, tmp_path):
        """Test config with PATH operations."""
        config_file = tmp_path / "path.yaml"
        config_file.write_text("""
env:
  PATH:
    - op: remove
      value: "/usr/bin/bad-version"
    - op: prepend
      value: "./bin"
    - op: prepend
      value: "${HOME}/.local/bin"
""")
        config = load_config(str(config_file))
        assert isinstance(config["env"]["PATH"], list)
        assert config["env"]["PATH"][0]["op"] == "remove"
        assert config["env"]["PATH"][1]["op"] == "prepend"

    def test_config_with_single_operation(self, tmp_path):
        """Test config with a single PATH operation (not a list)."""
        config_file = tmp_path / "single_op.yaml"
        config_file.write_text("""
env:
  PYTHONPATH:
    op: prepend
    value: "./src"
""")
        config = load_config(str(config_file))
        # Single operation should be normalized to a list
        assert isinstance(config["env"]["PYTHONPATH"], dict)
        assert config["env"]["PYTHONPATH"]["op"] == "prepend"

    def test_config_with_hooks(self, tmp_path):
        """Test config with lifecycle hooks."""
        config_file = tmp_path / "hooks.yaml"
        config_file.write_text("""
hooks:
  pre_load:
    - name: "Check VPN"
      script: "echo 'Checking VPN...'"
  post_load:
    - name: "Notify"
      script: "echo 'Loaded!'"
  pre_unload:
    - name: "Cleanup"
      script: "echo 'Cleaning up...'"
  post_unload:
    - name: "Done"
      script: "echo 'Done!'"
""")
        config = load_config(str(config_file))
        assert "pre_load" in config["hooks"]
        assert len(config["hooks"]["pre_load"]) == 1
        assert config["hooks"]["pre_load"][0]["name"] == "Check VPN"

    def test_config_inheritance_simple(self, tmp_path):
        """Test simple config inheritance."""
        # Create base config
        base_file = tmp_path / "base.yaml"
        base_file.write_text("""
env:
  BASE_VAR: "from_base"
  SHARED_VAR: "base_value"
""")

        # Create derived config
        derived_file = tmp_path / "derived.yaml"
        derived_file.write_text(f"""
extends: {base_file}
env:
  DERIVED_VAR: "from_derived"
  SHARED_VAR: "derived_value"
""")

        config = load_config(str(derived_file))
        assert config["env"]["BASE_VAR"] == "from_base"
        assert config["env"]["DERIVED_VAR"] == "from_derived"
        # Derived should override base
        assert config["env"]["SHARED_VAR"] == "derived_value"

    def test_config_inheritance_relative_path(self, tmp_path):
        """Test config inheritance with relative path."""
        base_file = tmp_path / "base.yaml"
        base_file.write_text("""
env:
  BASE_VAR: "value"
""")

        derived_file = tmp_path / "derived.yaml"
        derived_file.write_text("""
extends: ./base.yaml
env:
  DERIVED_VAR: "value"
""")

        config = load_config(str(derived_file))
        assert config["env"]["BASE_VAR"] == "value"
        assert config["env"]["DERIVED_VAR"] == "value"

    def test_config_inheritance_flags_merge(self, tmp_path):
        """Test that flags from base and derived configs are merged."""
        base_file = tmp_path / "base.yaml"
        base_file.write_text("""
flags:
  cuda:
    flag: "--cuda"
    default: "0"
    target: "CUDA_VISIBLE_DEVICES"
""")

        derived_file = tmp_path / "derived.yaml"
        derived_file.write_text(f"""
extends: {base_file}
flags:
  backend:
    flag: "--backend"
    default: "torch"
    target: "ML_COMPUTE_BACKEND"
""")

        config = load_config(str(derived_file))
        assert "cuda" in config["flags"]
        assert "backend" in config["flags"]

    def test_config_inheritance_hooks_merge(self, tmp_path):
        """Test that hooks from base and derived configs are merged."""
        base_file = tmp_path / "base.yaml"
        base_file.write_text("""
hooks:
  pre_load:
    - name: "Base Hook"
      script: "echo 'base'"
""")

        derived_file = tmp_path / "derived.yaml"
        derived_file.write_text(f"""
extends: {base_file}
hooks:
  pre_load:
    - name: "Derived Hook"
      script: "echo 'derived'"
  post_load:
    - name: "Post Hook"
      script: "echo 'post'"
""")

        config = load_config(str(derived_file))
        # pre_load should have both hooks
        assert len(config["hooks"]["pre_load"]) == 2
        assert config["hooks"]["pre_load"][0]["name"] == "Base Hook"
        assert config["hooks"]["pre_load"][1]["name"] == "Derived Hook"
        # post_load should only have derived hook
        assert len(config["hooks"]["post_load"]) == 1

    def test_empty_config(self, tmp_path):
        """Test loading an empty config."""
        config_file = tmp_path / "empty.yaml"
        config_file.write_text("")
        config = load_config(str(config_file))
        assert config == {} or config is None or config == {"env": {}, "flags": {}, "hooks": {}}

    def test_nonexistent_config(self):
        """Test loading a nonexistent config file."""
        with pytest.raises(FileNotFoundError):
            load_config("/nonexistent/config.yaml")

    def test_invalid_yaml(self, tmp_path):
        """Test loading invalid YAML."""
        config_file = tmp_path / "invalid.yaml"
        config_file.write_text("invalid: yaml: content:")
        with pytest.raises(yaml.YAMLError):  # YAML parsing error
            load_config(str(config_file))

    def test_flags_section_emits_deprecation_warning(self, tmp_path):
        config_file = tmp_path / "flagged.yaml"
        config_file.write_text("""
flags:
  cuda:
    flag: "--cuda"
    default: "0"
    target: "CUDA_VISIBLE_DEVICES"
""")
        with pytest.warns(DeprecationWarning, match="flags.*deprecated"):
            load_config(str(config_file))

    def test_no_deprecation_warning_for_inline_flags(self, tmp_path):
        config_file = tmp_path / "inline.yaml"
        config_file.write_text("""
env:
  CUDA_VISIBLE_DEVICES:
    flag: ["--cuda", "-g"]
    default: "0"
""")
        import warnings

        with warnings.catch_warnings():
            warnings.simplefilter("error", DeprecationWarning)
            load_config(str(config_file))  # should not raise

    def test_empty_flags_section_no_warning(self, tmp_path):
        config_file = tmp_path / "empty_flags.yaml"
        config_file.write_text("""
env:
  MY_VAR: "value"
flags: {}
""")
        import warnings

        with warnings.catch_warnings():
            warnings.simplefilter("error", DeprecationWarning)
            load_config(str(config_file))  # should not raise


class TestDotenvLoading:
    def test_loads_single_dotenv_relative_to_config(self, tmp_path):
        (tmp_path / ".env").write_text("API_URL=https://example.test\nEMPTY=\n")
        config_file = tmp_path / "default.yaml"
        config_file.write_text('dotenv: "./.env"\n')

        config = load_config(str(config_file))

        assert config["env"] == {"API_URL": "https://example.test", "EMPTY": ""}

    def test_loads_absolute_dotenv_and_preserves_interpolation(self, tmp_path):
        dotenv_file = tmp_path / "shared.env"
        dotenv_file.write_text("BIN=${HOME}/bin\n")
        config_file = tmp_path / "default.yaml"
        config_file.write_text(f'dotenv: "{dotenv_file}"\n')

        config = load_config(str(config_file))

        assert config["env"]["BIN"] == "${HOME}/bin"

    def test_empty_dotenv_list_loads_nothing(self, tmp_path):
        config_file = tmp_path / "default.yaml"
        config_file.write_text("dotenv: []\nenv:\n  LOCAL: yes\n")

        config = load_config(str(config_file))

        assert config["env"] == {"LOCAL": True}

    @pytest.mark.parametrize(
        "dotenv_yaml",
        ["dotenv: 42\n", "dotenv:\n  nested: value\n", "dotenv:\n  - ./.env\n  - 42\n"],
    )
    def test_invalid_dotenv_shape_names_declaring_yaml(self, tmp_path, dotenv_yaml):
        config_file = tmp_path / "default.yaml"
        config_file.write_text(dotenv_yaml)

        with pytest.raises(ValueError, match=str(config_file)):
            load_config(str(config_file))

    @pytest.mark.parametrize("kind", ["missing", "directory"])
    def test_invalid_dotenv_path_names_yaml_and_resolved_path(self, tmp_path, kind):
        dotenv_path = tmp_path / kind
        if kind == "directory":
            dotenv_path.mkdir()
        config_file = tmp_path / "default.yaml"
        config_file.write_text(f'dotenv: "./{kind}"\n')

        with pytest.raises(ValueError) as exc_info:
            load_config(str(config_file))

        message = str(exc_info.value)
        assert str(config_file) in message
        assert str(dotenv_path) in message

    def test_unreadable_dotenv_names_yaml_and_resolved_path(self, tmp_path, monkeypatch):
        dotenv_file = (tmp_path / ".env").resolve()
        dotenv_file.write_text("KEY=value\n")
        config_file = tmp_path / "default.yaml"
        config_file.write_text('dotenv: "./.env"\n')
        original_open = Path.open

        def deny_target(path, *args, **kwargs):
            if path.resolve() == dotenv_file:
                raise PermissionError("denied")
            return original_open(path, *args, **kwargs)

        monkeypatch.setattr(Path, "open", deny_target)

        with pytest.raises(ValueError) as exc_info:
            load_config(str(config_file))

        message = str(exc_info.value)
        assert str(config_file) in message
        assert str(dotenv_file) in message

    def test_malformed_dotenv_fails_atomically_with_all_context(self, tmp_path):
        dotenv_file = tmp_path / ".env"
        dotenv_file.write_text("FIRST='unterminated\nGOOD=value\nSECOND=\"unterminated\n")
        config_file = tmp_path / "default.yaml"
        config_file.write_text('dotenv: "./.env"\n')

        with pytest.raises(ValueError) as exc_info:
            load_config(str(config_file))

        message = str(exc_info.value)
        assert str(config_file) in message
        assert str(dotenv_file) in message
        assert "1" in message
        assert "3" in message

    def test_key_without_equals_is_ignored_with_dotenv_warning(self, tmp_path):
        dotenv_file = tmp_path / ".env"
        dotenv_file.write_text("IGNORED\nKEPT=value\n")
        config_file = tmp_path / "default.yaml"
        config_file.write_text('dotenv: "./.env"\n')

        with pytest.warns(UserWarning, match="IGNORED") as warning_records:
            config = load_config(str(config_file))

        assert config["env"] == {"KEPT": "value"}
        assert warning_records[0].category is config_module.ConfigDotenvWarning

    def test_multiple_dotenv_files_and_yaml_override_in_order(self, tmp_path):
        first = (tmp_path / ".env").resolve()
        second = (tmp_path / ".env.local").resolve()
        first.write_text("SHARED=first-secret\nFIRST_ONLY=yes\n")
        second.write_text("SHARED=second-secret\nSECOND_ONLY=yes\n")
        config_file = (tmp_path / "default.yaml").resolve()
        config_file.write_text('dotenv:\n  - "./.env"\n  - "./.env.local"\nenv:\n  SHARED: yaml-secret\n')

        with pytest.warns(UserWarning) as warning_records:
            config = load_config(str(config_file))

        override_warnings = [w for w in warning_records if w.category is config_module.ConfigOverrideWarning]
        assert config["env"] == {
            "SHARED": "yaml-secret",
            "FIRST_ONLY": "yes",
            "SECOND_ONLY": "yes",
        }
        assert len(override_warnings) == 2
        warning_text = "\n".join(str(w.message) for w in override_warnings)
        assert "SHARED" in warning_text
        assert str(first) in warning_text
        assert str(second) in warning_text
        assert f"{config_file}:env" in warning_text
        assert "first-secret" not in warning_text
        assert "second-secret" not in warning_text
        assert "yaml-secret" not in warning_text

    def test_child_dotenv_and_yaml_override_parent_in_order(self, tmp_path):
        parent = (tmp_path / "base.yaml").resolve()
        parent.write_text("env:\n  SHARED: parent-secret\n")
        child_dotenv = (tmp_path / ".env.child").resolve()
        child_dotenv.write_text("SHARED=dotenv-secret\n")
        child = (tmp_path / "child.yaml").resolve()
        child.write_text('extends: "./base.yaml"\ndotenv: "./.env.child"\nenv:\n  SHARED: child-secret\n')

        with pytest.warns(UserWarning) as warning_records:
            config = load_config(str(child))

        override_warnings = [w for w in warning_records if w.category is config_module.ConfigOverrideWarning]
        assert config["env"]["SHARED"] == "child-secret"
        assert len(override_warnings) == 2
        warning_text = "\n".join(str(w.message) for w in override_warnings)
        assert f"{parent}:env" in warning_text
        assert str(child_dotenv) in warning_text
        assert f"{child}:env" in warning_text
        assert "secret" not in warning_text

    def test_duplicate_key_within_one_dotenv_uses_last_value_without_override_warning(self, tmp_path):
        dotenv_file = tmp_path / ".env"
        dotenv_file.write_text("DUP=first\nDUP=last\n")
        config_file = tmp_path / "default.yaml"
        config_file.write_text('dotenv: "./.env"\n')

        import warnings

        with warnings.catch_warnings(record=True) as warning_records:
            warnings.simplefilter("always")
            config = load_config(str(config_file))

        assert config["env"]["DUP"] == "last"
        assert not [w for w in warning_records if w.category is config_module.ConfigOverrideWarning]
