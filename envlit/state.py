"""
State management for envlit.
Implements the Compare-and-Swap algorithm for tracking environment variable changes.
"""

import json
import os
from typing import Any

from envlit.constants import get_state_var_name


class StateManager:
    """Manages the state record for environment variables."""

    def __init__(self):
        """Initialize StateManager and load existing state."""
        self.state_var = get_state_var_name()
        self._state = self._load_state()

    def _load_state(self) -> dict[str, dict[str, Any]]:
        """
        Load the current state from __ENVLIT_STATE environment variable.

        Returns:
            Dictionary mapping variable names to their state records.
            Each record contains 'original' and 'current' keys.
            Returns empty dict if no state exists.
        """
        state_json = os.environ.get(self.state_var, "{}")
        try:
            return json.loads(state_json)
        except json.JSONDecodeError:
            return {}

    def get_state(self) -> dict[str, dict[str, Any]]:
        """Get the current state dictionary."""
        return self._state

    def update_variable(
        self,
        var_name: str,
        actual_val: str | None,
        target_val: str | None,
    ) -> None:
        """
        Update a variable using the Compare-and-Swap algorithm.

        Implements the decision matrix from the design spec:
        1. New Variable: Save actual_val as original, set target_val as current
        2. Consecutive Load: Keep existing original, update current to target_val
        3. Manual Interference: Update original to actual_val, set current to target_val

        Args:
            var_name: Name of the environment variable.
            actual_val: Current value in the environment (None if unset).
            target_val: Desired value to set (None to unset).
        """
        if var_name not in self._state:
            # Scenario 1: New Variable
            self._state[var_name] = {"original": actual_val, "current": target_val}
        elif actual_val == self._state[var_name]["current"]:
            # Scenario 2: Consecutive Load (no manual interference)
            # Keep original, update current
            self._state[var_name]["current"] = target_val
        else:
            # Scenario 3: Manual Interference detected
            # Update original to reflect user's manual change, set new current
            self._state[var_name]["original"] = actual_val
            self._state[var_name]["current"] = target_val

    def get_original_value(self, var_name: str) -> str | None:
        """Get the original value of a tracked variable."""
        if var_name in self._state:
            return self._state[var_name]["original"]
        return None

    def get_current_value(self, var_name: str) -> str | None:
        """Get the current value of a tracked variable."""
        if var_name in self._state:
            return self._state[var_name]["current"]
        return None

    def get_tracked_variables(self) -> list[str]:
        """Get list of all tracked variable names."""
        return list(self._state.keys())

    def get_env_dict(self, from_env: bool = False) -> dict[str, str]:
        """
        Get tracked variables as a dictionary.

        Args:
            from_env: If True, get values from os.environ; if False, get from state's 'current' values

        Returns:
            Dictionary mapping variable names to values
        """
        result = {}
        for var_name in self.get_tracked_variables():
            if from_env:
                value = os.environ.get(var_name)
                if value is not None:
                    result[var_name] = value
            else:
                value = self.get_current_value(var_name)
                if value is not None:
                    result[var_name] = value
        return result
