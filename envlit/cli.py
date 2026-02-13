"""
Command-line interface for envlit.
Provides shell script generation commands.
"""

import os
import shutil
import sys
from pathlib import Path

import click

from envlit.__about__ import __version__
from envlit.config import load_config
from envlit.constants import get_hash_suffix
from envlit.script_generator import generate_load_script, generate_unload_script


def find_config_file(profile: str | None = None, search_dir: Path | None = None) -> Path | None:
    """
    Find the configuration file for a given profile.

    Search order:
    1. If profile is specified:
       - .envlit/<profile>.yaml
       - .envlit/<profile>.yml
    2. If no profile specified:
       - .envlit/default.yaml
       - .envlit/default.yml

    Args:
        profile: Optional profile name (e.g., "dev", "prod")
        search_dir: Directory to search in (defaults to current directory)

    Returns:
        Path to config file if found, None otherwise
    """
    if search_dir is None:
        search_dir = Path.cwd()

    envlit_dir = search_dir / ".envlit"
    if not envlit_dir.is_dir():
        return None

    # Determine profile name
    profile_name = profile or "default"

    # Try .yaml first, then .yml
    for ext in [".yaml", ".yml"]:
        config_path = envlit_dir / f"{profile_name}{ext}"
        if config_path.is_file():
            return config_path

    return None


@click.group(context_settings={"help_option_names": ["-h", "--help"]})
@click.version_option(version=__version__, prog_name="envlit")
def cli():
    """envlit: Environment Orchestration Engine"""
    pass


class DynamicFlagCommand(click.Command):
    """
    Custom Click command that dynamically adds flag options based on config file.

    This allows flags like --cuda, --backend to be recognized from the config.
    """

    def parse_args(self, ctx: click.Context, args: list):
        """Override parse_args to add dynamic options before argument parsing."""
        # Quick scan for profile (positional arg) and --config/-c values
        profile = None
        config_path_str = None

        i = 0
        while i < len(args):
            if args[i] in ["--config", "-c"] and i + 1 < len(args):
                config_path_str = args[i + 1]
                i += 2
            elif not args[i].startswith("-"):
                # First non-option argument is the profile
                if profile is None:
                    profile = args[i]
                i += 1
            else:
                i += 1

        # Find config file
        config_path = Path(config_path_str) if config_path_str else find_config_file(profile)

        # Load config and add dynamic flag options
        if config_path and config_path.is_file():
            try:
                config_dict = load_config(str(config_path))

                if "flags" in config_dict:
                    for flag_name, flag_config in config_dict["flags"].items():
                        # Check if already exists
                        if any(p.name == flag_name for p in self.params):
                            continue

                        # Get flag aliases
                        flag_aliases = flag_config.get("flag", [f"--{flag_name}"])
                        default_value = flag_config.get("default", None)
                        target = flag_config.get("target", flag_name.upper())

                        # Add option to command
                        option = click.Option(
                            param_decls=flag_aliases,
                            default=default_value,
                            help=f"Set {target} (default: {default_value})",
                        )
                        self.params.append(option)
            except Exception as e:
                click.echo(f"Error loading config for dynamic flags: {e}", err=True)
                sys.exit(1)

        return super().parse_args(ctx, args)


@cli.command(cls=DynamicFlagCommand)
@click.argument("profile", required=False)
@click.option("--config", "-c", type=click.Path(exists=True), help="Path to config file")
def load(profile: str | None, config: str | None, **kwargs):  # noqa: C901
    """
    Generate shell script to load environment configuration.

    For daily use with aliases (recommended):
        el                    # Load default profile
        el dev --cuda 1       # Load dev profile with CUDA device 1

    Direct usage (after running 'source <(envlit init)'):
        source <(envlit load)
        source <(envlit load dev --cuda 1)
        source <(envlit load --config path/to/config.yaml)

    Dynamic flags from the config file are automatically added as options.
    """
    try:
        # Find config file
        config_path: Path
        if config:
            config_path = Path(config)
        else:
            found_path = find_config_file(profile)
            if not found_path:
                profile_msg = f" for profile '{profile}'" if profile else ""
                click.echo(f"Error: No config file found{profile_msg}", err=True)
                click.echo("Expected: .envlit/default.yaml or .envlit/<profile>.yaml", err=True)
                sys.exit(1)
            config_path = found_path

        # Load configuration
        try:
            config_dict = load_config(str(config_path))
        except FileNotFoundError:
            click.echo(f"Error: Config file not found: {config_path}", err=True)
            sys.exit(1)
        except Exception as e:
            click.echo(f"Error parsing config file '{config_path}':", err=True)
            click.echo(f"  {type(e).__name__}: {e}", err=True)
            sys.exit(1)

        # Validate config structure
        if not isinstance(config_dict, dict):
            click.echo(f"Error: Config file '{config_path}' must contain a YAML dictionary", err=True)
            sys.exit(1)

        # Extract flag values from kwargs (dynamic flags)
        flag_values = {}
        if "flags" in config_dict:
            for flag_name in config_dict["flags"]:
                if flag_name in kwargs and kwargs[flag_name] is not None:
                    flag_values[flag_name] = kwargs[flag_name]

        # Generate shell script
        try:
            script = generate_load_script(config_dict, flag_values)
            click.echo(script)
        except KeyError as e:
            click.echo(f"Error: Missing required key in config: {e}", err=True)
            sys.exit(1)
        except Exception as e:
            click.echo("Error generating load script:", err=True)
            click.echo(f"  {type(e).__name__}: {e}", err=True)
            sys.exit(1)

    except Exception as e:
        click.echo(f"Unexpected error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option("--profile", "-p", help="Profile name (e.g., dev, prod)")
@click.option("--config", "-c", type=click.Path(exists=True), help="Path to config file")
def unload(profile: str | None, config: str | None):
    """
    Generate shell script to unload environment configuration.

    For daily use with aliases (recommended):
        eul                   # Unload current environment

    Direct usage:
        source <(envlit unload)
    """
    try:
        # Find config file (needed for hooks)
        config_path: Path | None
        if config:
            config_path = Path(config)
        else:
            config_path = find_config_file(profile)
            if not config_path:
                # If no config found, still try to restore from state
                click.echo(generate_unload_script({}))
                return

        # Load configuration for hooks
        config_dict = load_config(str(config_path))

        # Generate unload script
        script = generate_unload_script(config_dict)
        click.echo(script)

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option(
    "--shell",
    type=click.Choice(["bash", "zsh", "auto"]),
    default="auto",
    help="Target shell (auto-detect if not specified)",
)
@click.option("--alias-load", default="el", help="Alias for 'envlit load' (default: el)")
@click.option("--alias-unload", default="eul", help="Alias for 'envlit unload' (default: eul)")
def init(shell: str, alias_load: str, alias_unload: str):
    """
    Generate shell initialization code for envlit.

    Add this to your .bashrc or .zshrc (recommended):
        zshrc: source <(envlit init --shell zsh)
        bashrc: eval "$(envlit init --shell bash)"

    With custom aliases:
        source <(envlit init --alias-load myload --alias-unload myunload)

    The generated code creates shell functions that wrap envlit commands.
    """

    # Auto-detect shell if needed
    if shell == "auto":
        shell_env = os.environ.get("SHELL", "")
        if "zsh" in shell_env:
            shell = "zsh"
        elif "bash" in shell_env:
            shell = "bash"
        else:
            # Default to bash if can't detect
            shell = "bash"

    # Generate shell initialization code
    lines = [
        "# envlit shell integration",
        f"# Generated for {shell}",
        "",
    ]

    # Function for load
    lines.extend([
        f"{alias_load}() {{",
        "    local tmp_script",
        f'    tmp_script=$(mktemp "${{TMPDIR:-/tmp}}/envlit.{get_hash_suffix()}")',
        "",
        '    if envlit load "$@" > "$tmp_script"; then',
        '        source "$tmp_script"',
        "    else",
        '        echo "Error: Failed to generate envlit environment."',
        "    fi",
        "",
        '    rm -f "$tmp_script"',
        "}",
        "",
    ])

    # Function for unload
    lines.extend([
        f"{alias_unload}() {{",
        "    local tmp_script",
        f'    tmp_script=$(mktemp "${{TMPDIR:-/tmp}}/envlit.{get_hash_suffix()}")',
        "",
        '    if envlit unload "$@" > "$tmp_script"; then',
        '        source "$tmp_script"',
        "    else",
        '        echo "Error: Failed to generate envlit unload script."',
        "    fi",
        "",
        '    rm -f "$tmp_script"',
        "}",
        "",
    ])

    click.echo("\n".join(lines))


@cli.command()
@click.option(
    "--shell",
    type=click.Choice(["bash", "zsh", "auto"]),
    default="auto",
    help="Target shell type",
)
def doctor(shell: str):
    """
    Check envlit installation and configuration.

    Verifies that envlit is properly set up in your shell.
    """

    click.echo("🔍 envlit Doctor - Checking Installation\n")

    # Check if envlit command is available
    envlit_path = shutil.which("envlit")
    if envlit_path:
        click.echo(f"✓ envlit command found: {envlit_path}")
    else:
        click.echo("✗ envlit command not found in PATH")
        return

    # Check shell type
    if shell == "auto":
        shell_env = os.environ.get("SHELL", "unknown")
        click.echo(f"✓ Shell: {shell_env}")
    else:
        click.echo(f"✓ Shell: {shell}")

    # Check for config directory
    envlit_dir = Path.cwd() / ".envlit"
    if envlit_dir.is_dir():
        click.echo(f"✓ Config directory found: {envlit_dir}")

        # List config files
        configs = list(envlit_dir.glob("*.yaml")) + list(envlit_dir.glob("*.yml"))
        if configs:
            click.echo(f"  Found {len(configs)} config file(s):")
            for config in configs:
                click.echo(f"    - {config.name}")
        else:
            click.echo("  ⚠ No config files found (.yaml or .yml)")
    else:
        click.echo("⚠ No .envlit directory in current directory")

    click.echo("\n💡 To add envlit to your shell, add this to your .bashrc or .zshrc:")
    click.echo('    eval "$(envlit init)"')


# Separate CLI for internal tracking (not part of main envlit CLI)
@click.command()
@click.argument("phase", type=click.Choice(["begin", "end", "restore"]))
def internal_track_cli(phase: str):
    """
    Internal command for state tracking (not for direct user use).

    Called by generated shell scripts as 'envlit-internal-track <phase>'.
    """
    from envlit.internal import track_begin, track_end, track_restore

    try:
        if phase == "begin":
            # Output JSON snapshot to stdout for shell capture
            result = track_begin()
            click.echo(result)

        elif phase == "end":
            # Read snapshot from __ENVLIT_SNAPSHOT_A environment variable
            # and output shell commands to update state
            script = track_end()
            click.echo(script)

        elif phase == "restore":
            # Output shell commands to restore original state
            script = track_restore()
            click.echo(script)

    except Exception as e:
        click.echo(f"Error in internal tracking: {e}", err=True)
        sys.exit(1)
