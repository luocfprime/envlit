# envlit

[![CI](https://github.com/luocfprime/envlit/actions/workflows/ci.yml/badge.svg)](https://github.com/luocfprime/envlit/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/luocfprime/envlit/branch/main/graph/badge.svg)](https://codecov.io/gh/luocfprime/envlit)
[![Python Versions](https://img.shields.io/pypi/pyversions/envlit)](https://pypi.org/project/envlit/)
[![PyPI](https://img.shields.io/pypi/v/envlit)](https://pypi.org/project/envlit/)

A minimal CLI tool to organize, load, and switch between your project's environment contexts.

## Installation

```bash
pip install envlit
```

## Quick Start

Initialize envlit in your shell (add to `.bashrc` or `.zshrc`):

```bash
eval "$(envlit init)"
```

Create a config file at `.envlit/default.yaml`:

```yaml
env:
  PROJECT_MODE: "Development"
  DEBUG: "true"
```

Load and unload environments:

```bash
el          # Load default profile
el dev      # Load dev profile
eul         # Unload environment
```

## Features

- **Smart state tracking** - Detects manual changes and preserves them
- **Dynamic flags** - YAML-defined flags become CLI options
- **Path operations** - Prepend, append, remove path entries
- **Lifecycle hooks** - Run scripts before/after load/unload
- **Config inheritance** - Extend base configurations

## Documentation

Visit [luocfprime.github.io/envlit](https://luocfprime.github.io/envlit/) for full documentation.

## Development

```bash
# Install dependencies
make install

# Run tests
pytest
```

## License

MIT License - see [LICENSE](LICENSE) for details.
