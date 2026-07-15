"""
Configuration parsing and management.
Handles YAML config loading with inheritance and dotenv support.
"""

import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml
from dotenv.parser import parse_stream


class ConfigOverrideWarning(UserWarning):
    """An environment value replaced one from an earlier config source."""


class ConfigDotenvWarning(UserWarning):
    """A non-fatal dotenv entry was ignored."""


class ConfigError(ValueError):
    """An envlit configuration cannot be resolved safely."""


@dataclass
class _ResolvedConfig:
    config: dict[str, Any]
    env_sources: dict[str, str]


def load_config(config_path: str) -> dict[str, Any]:
    """
    Load and resolve a YAML configuration file.

    Dotenv and inheritance layers are applied from lowest to highest priority:
    parent config, local dotenv files in list order, then local ``env`` values.

    Args:
        config_path: Path to the YAML configuration file.

    Returns:
        Parsed and resolved configuration dictionary.

    Raises:
        FileNotFoundError: If the YAML config file doesn't exist.
        ValueError: If the YAML or dotenv configuration has an invalid shape.
        yaml.YAMLError: If the YAML is invalid.
    """
    return _load_config(Path(config_path)).config


def _load_config(config_file: Path) -> _ResolvedConfig:  # noqa: C901
    if not config_file.exists():
        raise FileNotFoundError(f"Config file not found: {config_file}")

    with open(config_file) as stream:
        raw_config = yaml.safe_load(stream)

    if raw_config is None:
        raw_config = {}
    if not isinstance(raw_config, dict):
        raise ConfigError(f"Config file '{config_file}' must contain a YAML dictionary")

    config_file = config_file.resolve()
    local_env = raw_config.get("env", {})
    local_flags = raw_config.get("flags", {})
    local_hooks = raw_config.get("hooks", {})
    if not isinstance(local_env, dict):
        raise ConfigError(f"The 'env' section in '{config_file}' must be a mapping")
    if not isinstance(local_flags, dict):
        raise ConfigError(f"The 'flags' section in '{config_file}' must be a mapping")
    if not isinstance(local_hooks, dict):
        raise ConfigError(f"The 'hooks' section in '{config_file}' must be a mapping")

    if local_flags:
        warnings.warn(
            "The top-level 'flags:' section is deprecated. "
            "Define flags inline inside 'env:' entries using the 'flag:' key instead.",
            DeprecationWarning,
            stacklevel=2,
        )

    parent = _load_parent(raw_config.get("extends"), config_file)
    result = parent.config.copy()
    result["env"] = dict(parent.config.get("env", {}))
    result["flags"] = dict(parent.config.get("flags", {}))
    result["hooks"] = {name: list(items) for name, items in parent.config.get("hooks", {}).items()}
    env_sources = dict(parent.env_sources)

    for dotenv_path in _normalize_dotenv_paths(raw_config, config_file):
        values, source = _parse_dotenv_file(dotenv_path, config_file)
        _merge_env_layer(result["env"], env_sources, values, source)

    _merge_env_layer(result["env"], env_sources, local_env, f"{config_file}:env")
    result["flags"].update(local_flags)
    _merge_hooks(result["hooks"], local_hooks)

    for key, value in raw_config.items():
        if key not in {"extends", "dotenv", "env", "flags", "hooks"}:
            result[key] = value

    return _ResolvedConfig(config=result, env_sources=env_sources)


def _load_parent(extends: Any, config_file: Path) -> _ResolvedConfig:
    if extends is None:
        return _ResolvedConfig(config={"env": {}, "flags": {}, "hooks": {}}, env_sources={})
    if not isinstance(extends, str):
        raise ConfigError(f"The 'extends' value in '{config_file}' must be a path string")

    parent_path = Path(extends)
    if not parent_path.is_absolute():
        parent_path = config_file.parent / parent_path
    return _load_config(parent_path)


def _normalize_dotenv_paths(raw_config: dict[str, Any], config_file: Path) -> list[Path]:
    if "dotenv" not in raw_config:
        return []

    dotenv = raw_config["dotenv"]
    if isinstance(dotenv, str):
        paths = [dotenv]
    elif isinstance(dotenv, list) and all(isinstance(item, str) for item in dotenv):
        paths = dotenv
    else:
        raise ConfigError(f"The 'dotenv' value in '{config_file}' must be a path string or list of path strings")

    resolved_paths = []
    for path_value in paths:
        path = Path(path_value)
        if not path.is_absolute():
            path = config_file.parent / path
        resolved_paths.append(path.resolve())
    return resolved_paths


def _parse_dotenv_file(dotenv_file: Path, config_file: Path) -> tuple[dict[str, str], str]:
    if not dotenv_file.is_file():
        raise ConfigError(f"Dotenv file '{dotenv_file}' declared by '{config_file}' does not exist or is not a file")

    try:
        with dotenv_file.open(encoding="utf-8") as stream:
            bindings = list(parse_stream(stream))
    except (OSError, UnicodeError) as error:
        raise ConfigError(f"Could not read dotenv file '{dotenv_file}' declared by '{config_file}': {error}") from error

    error_lines = [binding.original.line for binding in bindings if binding.error]
    if error_lines:
        lines = ", ".join(str(line) for line in error_lines)
        raise ConfigError(
            f"Could not parse dotenv file '{dotenv_file}' declared by '{config_file}' at starting line(s): {lines}"
        )

    values: dict[str, str] = {}
    for binding in bindings:
        if binding.key is None:
            continue
        if binding.value is None:
            warnings.warn(
                f"Ignoring dotenv key '{binding.key}' without '=' from '{dotenv_file}'",
                ConfigDotenvWarning,
                stacklevel=3,
            )
            continue
        # Collapse repeated declarations within one file without a cross-source warning.
        values[binding.key] = binding.value

    return values, str(dotenv_file)


def _merge_env_layer(
    destination: dict[str, Any],
    sources: dict[str, str],
    incoming: dict[str, Any],
    source: str,
) -> None:
    for name, value in incoming.items():
        if name in destination:
            warnings.warn(
                f"{name} from '{source}' overrides value from '{sources[name]}'",
                ConfigOverrideWarning,
                stacklevel=3,
            )
        destination[name] = value
        sources[name] = source


def _merge_hooks(destination: dict[str, list[Any]], incoming: dict[str, Any]) -> None:
    for hook_type, hooks in incoming.items():
        if hook_type not in destination:
            destination[hook_type] = []
        destination[hook_type].extend(hooks)


def _merge_configs(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """Merge normalized configs without source tracking (backward-compatible helper)."""
    result = base.copy()
    result["env"] = dict(base.get("env", {}))
    result["env"].update(override.get("env", {}))
    result["flags"] = dict(base.get("flags", {}))
    result["flags"].update(override.get("flags", {}))
    result["hooks"] = {name: list(items) for name, items in base.get("hooks", {}).items()}
    _merge_hooks(result["hooks"], override.get("hooks", {}))
    for key, value in override.items():
        if key not in {"env", "flags", "hooks"}:
            result[key] = value
    return result
