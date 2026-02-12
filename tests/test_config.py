"""
Tests for configuration parsing and management.
"""

import pytest
import yaml

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
