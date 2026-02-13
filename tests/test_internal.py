"""
Tests for internal tracking functionality.
The envlit-internal-track command is a hidden CLI command used by generated scripts.
"""

import json
import os

from envlit.internal import track_begin, track_end, track_restore


class TestInternalTracking:
    """Test internal state tracking commands."""

    def test_track_begin_captures_snapshot(self, monkeypatch):
        """Test that track_begin captures the current environment state."""
        # Set up environment
        monkeypatch.setenv("TEST_VAR", "original_value")
        monkeypatch.setenv("ANOTHER_VAR", "another_original")

        # Call track_begin
        snapshot_json = track_begin()
        snapshot = json.loads(snapshot_json)

        # Verify snapshot contains current environment
        assert snapshot["TEST_VAR"] == "original_value"
        assert snapshot["ANOTHER_VAR"] == "another_original"

    def test_track_end_detects_new_variable(self, monkeypatch):
        """Test track_end detecting a newly set variable."""
        # Clear any existing state
        from envlit.constants import SNAPSHOT_VAR_NAME, get_state_var_name

        state_var = get_state_var_name()

        for key in list(os.environ.keys()):
            if key.startswith("__ENVLIT_STATE"):
                monkeypatch.delenv(key, raising=False)

        # Set snapshot A in environment (empty snapshot)
        snapshot_a = {}
        monkeypatch.setenv(SNAPSHOT_VAR_NAME, json.dumps(snapshot_a))

        # Set a new variable
        monkeypatch.setenv("NEW_VAR", "new_value")

        # Call track_end
        result = track_end()

        # Should return shell commands to update state
        assert f"export {state_var}" in result

        # Parse the state
        state_json = result.split(f"export {state_var}='")[1].split("'")[0]
        state = json.loads(state_json)

        # NEW_VAR should be tracked with original=None (unset), current=new_value
        assert "NEW_VAR" in state
        assert state["NEW_VAR"]["original"] is None
        assert state["NEW_VAR"]["current"] == "new_value"

    def test_track_end_consecutive_load(self, monkeypatch):
        """Test track_end with consecutive loads (normal flow)."""
        # Setup: Variable was tracked before
        from envlit.constants import SNAPSHOT_VAR_NAME, get_state_var_name

        state_var = get_state_var_name()

        existing_state = {"MY_VAR": {"original": "first_value", "current": "second_value"}}
        monkeypatch.setenv(state_var, json.dumps(existing_state))

        # Snapshot A: variable has value from previous load
        snapshot_a = {"MY_VAR": "second_value"}
        monkeypatch.setenv(SNAPSHOT_VAR_NAME, json.dumps(snapshot_a))

        # User changes variable during load (simulated)
        monkeypatch.setenv("MY_VAR", "third_value")

        # Call track_end
        result = track_end()

        # Parse updated state
        state_json = result.split(f"export {state_var}='")[1].split("'")[0]
        state = json.loads(state_json)

        # Should keep original="first_value", update current="third_value"
        assert state["MY_VAR"]["original"] == "first_value"
        assert state["MY_VAR"]["current"] == "third_value"

    def test_track_end_manual_interference(self, monkeypatch):
        """Test track_end detecting manual user changes."""
        # Setup: Variable was tracked
        from envlit.constants import SNAPSHOT_VAR_NAME, get_state_var_name

        state_var = get_state_var_name()

        existing_state = {"MY_VAR": {"original": "first_value", "current": "second_value"}}
        monkeypatch.setenv(state_var, json.dumps(existing_state))

        # Snapshot A: User manually changed it!
        snapshot_a = {"MY_VAR": "manual_value"}  # Different from "second_value"
        monkeypatch.setenv(SNAPSHOT_VAR_NAME, json.dumps(snapshot_a))

        # During load, envlit sets it to a new value
        monkeypatch.setenv("MY_VAR", "third_value")

        # Call track_end
        result = track_end()

        # Parse updated state
        state_json = result.split(f"export {state_var}='")[1].split("'")[0]
        state = json.loads(state_json)

        # Manual interference: original should update to "manual_value"
        assert state["MY_VAR"]["original"] == "manual_value"
        assert state["MY_VAR"]["current"] == "third_value"

    def test_track_restore_simple(self, monkeypatch):
        """Test restoring variables to original values."""
        # Setup state with tracked variables
        from envlit.constants import get_state_var_name

        state_var = get_state_var_name()

        state = {
            "VAR1": {"original": "original1", "current": "modified1"},
            "VAR2": {"original": None, "current": "was_set"},  # Should unset
            "VAR3": {"original": "", "current": "was_empty"},  # Should set to empty
        }
        monkeypatch.setenv(state_var, json.dumps(state))

        # Current environment
        monkeypatch.setenv("VAR1", "modified1")
        monkeypatch.setenv("VAR2", "was_set")
        monkeypatch.setenv("VAR3", "was_empty")

        # Call restore
        result = track_restore()

        # Should generate commands to restore
        assert "export VAR1=original1" in result
        assert "unset VAR2" in result
        assert "export VAR3=''" in result
        assert f"unset {state_var}" in result  # Clear state after restore

    def test_track_restore_no_state(self, monkeypatch):
        """Test restore when no state exists."""
        # Clear all state variables
        for key in list(os.environ.keys()):
            if key.startswith("__ENVLIT_STATE"):
                monkeypatch.delenv(key, raising=False)

        # Call restore
        result = track_restore()

        # Should return warning message
        assert "No envlit state" in result

    def test_track_restore_with_manual_changes(self, monkeypatch):
        """Test restore when user manually changed variables after load."""
        # Setup state with tracked variables
        from envlit.constants import get_state_var_name

        state_var = get_state_var_name()

        # State shows: DEBUG was originally unset, envlit set it to "true"
        state = {
            "DEBUG": {"original": None, "current": "true"},
            "API_URL": {"original": "http://old.com", "current": "http://new.com"},
        }
        monkeypatch.setenv(state_var, json.dumps(state))

        # Current environment: User manually changed DEBUG to "false" and kept API_URL
        monkeypatch.setenv("DEBUG", "false")  # Manual change!
        monkeypatch.setenv("API_URL", "http://new.com")  # No change

        # Call restore
        result = track_restore()

        # DEBUG: User changed from "true" to "false", should restore to "false" (preserve manual change)
        assert "export DEBUG=false" in result

        # API_URL: No manual change, should restore to original "http://old.com"
        assert "export API_URL=http://old.com" in result

        # Should clear state
        assert f"unset {state_var}" in result

    def test_track_restore_manual_unset(self, monkeypatch):
        """Test restore when user manually unset a variable after load."""
        # Setup state
        from envlit.constants import get_state_var_name

        state_var = get_state_var_name()

        # State shows: TEMP_VAR was originally "old", envlit set it to "new"
        state = {
            "TEMP_VAR": {"original": "old", "current": "new"},
        }
        monkeypatch.setenv(state_var, json.dumps(state))

        # Current environment: User manually unset TEMP_VAR
        # (TEMP_VAR is not in environment)

        # Call restore
        result = track_restore()

        # User unset it (None != "new"), should restore to None (unset)
        assert "unset TEMP_VAR" in result

    def test_track_restore_manual_set_new_var(self, monkeypatch):
        """Test restore when user manually set a new variable that wasn't tracked."""
        # Setup state with one tracked variable
        from envlit.constants import get_state_var_name

        state_var = get_state_var_name()

        state = {
            "TRACKED_VAR": {"original": "old", "current": "new"},
        }
        monkeypatch.setenv(state_var, json.dumps(state))

        # Current environment
        monkeypatch.setenv("TRACKED_VAR", "new")
        monkeypatch.setenv("USER_VAR", "user_value")  # User added this manually

        # Call restore
        result = track_restore()

        # TRACKED_VAR should be restored to "old"
        assert "export TRACKED_VAR=old" in result

        # USER_VAR is not tracked, so it won't be in the restore commands
        # (it will remain in the environment)
        assert "USER_VAR" not in result

    def test_directory_specific_state_var(self, tmp_path):
        """Test that state variable name is directory-specific."""
        from envlit.constants import get_state_var_name

        # Save original directory
        original_dir = os.getcwd()

        try:
            # Change to tmp directory
            os.chdir(str(tmp_path))
            state_var_1 = get_state_var_name()

            # Change to different directory
            sub_dir = tmp_path / "subdir"
            sub_dir.mkdir()
            os.chdir(str(sub_dir))
            state_var_2 = get_state_var_name()

            # Should be different
            assert state_var_1 != state_var_2
            assert state_var_1.startswith("__ENVLIT_STATE_")
            assert state_var_2.startswith("__ENVLIT_STATE_")
        finally:
            # Restore original directory
            os.chdir(original_dir)
