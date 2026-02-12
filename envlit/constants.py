"""
Constants used throughout envlit.
"""

import hashlib
import os

# Environment variable name for temporary snapshot storage
SNAPSHOT_VAR_NAME = "__ENVLIT_SNAPSHOT_A"


def get_state_var_name() -> str:
    """
    Get the state variable name with a hash suffix based on current directory.

    This prevents collisions when running envlit in different directories.
    Example: __ENVLIT_STATE_a1b2c3d4

    Returns:
        State variable name with directory hash suffix
    """
    cwd = os.getcwd()
    hash_suffix = hashlib.md5(cwd.encode(), usedforsecurity=False).hexdigest()[:8]
    return f"__ENVLIT_STATE_{hash_suffix}"
