"""
Internal tracking functionality for envlit.
These functions are called by the generated shell scripts via the envlit-internal-track CLI command.
"""

import json
import os
import shlex

from envlit.constants import SNAPSHOT_VAR_NAME, get_state_var_name
from envlit.state import StateManager


def track_begin() -> str:
    """
    Capture the current environment state (Snapshot A) and output as JSON.

    This is called at the beginning of a load script before any changes are made.
    The output is captured by the shell:
        __ENVLIT_SNAPSHOT_A=$(envlit-internal-track begin)

    Returns:
        JSON string of current environment variables.
    """
    # Return environment as JSON string
    snapshot = dict(os.environ)
    return json.dumps(snapshot)


def track_end() -> str:
    """
    Capture the ending state (Snapshot B), compare with Snapshot A,
    and update the __ENVLIT_STATE variable.
    """
    # Read Snapshot A (Start state)
    snapshot_a_json = os.environ.get(SNAPSHOT_VAR_NAME, "{}")
    try:
        snapshot_a = json.loads(snapshot_a_json)
    except json.JSONDecodeError:
        # Fallback if the snapshot is corrupted
        snapshot_a = {}

    # Read Snapshot B (Current state)
    snapshot_b = dict(os.environ)

    # Identify keys
    keys_a = set(snapshot_a.keys())
    keys_b = set(snapshot_b.keys())

    # Filter out the snapshot variable itself to avoid self-reference loops
    keys_a.discard(SNAPSHOT_VAR_NAME)
    keys_b.discard(SNAPSHOT_VAR_NAME)

    # 1. Variables added or removed (Symmetric Difference)
    changed_vars = {k: snapshot_b.get(k) for k in keys_a ^ keys_b}

    # 2. Variables present in both but with different values
    common_keys = keys_a & keys_b
    for k in common_keys:
        if snapshot_a[k] != snapshot_b[k]:
            changed_vars[k] = snapshot_b[k]

    # Apply Compare-and-Swap
    state_manager = StateManager()

    # We only need to update the state manager if there are changes
    if changed_vars:
        for var_name, target_val in changed_vars.items():
            # actual_val is what it was at the start (Snapshot A)
            actual_val = snapshot_a.get(var_name)
            state_manager.update_variable(var_name, actual_val, target_val)

    # Generate shell command
    state_var = get_state_var_name()
    updated_state = state_manager.get_state()
    state_json = json.dumps(updated_state)

    # Use shlex for safe quoting (handles single quotes, spaces, etc.)
    return f"export {state_var}={shlex.quote(state_json)}"


def track_restore() -> str:
    """
    Restore environment variables to their original values from __ENVLIT_STATE.
    """
    state_var = get_state_var_name()

    # Check if state exists in environment
    if state_var not in os.environ:
        return "# No envlit state found to restore"

    state_manager = StateManager()
    tracked_vars = state_manager.get_tracked_variables()

    if not tracked_vars:
        return f"unset {state_var}"

    commands = ["# Restoring environment to original state"]

    for var_name in tracked_vars:
        original = state_manager.get_original_value(var_name)

        if original is None:
            # Variable was originally unset, so we unset it now
            commands.append(f"unset {var_name}")
        else:
            # Variable had a value, restore it safely
            # shlex.quote ensures that $VAR, `cmd`, and spaces are treated as literals
            commands.append(f"export {var_name}={shlex.quote(original)}")

    # Clear the internal state variable last
    commands.append(f"unset {state_var}")

    return "\n".join(commands)
