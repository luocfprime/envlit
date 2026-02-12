import argparse
from pathlib import Path

import tomlkit
from packaging.version import Version


def parse_version(tag: str) -> str:
    """Parse version tag (e.g. git tag v0.1.0) and validate it using PEP 440."""
    return str(Version(tag))


def get_pyproject_version() -> str:
    """Retrieve the version from pyproject.toml."""
    pyproject_toml = Path("pyproject.toml")

    with pyproject_toml.open("rb") as f:
        pyproject = tomlkit.load(f)
    return pyproject.get("project", {}).get("version", "")


def check_version_match(tag: str) -> bool:
    """Check if the version in pyproject.toml and the provided tag match.

    Args:
        tag: Git tag (e.g., "v0.1.0").

    Returns: True if all versions match, False otherwise.

    """
    pyproject_version = get_pyproject_version()
    tag_version = parse_version(tag) if tag else None

    return pyproject_version == tag_version


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Check if version numbers match.")
    parser.add_argument(
        "--tag",
        type=str,
        required=True,
        help="The Git tag to compare, e.g., 'v0.1.0'.",
    )
    args = parser.parse_args()

    match = check_version_match(tag=args.tag)
    print(f"check version match: {match}")

    exit(0 if match else 1)
