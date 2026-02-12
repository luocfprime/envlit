"""
Tests for state management functionality.
State management is core to envlit's Compare-and-Swap algorithm.
"""

import json
import os

from envlit.state import StateManager


class TestStateManagement:
    """Test the state management and Compare-and-Swap algorithm."""

    def test_new_variable_first_time_tracking(self, monkeypatch):
        """Test tracking a variable for the first time (Scenario 1)."""
        # Clear any existing state
        for key in list(os.environ.keys()):
            if key.startswith("__ENVLIT_STATE"):
                monkeypatch.delenv(key, raising=False)

        manager = StateManager()
        assert manager.get_state() == {}

        # First time setting CUDA_VISIBLE_DEVICES
        manager.update_variable("CUDA_VISIBLE_DEVICES", "0", "1")

        # Should record original=0, current=1
        assert manager.get_original_value("CUDA_VISIBLE_DEVICES") == "0"
        assert manager.get_current_value("CUDA_VISIBLE_DEVICES") == "1"

    def test_consecutive_loads_normal_flow(self, monkeypatch):
        """Test consecutive loads without manual interference (Scenario 2)."""
        # Setup: First load already happened
        initial_state = {"CUDA_VISIBLE_DEVICES": {"original": "0", "current": "1"}}
        from envlit.constants import get_state_var_name

        monkeypatch.setenv(get_state_var_name(), json.dumps(initial_state))

        manager = StateManager()

        # Second load: actual value (1) matches current (1)
        manager.update_variable("CUDA_VISIBLE_DEVICES", "1", "2")

        # Should keep original=0, update current=2
        assert manager.get_original_value("CUDA_VISIBLE_DEVICES") == "0"
        assert manager.get_current_value("CUDA_VISIBLE_DEVICES") == "2"

    def test_manual_interference_detection(self, monkeypatch):
        """Test detecting manual user changes (Scenario 3)."""
        # Setup: Variable was tracked
        initial_state = {"CUDA_VISIBLE_DEVICES": {"original": "0", "current": "1"}}
        from envlit.constants import get_state_var_name

        monkeypatch.setenv(get_state_var_name(), json.dumps(initial_state))

        manager = StateManager()

        # User manually changed it to "7" (actual != current)
        manager.update_variable("CUDA_VISIBLE_DEVICES", "7", "3")

        # Should update original=7, current=3
        assert manager.get_original_value("CUDA_VISIBLE_DEVICES") == "7"
        assert manager.get_current_value("CUDA_VISIBLE_DEVICES") == "3"

    def test_unset_vs_empty_string(self, monkeypatch):
        """Test distinction between unset (None) and empty ('')."""
        for key in list(os.environ.keys()):
            if key.startswith("__ENVLIT_STATE"):
                monkeypatch.delenv(key, raising=False)

        manager = StateManager()

        # Variable was unset (None), now setting it
        manager.update_variable("MY_VAR", None, "foo")
        assert manager.get_original_value("MY_VAR") is None
        assert manager.get_current_value("MY_VAR") == "foo"

        # Variable was empty string, now changing it
        manager.update_variable("ANOTHER_VAR", "", "bar")
        assert manager.get_original_value("ANOTHER_VAR") == ""
        assert manager.get_current_value("ANOTHER_VAR") == "bar"

    def test_get_tracked_variables(self, monkeypatch):
        """Test getting list of tracked variables."""
        initial_state = {
            "VAR1": {"original": "a", "current": "b"},
            "VAR2": {"original": None, "current": "c"},
        }
        from envlit.constants import get_state_var_name

        monkeypatch.setenv(get_state_var_name(), json.dumps(initial_state))

        manager = StateManager()
        tracked = manager.get_tracked_variables()

        assert set(tracked) == {"VAR1", "VAR2"}
