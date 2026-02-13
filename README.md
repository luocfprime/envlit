# envlit

[![CI](https://github.com/luocfprime/envlit/actions/workflows/ci.yml/badge.svg)](https://github.com/luocfprime/envlit/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/luocfprime/envlit/branch/main/graph/badge.svg)](https://codecov.io/gh/luocfprime/envlit)
[![Python Versions](https://img.shields.io/pypi/pyversions/envlit)](https://pypi.org/project/envlit/)
[![PyPI](https://img.shields.io/pypi/v/envlit)](https://pypi.org/project/envlit/)

A simple CLI tool to organize, load, and switch between your project's environment variable contexts.

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

Load and unload environment variables:

```bash
el                       # Load default profile
echo $PROJECT_MODE       # Output: Development (variable set by envlit)
echo $DEBUG              # Output: true (variable set by envlit)

eul                      # Unload environment variables
echo $PROJECT_MODE       # Output: (empty - variable restored to original state)
echo $DEBUG              # Output: (empty - variable restored to original state)
```

## Features

- **Smart state tracking** - Detects manual changes and preserves them
- **Dynamic flags** - YAML-defined flags become CLI options
- **Path operations** - Prepend, append, remove path entries
- **Lifecycle hooks** - Run scripts before/after load/unload
- **Config inheritance** - Extend base configurations

## Comparison with Similar Tools

| Feature | envlit | direnv | dotenv |
|---------|--------|--------|--------|
| **Auto-activation on cd** | ❌ | ✅ | ❌ |
| **Manual load/unload** | ✅ | ❌ | ✅ |
| **State restoration** | ✅ Full restore | ⚠️ Basic | ❌ No |
| **Config format** | YAML | Shell/direnvrc | `.env` |
| **Dynamic CLI flags** | ✅ | ❌ | ❌ |
| **PATH operations** | ✅ | ✅ | ❌ |
| **Lifecycle hooks** | ✅ 4 stages | ⚠️ Limited | ❌ |
| **Config inheritance** | ✅ | ❌ | ❌ |
| **Manual change detection** | ✅ | ❌ | ❌ |

**Key Differences:**

- **envlit**: Manual control with explicit load/unload. Full state tracking with restoration. Better for variable contexts that you want to toggle on demand.
- **direnv**: Automatically activates on directory change. Great for per-directory isolation but less control over when environments load. Basic restoration.
- **dotenv**: Simple `.env` file loading, no restoration or advanced features. Good for 12-factor apps but lacks state management.

**When to use envlit:**

- You want CLI flags that map to environment variables (especially useful for long names and values)
- You want explicit control over when environments load/unload
- You need to preserve user modifications and restore clean state
- You need complex PATH operations or lifecycle hooks

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
