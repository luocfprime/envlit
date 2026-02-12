"""
Internal tracking functionality for envlit.
These functions are called by the generated shell scripts via the _envlit_internal_track CLI command.
"""

import json
import os

from envlit.constants import SNAPSHOT_VAR_NAME, get_state_var_name
from envlit.state import StateManager


def track_begin() -> str:
    """
    Capture the current environment state (Snapshot A) and output as JSON.

    This is called at the beginning of a load script before any changes are made.
    The output is meant to be captured by the shell: __ENVLIT_SNAPSHOT_A=$(envlit-internal-track begin)

    Returns:
        JSON string of current environment variables.
    """
    # Return environment as JSON string
    snapshot = dict(os.environ)
    return json.dumps(snapshot)


def track_end() -> str:
    """
    Capture the ending state (Snapshot B), compare with Snapshot A from environment,
    and update the __ENVLIT_STATE variable.

    This implements the "Compare-and-Swap" algorithm from the design spec.
    Reads snapshot A from the __ENVLIT_SNAPSHOT_A environment variable.

    Returns:
        Shell commands to export the updated __ENVLIT_STATE.
    """
    # Read Snapshot A from environment
    snapshot_a_json = os.environ.get(SNAPSHOT_VAR_NAME, "{}")
    snapshot_a = json.loads(snapshot_a_json)

    # Get current state (Snapshot B)
    snapshot_b = dict(os.environ)

    # Load existing state
    state_var = get_state_var_name()
    state_manager = StateManager()

    # Find all changed variables (comparing A to B)
    changed_vars = {}
    all_vars = set(snapshot_a.keys()) | set(snapshot_b.keys())

    for var_name in all_vars:
        # Skip the temporary snapshot variable itself
        if var_name == SNAPSHOT_VAR_NAME:
            continue

        val_a = snapshot_a.get(var_name)
        val_b = snapshot_b.get(var_name)

        if val_a != val_b:
            changed_vars[var_name] = val_b

    # Apply the Compare-and-Swap algorithm for each changed variable
    for var_name, target_val in changed_vars.items():
        actual_val = snapshot_a.get(var_name)  # Value at beginning
        state_manager.update_variable(var_name, actual_val, target_val)

    # Generate shell command to export the updated state
    updated_state = state_manager.get_state()
    state_json = json.dumps(updated_state)
    # Escape single quotes for shell
    state_json_escaped = state_json.replace("'", "'\\''")

    return f"export {state_var}='{state_json_escaped}'"


def track_restore() -> str:
    """
    Restore environment variables to their original values from __ENVLIT_STATE.

    This is called during unload to restore the environment to its pre-envlit state.

    Returns:
        Shell commands to restore variables and clear state.
    """
    state_var = get_state_var_name()
    state_manager = StateManager()

    # Check if state exists
    if not os.environ.get(state_var):
        return "# No envlit state found to restore"

    # Get all tracked variables
    state = state_manager.get_state()

    if not state:
        return f"unset {state_var}"

    # Generate restore commands
    commands = []
    commands.append("# Restoring environment to original state")

    for var_name in state_manager.get_tracked_variables():
        original = state_manager.get_original_value(var_name)

        if original is None:
            # Was unset originally, unset it again
            commands.append(f"unset {var_name}")
        else:
            # Restore original value
            # Escape for shell
            escaped = original.replace("\\", "\\\\").replace('"', '\\"')
            commands.append(f'export {var_name}="{escaped}"')

    # Clear the state
    commands.append(f"unset {state_var}")

    return "\n".join(commands)
