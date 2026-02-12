"""
Configuration parsing and management.
Handles YAML config loading with inheritance support.
"""

from pathlib import Path
from typing import Any

import yaml


def load_config(config_path: str) -> dict[str, Any]:
    """
    Load a YAML configuration file.

    Args:
        config_path: Path to the YAML configuration file.

    Returns:
        Parsed configuration dictionary.

    Raises:
        FileNotFoundError: If the config file doesn't exist.
        yaml.YAMLError: If the YAML is invalid.
    """
    config_file = Path(config_path)
    if not config_file.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_file) as f:
        config = yaml.safe_load(f)

    # Handle empty file
    if config is None:
        config = {}

    # Normalize config structure
    if "env" not in config:
        config["env"] = {}
    if "flags" not in config:
        config["flags"] = {}
    if "hooks" not in config:
        config["hooks"] = {}

    # Handle inheritance
    if "extends" in config:
        parent_path = config.pop("extends")
        # Resolve relative paths
        if not Path(parent_path).is_absolute():
            parent_path = config_file.parent / parent_path
        parent_config = load_config(str(parent_path))
        config = _merge_configs(parent_config, config)

    return config


def resolve_inheritance(config: dict[str, Any], config_dir: Path) -> dict[str, Any]:
    """
    Resolve inheritance in a configuration.

    Args:
        config: Configuration dictionary.
        config_dir: Directory containing the config file (for resolving relative paths).

    Returns:
        Configuration with inheritance resolved.
    """
    if "extends" not in config:
        return config

    parent_path = config.pop("extends")
    # Resolve relative paths
    if not Path(parent_path).is_absolute():
        parent_path = config_dir / parent_path

    parent_config = load_config(str(parent_path))
    return _merge_configs(parent_config, config)


def _merge_configs(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:  # noqa: C901
    """
    Merge two configurations with override taking precedence.

    Special handling:
    - env: Shallow merge (override wins)
    - flags: Shallow merge (override wins)
    - hooks: Deep merge (lists are concatenated)

    Args:
        base: Base configuration.
        override: Override configuration.

    Returns:
        Merged configuration.
    """
    result = base.copy()

    # Merge env section (shallow merge, override wins)
    if "env" in override:
        if "env" not in result:
            result["env"] = {}
        result["env"].update(override["env"])

    # Merge flags section (shallow merge, override wins)
    if "flags" in override:
        if "flags" not in result:
            result["flags"] = {}
        result["flags"].update(override["flags"])

    # Merge hooks section (deep merge, lists concatenated)
    if "hooks" in override:
        if "hooks" not in result:
            result["hooks"] = {}
        for hook_type in override["hooks"]:
            if hook_type not in result["hooks"]:
                result["hooks"][hook_type] = []
            # Concatenate hook lists
            result["hooks"][hook_type] = result["hooks"][hook_type] + override["hooks"][hook_type]

    # Copy over any other keys
    for key in override:
        if key not in ["env", "flags", "hooks"]:
            result[key] = override[key]

    return result
